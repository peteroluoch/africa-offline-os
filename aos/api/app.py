from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.responses import StreamingResponse, RedirectResponse

from aos.bus.dispatcher import EventDispatcher
from aos.bus.event_store import EventStore
from aos.bus.events import Event
from aos.core.config import Settings
from aos.core.health import HealthStatus, check_db_health, get_disk_space, get_uptime
from aos.db.engine import connect
from aos.db.migrations import MigrationManager
from aos.db.migrations.registry import MIGRATIONS

from aos.api.state import core_state, mesh_state, agri_state, resource_state, transport_state, community_state, event_stream



def get_db() -> sqlite3.Connection:
    """Get the global database connection."""
    if core_state.db_conn is None:
        raise RuntimeError("Database not initialized")
    return core_state.db_conn

def reset_globals() -> None:
    """Reset global state for testing purposes."""
    event_stream.clear()
    
    if core_state.db_conn:
        try:
            core_state.db_conn.close()
        except: pass
    core_state.db_conn = None
    core_state.boot_time = None
    core_state.event_store = None
    core_state.event_dispatcher = None
    core_state.encryptor = None

    # Clear other managers too
    mesh_state.manager = None
    agri_state.module = None
    transport_state.module = None
    resource_state.manager = None
    community_state.module = None

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle with graceful startup and shutdown."""

    # Startup
    core_state.boot_time = time.time()
    settings = Settings()

    # Auto-create directories
    Path(settings.sqlite_path).parent.mkdir(parents=True, exist_ok=True)

    core_state.db_conn = connect(settings.sqlite_path)

    # Run migrations
    mgr = MigrationManager(core_state.db_conn)
    mgr.apply_migrations(MIGRATIONS)

    # Power-safe Uptime Merge
    try:
        cursor = core_state.db_conn.execute("SELECT value FROM node_config WHERE key = 'session_uptime'")
        row = cursor.fetchone()
        if row:
            session_uptime = float(row[0])
            core_state.db_conn.execute(
                "UPDATE node_config SET value = CAST(value AS REAL) + ? WHERE key = 'accumulated_uptime'",
                (session_uptime,)
            )
            # If accumulated doesn't exist, insert it
            if core_state.db_conn.total_changes == 0:
                 core_state.db_conn.execute(
                    "INSERT OR IGNORE INTO node_config (key, value) VALUES ('accumulated_uptime', ?)",
                    (str(session_uptime),)
                )
            
            core_state.db_conn.execute("DELETE FROM node_config WHERE key = 'session_uptime'")
            core_state.db_conn.commit()
    except Exception as e:
        print(f"[A-OS] Warning: Uptime merge failed: {e}")

    # Initialize Event Bus
    core_state.event_store = EventStore(settings.sqlite_path)
    await core_state.event_store.initialize()

    core_state.event_dispatcher = EventDispatcher(core_state.event_store)

    # Initialize Security Engine (Phase 6.1)
    from aos.core.security.encryption import SymmetricEncryption
    from aos.core.security.identity import NodeIdentityManager
    identity_mgr = NodeIdentityManager()
    identity_mgr.ensure_identity()
    
    # Derive master key from node identity and configured secret
    master_key = SymmetricEncryption.derive_key(
        salt=identity_mgr.get_public_key()[:16], # Use node public key as salt
        secret=settings.master_secret,
        iterations=settings.kdf_iterations
    )
    core_state.encryptor = SymmetricEncryption(master_key)
    
    # Hook up the Stream
    core_state.event_dispatcher.subscribe_all(event_stream.broadcast)

    # Initialize Mesh System (Batch 5)
    from aos.adapters.remote_node import RemoteNodeAdapter
    from aos.core.mesh.manager import MeshSyncManager
    from aos.core.mesh.queue import MeshQueue

    identity_mgr = NodeIdentityManager()
    remote_adapter = RemoteNodeAdapter(identity_mgr)
    mesh_db_path = str(Path(settings.sqlite_path).parent / "mesh_queue.db")
    mesh_queue = MeshQueue(mesh_db_path)

    mesh_state.manager = MeshSyncManager(remote_adapter, mesh_queue)
    await mesh_state.manager.start()

    # Initialize Modules (Phase 5/6)
    from aos.modules.agri import AgriModule
    from aos.modules.reference import ReferenceModule
    from aos.modules.transport import TransportModule
    from aos.modules.community import CommunityModule

    ref_mod = ReferenceModule(core_state.event_dispatcher)
    await ref_mod.initialize()

    # Initialize Resource Manager (Phase 8) - BEFORE modules so they can use it
    from aos.core.resource import ResourceManager
    resource_state.manager = ResourceManager(
        event_bus=core_state.event_dispatcher, 
        db_conn=core_state.db_conn, 
        check_interval=settings.resource_check_interval
    )
    await resource_state.manager.start()

    # Initialize Modules with ResourceManager (Phase 5/6/7) - Power-aware
    agri_state.module = AgriModule(core_state.event_dispatcher, core_state.db_conn, resource_state.manager, core_state.encryptor)
    await agri_state.module.initialize()

    transport_state.module = TransportModule(core_state.event_dispatcher, core_state.db_conn, resource_state.manager)
    await transport_state.module.initialize()

    community_state.module = CommunityModule(core_state.event_dispatcher, core_state.db_conn)
    await community_state.module.initialize()

    print(f"[A-OS] Started - DB: {settings.sqlite_path}")

    try:
        yield
    finally:
        # Shutdown
        if resource_state.manager:
            await resource_state.manager.stop()
        if community_state.module:
            await community_state.module.shutdown()
        if core_state.event_store:
            await core_state.event_store.shutdown()
        if mesh_state.manager:
            await mesh_state.manager.stop()
        if core_state.db_conn:
            core_state.db_conn.close()
            print("[A-OS] Shutdown complete")


from fastapi import Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from aos.api.routers.agri import router as agri_router
from aos.api.routers.auth import router as auth_router
from aos.api.routers.community import router as community_router
from aos.api.routers.channels import router as channels_router
from aos.api.routers.mesh import router as mesh_router
from aos.api.routers.regional import router as regional_router
from aos.api.routers.resource import router as resource_router
from aos.api.routers.transport import router as transport_router
from aos.api.routers.admin_users import router as admin_users_router
from aos.api.routers.operators import router as operators_router
from aos.api.routers.policies import router as policies_router
from aos.core.security.auth import get_current_operator


def create_app() -> FastAPI:
    app = FastAPI(
        title="A-OS",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Register RBAC middleware (MUST be before routes)
    from aos.api.middleware.rbac import rbac_route_guard
    app.middleware("http")(rbac_route_guard)

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
    app.include_router(community_router)
    app.include_router(channels_router)
    app.include_router(resource_router)
    app.include_router(regional_router)
    app.include_router(admin_users_router)
    app.include_router(operators_router)
    app.include_router(policies_router)

    @app.get("/")
    async def root():
        """Redirect root to login page."""
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    @app.post("/sys/ping")
    async def sys_ping(current_user: dict = Depends(get_current_operator)) -> dict:
        """Trigger a system ping event (Protected)."""
        if core_state.event_dispatcher:
            event = Event(name="system.ping", payload={"nonce": int(time.time()), "source": current_user["username"]})
            await core_state.event_dispatcher.dispatch(event)
            return {"status": "ping_sent", "id": event.id}
        return {"status": "error"}
    
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """Serve the favicon."""
        from fastapi.responses import FileResponse
        favicon_path = Path(__file__).parent / "static" / "favicon.svg"
        if favicon_path.exists():
            return FileResponse(favicon_path, media_type="image/svg+xml")
        return {"status": "not_found"}

    @app.get("/health")
    def health() -> dict:
        """Comprehensive health check (Public)."""
        from aos.core.health import get_total_uptime
        
        disk_free = get_disk_space()
        session_uptime = get_uptime(core_state.boot_time)
        total_uptime = get_total_uptime(core_state.db_conn, session_uptime)
        db_status = check_db_health(core_state.db_conn)

        # Determine kernel metrics
        events_processed = 0
        mesh_peers_online = 0
        if mesh_state.manager:
            mesh_peers_online = sum(1 for p in mesh_state.manager.adapter.peers.values() if p.status == "ONLINE")

        status_obj = HealthStatus(
            status="ok",
            disk_free_mb=disk_free,
            uptime_seconds=total_uptime,
            db_status=db_status,
            events_processed=events_processed
        )

        return {
            "status": status_obj.status,
            "db_status": db_status,
            "disk_free_mb": disk_free,
            "uptime_seconds": total_uptime,
            "metrics": {
                "disk_mb": status_obj.disk_free_mb,
                "uptime_s": status_obj.uptime_seconds,
                "session_uptime_s": session_uptime,
                "mesh_peers_online": mesh_peers_online
            }
        }

    @app.get("/health/ready")
    def readiness_check() -> dict:
        """
        Kubernetes-style readiness probe.
        Returns 200 only if app is ready to serve traffic.
        """
        try:
            # Check database is accessible
            if not core_state.db_conn:
                return {"ready": False, "reason": "Database not initialized"}
            
            # Verify database is responsive
            core_state.db_conn.execute("SELECT 1").fetchone()
            
            # Check event dispatcher is running
            if not core_state.event_dispatcher:
                return {"ready": False, "reason": "Event dispatcher not initialized"}
            
            # Check disk space (need at least 100MB)
            disk_free = get_disk_space()
            if disk_free < 100:
                return {"ready": False, "reason": f"Low disk space: {disk_free}MB"}
            
            return {
                "ready": True,
                "timestamp": time.time(),
                "checks": {
                    "database": "ok",
                    "event_dispatcher": "ok",
                    "disk_space": f"{disk_free}MB"
                }
            }
        except Exception as e:
            return {"ready": False, "reason": str(e)}

    @app.get("/stream")
    async def stream(current_user: dict = Depends(get_current_operator)) -> StreamingResponse:
        """Stream real-time kernel events (Protected)."""
        return StreamingResponse(
            event_stream.subscribe(),
            media_type="text/event-stream"
        )

    @app.get("/dashboard")
    async def dashboard(request: Request, current_user: dict = Depends(get_current_operator)):
        """Render the kernel dashboard (Protected) with role-based redirection."""
        from aos.core.security.auth import AosRole
        
        user_role = current_user.get("role")
        community_id = current_user.get("community_id")

        # Redirect limited roles to their specific community base
        if user_role in [AosRole.COMMUNITY_ADMIN.value, AosRole.OPERATOR.value]:
            if community_id:
                return RedirectResponse(url=f"/community/{community_id}", status_code=status.HTTP_303_SEE_OTHER)
            else:
                # User is a field agent but hasn't been assigned to a group yet
                return templates.TemplateResponse(
                    "unassigned.html",
                    {"request": request, "user": current_user}
                )
        
        # ROOT and ADMIN see the kernel overview
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

    @app.get("/security")
    async def security_policy(request: Request, current_user: dict = Depends(get_current_operator)):
        """Security policy page."""
        return templates.TemplateResponse(
            "security.html",
            {"request": request, "user": current_user}
        )

    return app
