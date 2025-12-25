"""
Mesh Sync Manager - Orchestrates mesh communication and persistence.
Ties together the Adapter and the Queue for high-level synchronization logic.
"""
from __future__ import annotations
import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from aos.adapters.remote_node import RemoteNodeAdapter
from aos.core.mesh.queue import MeshQueue
from aos.core.security.identity import NodeIdentityManager

logger = logging.getLogger("aos.mesh")

class MeshSyncManager:
    """
    Orchestrates the mesh network lifecycle.
    """
    
    def __init__(
        self, 
        adapter: RemoteNodeAdapter, 
        queue: MeshQueue,
        sync_interval: int = 60
    ):
        self.adapter = adapter
        self.queue = queue
        self.sync_interval = sync_interval
        self._sync_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Initialize adapter and start background sync task."""
        if not self._running:
            await self.adapter.connect()
            self._running = True
            self._sync_task = asyncio.create_task(self._run_background_sync())
            logger.info("MeshSyncManager started")

    async def stop(self) -> None:
        """Stop background task and disconnect adapter."""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        await self.adapter.disconnect()
        logger.info("MeshSyncManager stopped")

    async def _run_background_sync(self) -> None:
        """Background loop to retry pending syncs and send heartbeats."""
        while self._running:
            try:
                # 1. Send Heartbeats to all peers
                for peer_id in list(self.adapter.peers.keys()):
                    await self.adapter.send_heartbeat(peer_id)
                
                # 2. Process Queue
                pending = self.queue.get_pending()
                for item in pending:
                    success = await self.adapter.send_delta(
                        peer_id=item["target_node_id"],
                        event_type=item["event_type"],
                        payload=json.loads(item["payload"]) if isinstance(item["payload"], str) else item["payload"]
                    )
                    
                    if success:
                        self.queue.mark_success(item["id"])
                    else:
                        self.queue.mark_failed(item["id"])
                        
            except Exception as e:
                logger.error(f"Error in background sync: {e}")
                
            await asyncio.sleep(self.sync_interval)

    def enqueue_broadcast(self, event_type: str, payload: Dict[str, Any], priority: int = 1) -> None:
        """Enqueue an event for all known peers."""
        for peer_id in self.adapter.peers:
            self.queue.enqueue(peer_id, event_type, payload, priority)

    def register_peer(self, node_id: str, base_url: str, public_key: str) -> None:
        """Register a peer and perform an initial heartbeat."""
        self.adapter.register_peer(node_id, base_url, public_key)
        # We don't await here, background task will pick it up or we can fire-and-forget
        asyncio.create_task(self.adapter.send_heartbeat(node_id))
