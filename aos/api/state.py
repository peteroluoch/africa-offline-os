from __future__ import annotations

import asyncio
import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aos.bus.dispatcher import EventDispatcher
    from aos.bus.event_store import EventStore
    from aos.core.mesh.manager import MeshSyncManager
    from aos.core.resource.manager import ResourceManager
    from aos.core.security.encryption import SymmetricEncryption
    from aos.modules.agri import AgriModule
    from aos.modules.transport import TransportModule
    from aos.modules.community import CommunityModule

class CoreState:
    db_conn: sqlite3.Connection | None = None
    boot_time: float | None = None
    event_store: EventStore | None = None
    event_dispatcher: EventDispatcher | None = None
    encryptor: SymmetricEncryption | None = None

class MeshState:
    manager: MeshSyncManager | None = None

class AgriState:
    module: AgriModule | None = None

class TransportState:
    module: TransportModule | None = None

class ResourceState:
    manager: ResourceManager | None = None

class CommunityState:
    module: CommunityModule | None = None

class EventStream:
    """Manages Server-Sent Events (SSE) connections."""
    def __init__(self):
        self._listeners: set[asyncio.Queue] = set()

    async def broadcast(self, event: Event) -> None:
        """Format event as HTML row and push to all listeners."""
        import json
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
        from collections.abc import AsyncIterator
        q = asyncio.Queue()
        self._listeners.add(q)
        try:
            yield ": connected\n\n"
            while True:
                msg = await q.get()
                yield msg
        finally:
            self._listeners.remove(q)

    def clear(self) -> None:
        """Clear all listeners."""
        self._listeners.clear()

# Singletons
core_state = CoreState()
mesh_state = MeshState()
agri_state = AgriState()
transport_state = TransportState()
resource_state = ResourceState()
community_state = CommunityState()
event_stream = EventStream()
