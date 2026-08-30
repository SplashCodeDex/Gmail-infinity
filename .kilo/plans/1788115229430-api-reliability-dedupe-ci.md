# Plan: API Reliability, Intelligence Dedup, Health-Check Concurrency & CI

Scope: the six approved items (session persistence, event-loop blocking, monkey-patch/global-config, duplicated intelligence, missing CI/API tests, sequential health checks). Out of scope: WS credential security, docs drift.

---

## Phase A — Database foundation (items 1, 2)

**`core/database.py`**

1. In `_init_db()`, add two tables via `CREATE TABLE IF NOT EXISTS` (works for existing DBs, no ALTER needed):
   - `sessions(session_id TEXT PRIMARY KEY, status TEXT, num_accounts INTEGER, successes INTEGER DEFAULT 0, failures INTEGER DEFAULT 0, progress_json TEXT, config_json TEXT, created_at TIMESTAMP, started_at TIMESTAMP, ended_at TIMESTAMP)`
   - `session_logs(id INTEGER PK AUTOINCREMENT, session_id TEXT, timestamp TIMESTAMP, level TEXT, message TEXT)` + index on `session_id`
2. Enable `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=5000` at init (wrapped in try/except with silent fallback — WAL may fail on exotic volumes). Needed because Phase B adds concurrent writers from `to_thread` and worker threads while `DatabaseManager` opens a connection per call.
3. New methods: `save_session(session_id, status, num_accounts, config_json)`, `update_session(session_id, status=None, successes=None, failures=None, progress_json=None, started_at=None, ended_at=None)` (partial UPDATE), `append_session_log(session_id, level, message)`, `get_sessions(limit, offset)` (ORDER BY created_at DESC), `get_session(session_id)`, `get_session_logs(session_id, limit)`, `get_interrupted_sessions()` (status IN `running`,`initializing`).
4. Pagination + stats in SQL: `get_accounts_page(limit, offset)` (`LIMIT ? OFFSET ?`), `get_accounts_count()`, `get_stats()` using `COUNT(*)`, `SUM(CASE WHEN status='active' ...)`, `GROUP BY strategy`, `GROUP BY sms_service`. Keep `get_all_accounts()` untouched (CLI/creator path).

**`core/account_manager.py`**

5. Facades: `get_page(limit, offset)` → `db.get_accounts_page`, `get_count()` → `db.get_accounts_count`, `get_stats()` → `db.get_stats` (replaces Python-side reduce over full table; response shape unchanged).

---

## Phase B — API: async DB + session persistence (items 1, 2)

**`api/main.py`**

6. Move all blocking work off the loop with `asyncio.to_thread`:
   - `/api/stats`: `to_thread(account_manager.get_stats)` + proxy stats
   - `/api/accounts`: `to_thread` `get_page` + `get_count` (response shape `{total, limit, offset, accounts}` unchanged)
   - `/api/accounts/export`: `to_thread(exporter)` (currently blocking file I/O on the loop)
7. `CreationSession` changes:
   - Cap in-memory `logs` at the last 500 entries (currently unbounded; `/logs` endpoint already returns last 100).
   - `add_log` also persists via `await asyncio.to_thread(db.append_session_log, ...)` (db = `account_manager.db` — same pattern as `enhanced_creator.py:360`).
   - `broadcast_progress` persists the snapshot via awaited `to_thread(db.update_session, ...)` (at most one write per account attempt — no write amplification).
8. Session lifecycle persistence (all via awaited `to_thread`):
   - `start_session`: INSERT row (status `initializing`, num_accounts, config JSON).
   - `run_creation_session`: on run begin → `started_at` + status `running`; on finish → final status + `ended_at` + successes/failures/progress. Status precedence: `stopped` if `stop_flag` was set before completion (fixes existing bug where `run` overwrites `stopped` with `completed`), else `completed`/`failed`.
   - Lifecycle transitions (started/completed/failed/stopped/interrupted) also go through the existing `db.log_event()` — makes the never-called method the global audit trail in `execution_logs`.
9. Startup rehydration in `lifespan`: load `get_interrupted_sessions()`; insert into `active_sessions` as records with status `interrupted` and no asyncio task (browser work cannot resume). GET `/api/session/{id}` and `/logs` fall back to DB rows when the id is not in memory.
10. `GET /api/sessions` becomes DB-backed: `to_thread(db.get_sessions, limit, offset)` with `?limit=&offset=` params. Keep existing response keys per session (`id`, `status`, `progress`, `start_time`) so `SessionsList.vue` and `stores/app.js` keep working; add `end_time`. Memory/live dict wins for running sessions.
11. `stop_session`: keep `stop_flag`; also persist status `stopped`.

**`enhanced_creator.py`**

12. Add optional `session_id` param to `EnhancedCreator.__init__`. When set (API runs), `save_to_database()` skips its `session_stats` INSERT — the API owns the canonical `sessions` record. CLI behavior unchanged (`session_stats` remains the CLI summary store).

---

## Phase C — Creator/API integration cleanup (item 3)

13. `EnhancedCreator.__init__(..., event_callback=None, headless=None)`:
    - `self.headless`: explicit `headless` arg > `True if concurrent > 1` > `Config.HEADLESS_MODE`. Never assign `Config.HEADLESS_MODE` anywhere (delete mutations at lines 456 and 1157).
    - `event_callback(event_name: str, payload: dict)` called from worker threads — must be thread-safe/fast. Events: `account_start {index, total, username}`, `account_result {result}`. No-op when None.
14. Thread `headless` down: `create_account_with_intelligence` → `run_playwright_flow(..., headless=...)` → `async_playwright_flow(...)` → `PlaywrightStealthManager.initialize(proxy, is_premium, headless=None)` where `None` falls back to `Config.HEADLESS_MODE` (stealth_browser.py:84,92). CLI `--headless` passes `headless=True` instead of mutating Config; `show_config_dashboard` displays `self.headless`.
15. `api/main.py run_creation_session`: delete the `wrapped_create` monkey-patch block (lines 199-240). Build creator with `event_callback=adapter`; adapter uses `asyncio.run_coroutine_threadsafe(..., loop)` to schedule `session.add_log`, `bump_progress` + `broadcast_progress`, `add_account`, wrapped in try/except so adapter errors never propagate into creator threads.
16. `stop_session`: set `session.stop_flag = True` AND `session.creator.stop_requested = True` (store the creator reference on the session when the run starts; creator loops already honor `stop_requested` at lines 574/697/707/761).

---

## Phase D — Intelligence dedup (item 4)

17. `core/proxy_manager.py` — extend `ProxyManager` (keep existing `_scores` arithmetic; `tests/test_proxy_manager.py` depends on it):
    - Per-proxy history dict: `{successes, failures, last_used, latency_ms: deque(maxlen=10)}`, maintained by `mark_success`/`mark_failure` and by `check_health` (store measured latency).
    - `record_result(proxy, success, latency_ms=None)` — the single bookkeeping entry point for creation outcomes.
    - `select_smart()` — port the epsilon-greedy composite score from `IntelligentProxyManager`: success rate 60%, latency 20% (neutral 0.5 when unknown; normalize in **milliseconds**, e.g. `max(0, 1 - ms/3000)` — the old code fed multi-minute creation durations into a 10-second normalization, so its speed component was permanently 0), freshness 20%.
    - `get_intelligence_stats()` — summary for insights/exports.
18. New `core/strategy_engine.py`: move `AdaptiveStrategyEngine` from `enhanced_creator.py` unchanged (class + logic). `enhanced_creator` imports it; instantiation stays per-`EnhancedCreator` so checkpoint save/restore of `strategy_stats` is untouched.
19. `enhanced_creator.py`: delete `IntelligentProxyManager`; use `proxy_manager.select_smart()` / `proxy_manager.record_result()`. `save_current_state` stops persisting `proxy_stats` (proxy history is now shared live state in the core singleton); `load_previous_state` drops its proxy-restore branch (old checkpoints still load — unknown/missing fields ignored). `show_intelligence_insights` reads from core managers.

---

## Phase E — Health-check concurrency (item 8)

20. `core/health_checker.py`: `check_all(accounts, max_workers=8)` using `ThreadPoolExecutor` (pattern from `proxy_manager.check_all_health_detailed`); each worker runs `check_single` on its own IMAP connection; preserve input order via index-mapped futures; per-account try/except isolation; drop the `time.sleep(delay_between)` pacing (bounded workers replace it).
21. `api/main.py` `/api/accounts/health-check`: `HealthCheckRequest` gains `workers: int = Field(ge=1, le=20, default=8)`; pass to `check_all`; still runs via executor as today. Frontend already sets `timeout: 0` for this call (`stores/app.js:159-164`) — no store change needed.

---

## Phase F — Tests + CI (item 6)

22. `tests/test_database.py` (new): sessions table lifecycle (save/update/append log/get_sessions/get_session_logs), interrupted-session query, pagination + SQL stats vs seeded rows, WAL pragma fallback.
23. `tests/test_api.py` (new): `TestClient` on `api.main.app`; `monkeypatch.setattr("api.main.account_manager", fake)` / `proxy_manager` with fakes (fake `account_manager.db` = real `DatabaseManager` on `tmp_path`); stub `enhanced_creator.EnhancedCreator` whose `run()` drives `event_callback` and returns — covers: `/api/health`, `/api/stats` shape, `/api/accounts` pagination, session start/get/stop/logs, DB session row + `interrupted` rehydration, export endpoints (fake exporters writing real temp files), token middleware (`API_SECRET_TOKEN` env: 401 without header, 200 with `X-API-Key` — monkeypatch setenv/delenv), `/api/proxies` import/clear.
24. `tests/test_health_checker.py`: add `check_all` tests — result order preserved, per-account isolation, `check_single` called for every account (mock it).
25. `tests/test_proxy_manager.py`: add `select_smart`/`record_result`/history tests (untested proxy neutral score, success/failure tracking, latency recording).
26. `tests/test_strategy_engine.py` (new): `AdaptiveStrategyEngine` — score math, epsilon-greedy determinism with patched `random`, cooldown after 4/5 failures, ban after 10 consecutive.
27. `.github/workflows/ci.yml` (new; directory exists but is empty):
    - `backend`: ubuntu-latest, Python 3.12, `pip install -r requirements-dev.txt`, `pytest` (playwright browsers NOT installed — all tests mock browser layer).
    - `frontend`: Node 20, working-directory `web/`, `npm ci`, `npm run test` (Vitest specs exist in `web/src/stores/__tests__/`), `npm run build` (catches template/build regressions).

---

## Compatibility & risks

- Response shapes extended, never renamed — `web/` stores/components untouched and Vitest specs must keep passing.
- New status value `interrupted` appears in `/api/sessions` after a restart; frontend renders unknown statuses as-is (generic badge) — acceptable.
- `session_stats` (CLI) vs `sessions` (API) tables: intentional duality, one writer each — creator skips stats write when `session_id` is present.
- Old checkpoints lose `proxy_stats` (cache-like data, now shared core state) — acceptable.
- WAL on unusual filesystems: try/except fallback to default journal mode.
- No lint/typecheck config exists in this repo; none added (future work).

## Validation

1. `python -m pytest` — full suite green (old + new tests).
2. `cd web && npm run test && npm run build` — green.
3. CI file validated by a pushed run (or `act` locally if available).
4. Manual smoke (optional): `uvicorn api.main:app`, start session with stubbed creator, restart API, confirm session shows `interrupted` in `/api/sessions`.
