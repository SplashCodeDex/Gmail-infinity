"""
Gmail Infinity Factory - FastAPI Backend
Ultra-lightweight, async API with WebSocket support.
"""
import asyncio
import logging
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
from core.database import DatabaseManager
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

    async def update_progress(self, **kwargs):
        self.progress.update(kwargs)
        total_attempts = self.progress['successes'] + self.progress['failures']
        if total_attempts > 0:
            self.progress['success_rate'] = (self.progress['successes'] / total_attempts) * 100

        await manager.broadcast({
            'type': 'session_progress',
            'session_id': self.session_id,
            'progress': self.progress
        })

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
                    asyncio.run_coroutine_threadsafe(
                        session.update_progress(
                            current=index + 1,
                            successes=session.progress['successes'] + 1
                        ),
                        loop
                    )
                    asyncio.run_coroutine_threadsafe(session.add_account(result), loop)
                    asyncio.run_coroutine_threadsafe(
                        session.add_log('success', f'✓ Created: {result.get("email", "")}'),
                        loop
                    )
                except Exception:
                    pass
            else:
                try:
                    asyncio.run_coroutine_threadsafe(
                        session.update_progress(
                            current=index + 1,
                            failures=session.progress['failures'] + 1
                        ),
                        loop
                    )
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
            'progress': session.progress
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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# ============================================================================
# API Routes
# ============================================================================

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/config")
async def get_config():
    return {
        "password_set": bool(Config.YOUR_PASSWORD),
        "sms_providers": {
            "fivesim": bool(Config.FIVESIM_API_KEY),
            "sms_activate": bool(Config.SMS_ACTIVATE_API_KEY),
            "onlinesim": bool(Config.ONLINESIM_API_KEY),
        },
        "captcha_providers": {
            "twocaptcha": bool(Config.TWOCAPTCHA_API_KEY),
            "anticaptcha": bool(Config.ANTICAPTCHA_API_KEY),
        },
        "proxies": {
            "enabled": Config.ENABLE_PROXY,
            "count": proxy_manager.count,
            "healthy": proxy_manager.get_stats().get('healthy', 0),
        },
        "engine": Config.ENGINE_MODE,
        "headless": Config.HEADLESS_MODE,
    }


@app.get("/api/stats")
async def get_stats():
    account_stats = account_manager.get_stats()
    proxy_stats = proxy_manager.get_stats()

    return {
        "accounts": account_stats,
        "proxies": proxy_stats,
        "active_sessions": len([s for s in active_sessions.values() if s.status == 'running'])
    }


@app.get("/api/accounts")
async def get_accounts():
    accounts = account_manager.get_all()
    return {
        "accounts": accounts,
        "count": len(accounts)
    }


@app.post("/api/accounts/export")
async def export_accounts(request: ExportRequest):
    try:
        if request.format == 'json':
            path = account_manager.export_json()
        elif request.format == 'csv':
            path = account_manager.export_csv()
        elif request.format == 'txt':
            path = account_manager.export_txt()
        else:
            raise HTTPException(400, "Invalid format")

        return FileResponse(path, filename=Path(path).name)
    except Exception as e:
        raise HTTPException(500, str(e))


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
        "config": session.config.dict(),
        "progress": session.progress,
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
            'progress': session.progress,
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
        "list": proxies[:10]
    }


@app.post("/api/proxies/test")
async def test_proxies():
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, proxy_manager.check_all_health_detailed)
    return {"results": results}


# ============================================================================
# Main
# ============================================================================

def main():
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
