from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from aos.bus.dispatcher import EventDispatcher
from aos.bus.event_store import EventStore
from aos.bus.events import Event
from aos.core.config import Settings
from aos.core.health import HealthStatus, check_db_health, get_disk_space, get_uptime
from aos.db.engine import connect
from aos.db.migrations import MigrationManager
from aos.db.migrations.registry import MIGRATIONS

# Global state
_db_conn: sqlite3.Connection | None = None
_boot_time: float | None = None
_event_store: EventStore | None = None
_event_dispatcher: EventDispatcher | None = None
_mesh_manager: MeshSyncManager | None = None
_agri_module: AgriModule | None = None

from aos.api.state import mesh_state


class EventStream:
    """Manages Server-Sent Events (SSE) connections."""
    def __init__(self):
        self._listeners: set[asyncio.Queue] = set()

    async def broadcast(self, event: Event) -> None:
        """Format event as HTML row and push to all listeners."""
        # Create HTMX-ready HTML fragment with Premium Styling
        payload_str = json.dumps(event.payload)
        html = f"""
        <tr class="fade-in hover:bg-white/5 transition-all group border-b border-slate-800/20">
            <td class="px-8 py-4 text-slate-500 font-mono text-[10px]">{event.timestamp.strftime('%H:%M:%S')}</td>
            <td class="px-8 py-4 font-bold text-blue-400 aos-text-mono text-[11px] uppercase tracking-wider">{event.name}</td>
            <td class="px-8 py-4 text-slate-400 max-w-4xl truncate group-hover:whitespace-normal aos-text-mono text-[11px] opacity-80">{payload_str}</td>
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

    # Power-safe Uptime Merge
    try:
        cursor = _db_conn.execute("SELECT value FROM node_config WHERE key = 'session_uptime'")
        row = cursor.fetchone()
        if row:
            session_uptime = float(row[0])
            _db_conn.execute(
                "UPDATE node_config SET value = CAST(value AS REAL) + ? WHERE key = 'accumulated_uptime'",
                (session_uptime,)
            )
            # If accumulated doesn't exist, insert it
            if _db_conn.total_changes == 0:
                 _db_conn.execute(
                    "INSERT OR IGNORE INTO node_config (key, value) VALUES ('accumulated_uptime', ?)",
                    (str(session_uptime),)
                )
            
            _db_conn.execute("DELETE FROM node_config WHERE key = 'session_uptime'")
            _db_conn.commit()
    except Exception as e:
        print(f"[A-OS] Warning: Uptime merge failed: {e}")

    # Initialize Event Bus
    _event_store = EventStore(settings.sqlite_path)
    await _event_store.initialize()

    _event_dispatcher = EventDispatcher(_event_store)

    # Hook up the Stream
    _event_dispatcher.subscribe_all(_event_stream.broadcast)

    # Initialize Mesh System (Batch 5)
    from aos.adapters.remote_node import RemoteNodeAdapter
    from aos.core.mesh.manager import MeshSyncManager
    from aos.core.mesh.queue import MeshQueue
    from aos.core.security.identity import NodeIdentityManager

    identity_mgr = NodeIdentityManager()
    remote_adapter = RemoteNodeAdapter(identity_mgr)
    mesh_db_path = str(Path(settings.sqlite_path).parent / "mesh_queue.db")
    mesh_queue = MeshQueue(mesh_db_path)

    _mesh_manager = MeshSyncManager(remote_adapter, mesh_queue)
    mesh_state.manager = _mesh_manager
    await _mesh_manager.start()

    # Initialize Modules (Phase 5/6)
    from aos.modules.agri import AgriModule
    from aos.modules.reference import ReferenceModule
    from aos.modules.transport import TransportModule

    ref_mod = ReferenceModule(_event_dispatcher)
    await ref_mod.initialize()

    # Initialize Resource Manager (Phase 8) - BEFORE modules so they can use it
    from aos.core.resource import ResourceManager
    _resource_manager = ResourceManager(
        event_bus=_event_dispatcher, 
        db_conn=_db_conn, 
        check_interval=settings.resource_check_interval
    )
    await _resource_manager.start()

    # Initialize Modules with ResourceManager (Phase 5/6/7) - Power-aware
    _agri_module = AgriModule(_event_dispatcher, _db_conn, _resource_manager)
    await _agri_module.initialize()

    _transport_module = TransportModule(_event_dispatcher, _db_conn, _resource_manager)
    await _transport_module.initialize()

    # Store for global access if needed
    from aos.api.state import agri_state, resource_state, transport_state
    agri_state.module = _agri_module
    transport_state.module = _transport_module
    resource_state.manager = _resource_manager

    print(f"[A-OS] Started - DB: {settings.sqlite_path}")

    try:
        yield
    finally:
        # Shutdown
        if _resource_manager:
            await _resource_manager.stop()
        if _event_store:
            await _event_store.shutdown()
        if _mesh_manager:
            await _mesh_manager.stop()
        if _db_conn:
            _db_conn.close()
            print("[A-OS] Shutdown complete")


from fastapi import Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from aos.api.routers.agri import router as agri_router
from aos.api.routers.auth import router as auth_router
from aos.api.routers.channels import router as channels_router
from aos.api.routers.mesh import router as mesh_router
from aos.api.routers.regional import router as regional_router
from aos.api.routers.resource import router as resource_router
from aos.api.routers.transport import router as transport_router
from aos.api.routers.admin_users import router as admin_users_router
from aos.api.routers.policies import router as policies_router
from aos.core.security.auth import get_current_operator


def create_app() -> FastAPI:
    app = FastAPI(
        title="A-OS",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Static files for Design System
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # Templates for Design System
    templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

    app.include_router(auth_router)
    app.include_router(mesh_router)
    app.include_router(agri_router)
    app.include_router(transport_router)
    app.include_router(channels_router)
    app.include_router(resource_router)
    app.include_router(regional_router)
    app.include_router(admin_users_router)
    app.include_router(policies_router)

    @app.post("/sys/ping")
    async def sys_ping(current_user: dict = Depends(get_current_operator)) -> dict:
        """Trigger a system ping event (Protected)."""
        if _event_dispatcher:
            event = Event(name="system.ping", payload={"nonce": int(time.time()), "source": current_user["username"]})
            await _event_dispatcher.dispatch(event)
            return {"status": "ping_sent", "id": event.id}
        return {"status": "error"}

    @app.get("/health")
    def health() -> dict:
        """Comprehensive health check (Public)."""
        from aos.core.health import get_total_uptime
        
        disk_free = get_disk_space()
        session_uptime = get_uptime(_boot_time)
        total_uptime = get_total_uptime(_db_conn, session_uptime)
        db_status = check_db_health(_db_conn)

        # Determine kernel metrics
        events_processed = 0
        mesh_peers_online = 0
        if _mesh_manager:
            mesh_peers_online = sum(1 for p in _mesh_manager.adapter.peers.values() if p.status == "ONLINE")

        status = HealthStatus(
            status="ok",
            disk_free_mb=disk_free,
            uptime_seconds=total_uptime,
            db_status=db_status,
            events_processed=events_processed
        )

        return {
            "status": status.status,
            "db_status": db_status,
            "disk_free_mb": disk_free,
            "uptime_seconds": total_uptime,
            "metrics": {
                "disk_mb": status.disk_free_mb,
                "uptime_s": status.uptime_seconds,
                "session_uptime_s": session_uptime,
                "mesh_peers_online": mesh_peers_online
            }
        }

    @app.get("/stream")
    async def stream(current_user: dict = Depends(get_current_operator)) -> StreamingResponse:
        """Stream real-time kernel events (Protected)."""
        return StreamingResponse(
            _event_stream.subscribe(),
            media_type="text/event-stream"
        )

    @app.get("/dashboard")
    async def dashboard(request: Request, current_user: dict = Depends(get_current_operator)):
        """Render the kernel dashboard (Protected)."""
        return templates.TemplateResponse(
            "dashboard.html",
            {"request": request, "user": current_user}
        )

    @app.get("/sys/gallery")
    async def ui_gallery(request: Request, current_user: dict = Depends(get_current_operator)):
        """Render the A-OS Design System Gallery (Protected)."""
        return templates.TemplateResponse(
            "gallery.html",
            {"request": request, "user": current_user}
        )

    @app.get("/sys/mesh")
    async def mesh_management(request: Request, current_user: dict = Depends(get_current_operator)):
        """Render the A-OS Mesh Management page (Protected)."""
        peers = []
        if mesh_state.manager:
            peers = list(mesh_state.manager.adapter.peers.values())

        return templates.TemplateResponse(
            "mesh.html",
            {"request": request, "user": current_user, "peers": peers}
        )

    @app.get("/operators")
    async def operators_management(request: Request, current_user: dict = Depends(get_current_operator)):
        """Operator management page."""
        return templates.TemplateResponse(
            "operators.html",
            {"request": request, "user": current_user}
        )

    @app.get("/security")
    async def security_policy(request: Request, current_user: dict = Depends(get_current_operator)):
        """Security policy page."""
        return templates.TemplateResponse(
            "security.html",
            {"request": request, "user": current_user}
        )

    return app
