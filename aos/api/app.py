from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator, List, Set, Any
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse

from aos.core.config import Settings
from aos.core.health import HealthStatus, check_db_health, get_disk_space, get_uptime
from aos.db.engine import connect
from aos.db.migrations import MigrationManager
from aos.db.migrations.registry import MIGRATIONS
from aos.bus.events import Event
from aos.bus.event_store import EventStore
from aos.bus.dispatcher import EventDispatcher

# Global state
_db_conn: sqlite3.Connection | None = None
_boot_time: float | None = None
_event_store: EventStore | None = None
_event_dispatcher: EventDispatcher | None = None

class EventStream:
    """Manages Server-Sent Events (SSE) connections."""
    def __init__(self):
        self._listeners: Set[asyncio.Queue] = set()

    async def broadcast(self, event: Event) -> None:
        """Format event as HTML row and push to all listeners."""
        # Create HTMX-ready HTML fragment
        payload_str = json.dumps(event.payload)
        html = f"""
        <tr class="fade-in">
            <td class="px-4 py-2 border-b border-gray-700 font-mono text-sm timestamp">{event.timestamp.strftime('%H:%M:%S')}</td>
            <td class="px-4 py-2 border-b border-gray-700 font-bold text-accent">{event.name}</td>
            <td class="px-4 py-2 border-b border-gray-700 font-mono text-xs">{payload_str}</td>
        </tr>
        """
        # SSE format: data: <content>\n\n
        msg = f"data: {html}\n\n"
        
        # Broadcast to all queues
        # We assume queues are unbounded or managed by consumer
        dead_listeners = set()
        for q in self._listeners:
            try:
                q.put_nowait(msg)
            except Exception:
                dead_listeners.add(q)
        
        # Cleanup dead listeners
        self._listeners -= dead_listeners

    async def subscribe(self) -> AsyncIterator[str]:
        """Yield events for a single connection."""
        q = asyncio.Queue()
        self._listeners.add(q)
        try:
            while True:
                msg = await q.get()
                yield msg
        finally:
            self._listeners.remove(q)

_event_stream = EventStream()

def get_db() -> sqlite3.Connection:
    """Get the global database connection."""
    if _db_conn is None:
        raise RuntimeError("Database not initialized")
    return _db_conn

def reset_globals() -> None:
    """Reset global state for testing purposes."""
    global _db_conn, _boot_time, _event_store, _event_dispatcher
    if _db_conn:
        try:
            _db_conn.close()
        except: pass
    _db_conn = None
    _boot_time = None
    
    # Store shutdown is async, we can't easily await here in synchronous reset
    # Tests should assume clean state or use async fixtures
    _event_store = None
    _event_dispatcher = None

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle with graceful startup and shutdown."""
    global _db_conn, _boot_time, _event_store, _event_dispatcher
    
    # Startup
    _boot_time = time.time()
    settings = Settings()
    
    # Auto-create directories
    Path(settings.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
    
    _db_conn = connect(settings.sqlite_path)
    
    # Run migrations
    mgr = MigrationManager(_db_conn)
    mgr.apply_migrations(MIGRATIONS)
    
    # Initialize Event Bus
    _event_store = EventStore(settings.sqlite_path)
    await _event_store.initialize()
    
    _event_dispatcher = EventDispatcher(_event_store)
    
    # Hook up the Stream
    _event_dispatcher.subscribe_all(_event_stream.broadcast)

    # Initialize Modules (Phase 5)
    from aos.modules.reference import ReferenceModule
    ref_mod = ReferenceModule(_event_dispatcher)
    await ref_mod.initialize()
    
    print(f"[A-OS] Started - DB: {settings.sqlite_path}")
    
    try:
        yield
    finally:
        # Shutdown
        if _event_store:
            await _event_store.shutdown()
        if _db_conn:
            _db_conn.close()
            print("[A-OS] Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="A-OS",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.post("/sys/ping")
    async def sys_ping() -> dict:
        """Trigger a system ping event (Demostrates Module Logic)."""
        if _event_dispatcher:
            event = Event(name="system.ping", payload={"nonce": int(time.time()), "source": "api"})
            await _event_dispatcher.dispatch(event)
            return {"status": "ping_sent", "id": event.id}
        return {"status": "error"}

    @app.get("/health")
    def health() -> dict:
        """Comprehensive health check."""
        disk_free = get_disk_space()
        uptime = get_uptime(_boot_time)
        db_status = check_db_health(_db_conn)
        
        # Determine kernel metrics
        events_processed = 0
        queue_depth = 0
        # In a real sync handler we'd need to lock or use a metrics store
        # For now return placeholders or use store if available (async issue in sync handler)
        
        status = HealthStatus(
            status="ok",
            disk_free_mb=disk_free,
            uptime_seconds=uptime,
            db_status=db_status,
            events_processed=events_processed
        )
        
        return {
            "status": status.status,
            "metrics": {
                "disk_mb": status.disk_free_mb,
                "uptime_s": status.uptime_seconds,
            }
        }

    @app.get("/stream")
    async def stream() -> StreamingResponse:
        """Stream real-time kernel events."""
        return StreamingResponse(
            _event_stream.subscribe(),
            media_type="text/event-stream"
        )
        
    @app.get("/dashboard")
    async def dashboard() -> HTMLResponse:
        """Render the kernel dashboard."""
        template_path = Path(__file__).parent / "templates" / "dashboard.html"
        if not template_path.exists():
            return HTMLResponse("Dashboard template not found", status_code=404)
        return HTMLResponse(template_path.read_text(encoding="utf-8"))

    return app
