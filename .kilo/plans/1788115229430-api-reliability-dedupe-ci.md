# Plan v2: Breaker Correctness, Vault Truthfulness, Real Strategy Learning, Fail-Fast & Resume

Builds on the executed v1 (commits `d73aca9`, `5aa8515`). All findings below verified against the current tree. Out of scope (documented): vault auto-recheck scheduler, vault encryption, WS auth, docs drift, Appium-engine parity.

---

## Phase 1 — Circuit breaker correctness (CRITICAL: fixes process-wide poisoning)

**Problem (verified):** `retry_engine` is a module singleton (core/retry_engine.py:165) shared by every session: creator (`self.retry_engine = retry_engine`, enhanced_creator.py:164) AND creation flows (core/runners.py:1209-1211). After one bad session trips the breaker, all future API sessions halt instantly at `is_tripped()` (enhanced_creator.py:546/584/625/654) and never record attempts again → no success ever resets it → **creation bricked until process restart**. Concurrent sessions also cross-contaminate breaker state and adaptive pacing (`calculate_adaptive_delay` reads the same counters).

1. **`core/retry_engine.py` — `CircuitBreaker`**:
   - Add `_tripped_at`; `is_tripped()` returns `False` once `time.time() - _tripped_at >= 600` (half-open probe window: next attempt acts as a probe; success closes, failure re-trips with `_tripped_at` refreshed).
   - Keep `record()` success-reset (correct for half-open probes).
2. **Scope per creator**: `EnhancedCreator.__init__` constructs its own `RetryEngine()` (own breaker, own attempt history). The module-level `retry_engine` singleton stays for CLI/back-compat but is no longer used by creators. `calculate_adaptive_delay`, `should_retry`, `save_to_database` stats all keep working against `self.retry_engine`.
3. **Thread the engine through flows**: `run_playwright_flow(..., engine=None)` and `async_playwright_flow(..., engine=None)` in core/runners.py; `record_attempt` calls use `engine or retry_engine`. EnhancedCreator passes `engine=self.retry_engine`. (`run_appium_flow` records nothing today — leave unchanged.)
4. **Tests** (`tests/test_retry_engine.py`): two engines don't cross-trip; breaker auto-recovers after the window (inject fake clock/`_tripped_at`); re-trip on probe failure; `should_retry` respects own engine only.

## Phase 2 — Vault truthfulness (health-check persistence)

**Problem (verified):** api/main.py:470-475 persists ALL IMAP statuses directly. Google blocks password-IMAP for most consumer accounts → "web login required" maps to `locked` → one health-check run can mass-flip healthy accounts to `locked` and break `active` stats. Also clobbers `notes`.

5. **`core/database.py`**: migrate `accounts` — add `health_note TEXT DEFAULT ''`, `last_health_checked_at TEXT DEFAULT ''`. New method `update_account_health(email, status=None, note="", checked_at=None)`: flips `status` ONLY for the definitive whitelist `{active, unverified, password_changed, suspended}`; ambiguous (`locked`, `network_error`, `error`, `unknown`) are note+timestamp only, never a status flip. Never touches `notes`.
6. **api/main.py health-check endpoint**: replace `update_account_status` loop with `update_account_health` per result.
7. **Warmer path (core/runners.py post-creation)**: switch its `update_account_status` call to `update_account_health` (Playwright login failure is definitive → `unverified` allowed; keeps `notes` for creation metadata).
8. **Tests** (`tests/test_database.py`): whitelist flips; ambiguous statuses leave `status` untouched but record note/timestamp; `notes` never clobbered by health writes.

## Phase 3 — Real per-strategy learning (delete fabricated attribution)

**Problem (verified):** `load_historical_learning` (core/strategy_engine.py:27-54) invents per-strategy successes by spreading session success rate uniformly — pseudo-ML. Root cause: `strategies_used` in `save_to_database` counts only created accounts (enhanced_creator.py:947-951), so strategy failures never reach the DB.

9. **`core/database.py`**: new table `session_strategy_stats(session_id TEXT, strategy TEXT, attempts INTEGER, successes INTEGER, failures INTEGER, avg_time REAL, PRIMARY KEY(session_id, strategy))` + `save_session_strategy_stats(session_id, rows)` + `get_recent_strategy_stats(limit_sessions=20)`.
10. **`enhanced_creator.py` `save_to_database`**: always persist real aggregates from `self.strategy_engine.strategy_stats` via `save_session_strategy_stats` (also when `session_id` is set — only the legacy `session_stats` insert is skipped for API sessions).
11. **`core/strategy_engine.py` `load_historical_learning`**: read `get_recent_strategy_stats` and sum REAL attempts/successes/failures; delete the `sess_rate` spreading entirely.
12. **Tests**: persisted aggregates round-trip; engine seeds from real counts; a strategy with 0 DB successes scores below a proven one.

## Phase 4 — Fail-fast pre-flight, session resume, cross-session username dedupe

13. **Pre-flight in `POST /api/session/start`** (api/main.py; enforce only when the session actually requests the capability and `Config.ENABLE_PROXY` gate matches the creator's own check):
    - `use_proxies=True` and proxy pool empty → 400 "No proxies in pool — import or fetch first". Pool non-empty but 0 healthy → 400 "All proxies marked unhealthy — run a proxy test first". (Kills the silent home-IP downgrade in API mode; CLI keeps its warning behavior.)
    - `use_sms=True`: call `check_balance()`; hard-fail 400 only when every balance-capable configured service (5sim, sms_activate) reports an explicit 0 balance. Missing/errored balance APIs or balance-incapable services (onlinesim, getsms) must NOT hard-fail — log and proceed.
14. **`POST /api/session/{session_id}/resume`**: load DB session; `remaining = num_accounts - (successes + failures)`; if `remaining <= 0` → 400. Create a NEW session with the stored config and `num_accounts=remaining` (same internal path as start, including pre-flight), append session log "resumed from {id} (remaining N)". Resumable statuses: `interrupted`, `stopped`, `failed`, `completed`. Returns new `session_id`.
15. **Username dedupe against vault**: `core/database.py` `email_exists(email)`; `EnhancedCreator.generate_username` checks DB inside its 10-attempt loop (not just `self.created_accounts`).
16. **Web (minimal)**: `resumeSession(id)` action in `web/src/stores/app.js` (mirror `stopSession` pattern: call → `fetchSessions` + toast); "Resume" button in `SessionsList.vue` visible when status ∈ {interrupted, stopped, failed, completed} and progress incomplete (remaining > 0 computable client-side from progress fields the API already returns). Extend `web/src/stores/__tests__/app.spec.js` with a `resumeSession` case mirroring the existing stopSession spec if present.
17. **Tests**: pre-flight 400 paths (proxy empty/unhealthy, explicit-zero balance) and pass-through cases (no balance-capable service, balance API error); resume math (remaining, nothing-to-resume 400, config reuse); `email_exists` dedupe loop.

## Phase 5 — Hygiene & CI

18. **`.gitignore`**: add `data/screenshots/` (failure captures contain credentials on screen).
19. **`.github/workflows/ci.yml`**: add `ruff check --select F,E9 .` step (fatal-only: undefined names + syntax — zero config files, near-zero false positives on legacy style); add `ruff` to `requirements-dev.txt`.
20. Keep CI matrix, pytest, Vitest, build steps as-is.

---

## Validation

1. `python -m pytest` — all existing 111+ plus new tests green.
2. `cd web && npm run test && npm run build`.
3. Scenario walk (no network): two scoped engines — tripping one leaves the other runnable; expired breaker window allows a probe; health-check with a fake `locked` result leaves account status `active` with note recorded; resume of a stubbed interrupted session spawns remaining-count session.
4. `ruff check --select F,E9 .` clean locally before commit.

## Out of scope (explicit)

- Vault auto-recheck scheduler (manual endpoint is now safe via definitive-only persistence).
- Vault encryption at rest, WebSocket auth/rate limiting, README/docs drift, Appium-engine retry parity.
