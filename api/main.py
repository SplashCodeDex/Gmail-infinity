"""
Gmail Infinity Factory - FastAPI Backend
Ultra-lightweight, async API with WebSocket support.
"""
import os
import sys
import asyncio
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import uvicorn

# Import core modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import Config
from core.account_manager import account_manager
from core.health_checker import AccountHealthChecker
from core.proxy_manager import proxy_manager


# ============================================================================
# Pydantic Models
# ============================================================================

class SessionConfig(BaseModel):
    num_accounts: int = Field(ge=1, le=1000)
    concurrent: int = Field(ge=1, le=5, default=1)
    use_sms: bool = False
    use_proxies: bool = True
    warmup: bool = True
    adaptive: bool = True
    export_format: str = "json"
    auto_recover: bool = True



class ExportRequest(BaseModel):
    format: str = Field(pattern="^(json|csv|txt|all)$")


class HealthCheckRequest(BaseModel):
    """Optional subset of emails to check; omit to check every account."""
    emails: Optional[List[str]] = None


class ProxyImportRequest(BaseModel):
    proxies: List[str] = []
    replace: bool = False


# ============================================================================
# WebSocket Manager
# ============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


# ============================================================================
# Session Manager
# ============================================================================

active_sessions = {}


class CreationSession:
    def __init__(self, session_id: str, config: SessionConfig):
        self.session_id = session_id
        self.config = config
        self.status = 'initializing'
        self.progress = {
            'current': 0,
            'total': config.num_accounts,
            'successes': 0,
            'failures': 0,
            'success_rate': 0.0
        }
        self.created_accounts = []
        self.logs = []
        self.start_time = None
        self.end_time = None
        self.stop_flag = False
        self.task = None
        # Guards progress read-modify-write: worker threads call bump_progress()
        # while the event loop / API handlers read the dict concurrently.
        self._progress_lock = threading.Lock()

    async def add_log(self, level: str, message: str):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        self.logs.append(log_entry)
        await manager.broadcast({
            'type': 'session_log',
            'session_id': self.session_id,
            'log': log_entry
        })

    def bump_progress(self, success: bool, index: int) -> dict:
        """Thread-safe progress increment. Callable from worker threads
        (concurrent > 1) without racing on the read-modify-write."""
        with self._progress_lock:
            key = 'successes' if success else 'failures'
            self.progress[key] += 1
            self.progress['current'] = max(self.progress['current'], index + 1)
            total_attempts = self.progress['successes'] + self.progress['failures']
            if total_attempts > 0:
                self.progress['success_rate'] = (self.progress['successes'] / total_attempts) * 100
            return dict(self.progress)

    def snapshot_progress(self) -> dict:
        """Return a consistent copy of progress for readers."""
        with self._progress_lock:
            return dict(self.progress)

    async def broadcast_progress(self, snapshot: dict):
        await manager.broadcast({
            'type': 'session_progress',
            'session_id': self.session_id,
            'progress': snapshot
        })

    async def update_progress(self, **kwargs):
        with self._progress_lock:
            self.progress.update(kwargs)
            total_attempts = self.progress['successes'] + self.progress['failures']
            if total_attempts > 0:
                self.progress['success_rate'] = (self.progress['successes'] / total_attempts) * 100
            snapshot = dict(self.progress)

        await self.broadcast_progress(snapshot)

    async def add_account(self, account: dict):
        self.created_accounts.append(account)
        await manager.broadcast({
            'type': 'account_created',
            'session_id': self.session_id,
            'account': account
        })


async def run_creation_session(session_id: str):
    """Run account creation session asynchronously."""
    session = active_sessions.get(session_id)
    if not session:
        return

    try:
        session.status = 'running'
        session.start_time = datetime.now()
        await session.add_log('info', 'Session started')

        # Import enhanced creator
        from enhanced_creator import EnhancedCreator

        # Create instance
        creator = EnhancedCreator(
            num_accounts=session.config.num_accounts,
            use_sms=session.config.use_sms,
            use_proxies=session.config.use_proxies,
            warmup=session.config.warmup,
            export_format=session.config.export_format,
            concurrent=session.config.concurrent,
            auto_recover=session.config.auto_recover,
            adaptive=session.config.adaptive
        )

        # Wrap creation method to hook into events
        original_create = creator.create_account_with_intelligence
        loop = asyncio.get_running_loop()

        def wrapped_create(index, progress=None, task_id=None):
            if session.stop_flag:
                return {'success': False, 'email': 'stopped', 'error': 'Stopped by user'}

            try:
                asyncio.run_coroutine_threadsafe(
                    session.add_log('info', f'Creating account {index + 1}/{session.config.num_accounts}'),
                    loop
                )
            except Exception:
                pass

            result = original_create(index, progress, task_id)

            if result and result.get('success'):
                try:
                    snapshot = session.bump_progress(success=True, index=index)
                    asyncio.run_coroutine_threadsafe(session.broadcast_progress(snapshot), loop)
                    asyncio.run_coroutine_threadsafe(session.add_account(result), loop)
                    asyncio.run_coroutine_threadsafe(
                        session.add_log('success', f'✓ Created: {result.get("email", "")}'),
                        loop
                    )
                except Exception:
                    pass
            else:
                try:
                    snapshot = session.bump_progress(success=False, index=index)
                    asyncio.run_coroutine_threadsafe(session.broadcast_progress(snapshot), loop)
                    asyncio.run_coroutine_threadsafe(
                        session.add_log('error', f'✗ Failed: {result.get("email", "unknown") if result else "unknown"}'),
                        loop
                    )
                except Exception:
                    pass

            return result

        creator.create_account_with_intelligence = wrapped_create

        # Run in executor (blocking operation)
        success = await loop.run_in_executor(None, creator.run)

        session.status = 'completed' if success else 'failed'
        session.end_time = datetime.now()
        await session.add_log('info', f'Session completed: {session.progress["successes"]} successes')

        await manager.broadcast({
            'type': 'session_complete',
            'session_id': session_id,
            'status': session.status,
            'progress': session.snapshot_progress()
        })

    except Exception as e:
        session.status = 'failed'
        await session.add_log('error', f'Session error: {str(e)}')
        logging.exception(f"Session {session_id} error")


# ============================================================================
# FastAPI App
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.info("Starting Gmail Infinity Factory API")
    yield
    # Shutdown
    logging.info("Shutting down Gmail Infinity Factory API")


app = FastAPI(
    title="Gmail Infinity Factory API",
    description="Lightweight async API for Gmail account creation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS & Security Hardening
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def verify_api_token(request, call_next):
    """Optional token authentication. If API_SECRET_TOKEN is set in .env,
    requests to /api/* must supply a matching X-API-Key or Bearer token."""
    token = os.getenv("API_SECRET_TOKEN", "")
    if token:
        path = request.url.path
        if path.startswith("/api/"):
            auth_header = request.headers.get("Authorization", "")
            api_key = request.headers.get("X-API-Key", "")
            provided = api_key or (auth_header.replace("Bearer ", "").strip() if auth_header.startswith("Bearer ") else auth_header.strip())
            if provided != token:
                from fastapi.responses import JSONResponse
                return JSONResponse(status_code=401, content={"detail": "Unauthorized: Invalid or missing API token"})
    return await call_next(request)


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle client messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/config")
async def get_config():
    return {
        "engine": Config.ENGINE_MODE,
        "headless": Config.HEADLESS_MODE,
        "use_proxies": Config.ENABLE_PROXY,
        "proxy_type": Config.PROXY_TYPE,
        "warmup_enabled": True,
        "delay_between_accounts": Config.DELAY_BETWEEN_ACCOUNTS,
        "password_set": bool(Config.YOUR_PASSWORD),
        "sms_providers": {
            "5sim": bool(Config.FIVESIM_API_KEY),
            "sms-activate": bool(Config.SMS_ACTIVATE_API_KEY),
            "onlinesim": bool(Config.ONLINESIM_API_KEY),
            "getsms": bool(Config.GETSMS_API_KEY),
        },
        "anti_captcha_set": bool(Config.ANTICAPTCHA_API_KEY or Config.TWOCAPTCHA_API_KEY or Config.CAPMONSTER_API_KEY),
    }


@app.get("/api/stats")
async def get_stats():
    account_stats = account_manager.get_stats()
    proxy_stats = proxy_manager.get_stats()

    return {
        "accounts": {
            "total": account_stats['total'],
            "successes": account_stats['active'],
            "failures": account_stats['total'] - account_stats['active'],
            "success_rate": account_stats.get('success_rate', 0.0),
            "strategies": account_stats['strategies'],
        },
        "proxies": {
            "total": proxy_stats.get('total', 0),
            "healthy": proxy_stats.get('healthy', 0),
            "unhealthy": proxy_stats.get('unhealthy', 0),
            "avg_response_time": proxy_stats.get('avg_latency_ms', 0),
        },
        "active_sessions": len([s for s in active_sessions.values() if s.status == 'running']),
        "total_sessions": len(active_sessions)
    }


@app.get("/api/accounts")
async def get_accounts(limit: int = 100, offset: int = 0):
    accounts = account_manager.get_all()
    total = len(accounts)

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "accounts": accounts[offset:offset + limit]
    }


@app.post("/api/accounts/health-check")
async def health_check_accounts(request: Optional[HealthCheckRequest] = None):
    """Verify accounts are still alive via Gmail IMAP.

    Blocking network I/O — runs in the executor threadpool. Checks a
    subset when `emails` is given, otherwise every stored account.
    """
    accounts = account_manager.get_all()
    if request and request.emails is not None:
        wanted = set(request.emails)
        accounts = [a for a in accounts if a.get("email") in wanted]

    to_check = [
        {"email": a.get("email", ""), "password": a.get("password", "")}
        for a in accounts
        if a.get("email") and a.get("password")
    ]
    if not to_check:
        return {"results": [], "summary": AccountHealthChecker.get_summary([])}

    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(
        None, AccountHealthChecker.check_all, to_check, 1
    )
    return {
        "results": results,
        "summary": AccountHealthChecker.get_summary(results),
    }


@app.post("/api/accounts/export")
async def export_accounts(request: ExportRequest):
    exporters = {
        'json': account_manager.export_json,
        'csv': account_manager.export_csv,
        'txt': account_manager.export_txt,
        'all': account_manager.export_all,
    }
    exporter = exporters.get(request.format)
    if exporter is None:
        raise HTTPException(400, f"Invalid format '{request.format}'. Supported: json, csv, txt, all")

    try:
        path = exporter()
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Account export failed")
        raise HTTPException(500, f"Export failed: {e}")

    media_types = {
        '.json': 'application/json',
        '.csv': 'text/csv',
        '.txt': 'text/plain',
        '.zip': 'application/zip',
    }
    ext = Path(path).suffix.lower()
    media_type = media_types.get(ext, 'application/octet-stream')

    return FileResponse(path, filename=Path(path).name, media_type=media_type)


@app.post("/api/session/start")
async def start_session(config: SessionConfig):
    import time
    import os

    session_id = f"session_{int(time.time())}_{os.urandom(4).hex()}"
    session = CreationSession(session_id, config)
    active_sessions[session_id] = session

    # Start background task
    session.task = asyncio.create_task(run_creation_session(session_id))

    return {
        "session_id": session_id,
        "message": "Session started"
    }


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(404, "Session not found")

    session = active_sessions[session_id]

    return {
        "id": session_id,
        "status": session.status,
        "config": session.config.model_dump(),
        "progress": session.snapshot_progress(),
        "start_time": session.start_time.isoformat() if session.start_time else None,
        "end_time": session.end_time.isoformat() if session.end_time else None,
        "accounts_count": len(session.created_accounts),
        "logs_count": len(session.logs)
    }


@app.post("/api/session/{session_id}/stop")
async def stop_session(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(404, "Session not found")

    session = active_sessions[session_id]
    session.stop_flag = True
    session.status = 'stopped'

    return {"message": "Session stopped"}


@app.get("/api/session/{session_id}/logs")
async def get_session_logs(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(404, "Session not found")

    session = active_sessions[session_id]
    return {"logs": session.logs[-100:]}


@app.get("/api/sessions")
async def get_all_sessions():
    sessions_data = []
    for session_id, session in active_sessions.items():
        sessions_data.append({
            'id': session_id,
            'status': session.status,
            'progress': session.snapshot_progress(),
            'start_time': session.start_time.isoformat() if session.start_time else None,
        })

    return {"sessions": sessions_data}


@app.get("/api/proxies")
async def get_proxies():
    proxies = proxy_manager.get_all_proxies()
    stats = proxy_manager.get_stats()

    return {
        "total": len(proxies),
        "healthy": stats.get('healthy', 0),
        "unhealthy": stats.get('unhealthy', 0),
        "list": proxies
    }


@app.post("/api/proxies/import")
async def import_proxies(request: ProxyImportRequest):
    try:
        added = proxy_manager.add_proxies(request.proxies, replace=request.replace)
        stats = proxy_manager.get_stats()
        return {
            "success": True,
            "added": added,
            "total": stats["total"],
            "message": f"Successfully imported {added} proxies"
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to import proxies: {e}")


@app.post("/api/proxies/fetch")
async def fetch_public_proxies():
    try:
        from core.proxy_fetcher import fetch_proxies
        loop = asyncio.get_running_loop()
        fetched = await loop.run_in_executor(None, fetch_proxies)
        added = proxy_manager.add_proxies(fetched, replace=False)
        stats = proxy_manager.get_stats()
        return {
            "success": True,
            "fetched": len(fetched),
            "added": added,
            "total": stats["total"],
            "message": f"Fetched {len(fetched)} public proxies ({added} new added to pool)"
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch public proxies: {e}")


@app.post("/api/proxies/clear")
async def clear_proxies():
    try:
        proxy_manager.clear_proxies()
        return {"success": True, "message": "Proxy pool cleared"}
    except Exception as e:
        raise HTTPException(500, f"Failed to clear proxies: {e}")


@app.post("/api/proxies/test")
async def test_proxies():
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, proxy_manager.check_all_health_detailed)
    return {"results": results}


@app.get("/api/sms/balances")
async def get_sms_balances():
    try:
        from services.sms_manager import check_balance
        balances = await check_balance()
        return {
            "success": True,
            "balances": balances
        }
    except Exception as e:
        return {
            "success": False,
            "balances": {},
            "error": str(e)
        }


@app.post("/api/telegram/test")
async def test_telegram_alert():
    try:
        from core.telegram_notifier import TelegramNotifier
        notifier = TelegramNotifier()
        if not notifier.enabled:
            return {
                "success": False,
                "message": "Telegram Bot Token or Chat ID is not configured in .env"
            }
        ok, msg = notifier.test_connection()
        if ok:
            sent = notifier.send("<b>Gmail Infinity Factory</b>\nPipeline test alert verified successfully!")
            return {
                "success": sent,
                "message": msg if sent else "Failed to deliver message to chat"
            }
        return {"success": False, "message": msg}
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.get("/api/engine/capabilities")
async def get_engine_capabilities():
    return {
        "engines": [
            {"id": "playwright", "name": "Playwright (Stealth Web)", "available": True},
            {"id": "appium", "name": "Appium (Android Native OS Emulator)", "available": True}
        ],
        "stealth_modules": {
            "poltergeist": Config.ENABLE_POLTERGEIST,
            "ghost_typer": Config.ENABLE_GHOST_TYPER,
            "cdp_injection": Config.ENABLE_CDP_INJECTION,
            "recovery_chain": Config.ENABLE_RECOVERY_CHAIN,
            "mac_rotation": Config.ENABLE_MAC_ROTATION,
        },
        "identity": {
            "use_arabic_names": Config.USE_ARABIC_NAMES,
            "birthday": Config.YOUR_BIRTHDAY,
            "gender": Config.YOUR_GENDER,
        },
        "telegram": {
            "configured": bool(Config.TELEGRAM_BOT_TOKEN and Config.TELEGRAM_CHAT_ID)
        }
    }


# ============================================================================
# Main
# ============================================================================

def main():
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "False").lower() in ("1", "true", "yes")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
