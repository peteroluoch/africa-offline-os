"""
RemoteNode Adapter - Secure Mesh Communication Layer.
Handles peer-to-peer discovery and status-aware synchronization.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from aos.core.adapter import Adapter
from aos.core.config import settings
from aos.core.security.identity import NodeIdentityManager


@dataclass
class RemoteNode:
    """Represents a peer node in the mesh network."""
    node_id: str
    base_url: str
    public_key: str
    last_seen: float = 0.0
    status: str = "OFFLINE"  # ONLINE, MESH, OFFLINE
    metadata: dict[str, Any] = field(default_factory=dict)

class RemoteNodeAdapter(Adapter):
    """
    Adapter for communicating with remote nodes.
    Ensures all outgoing requests are signed and verified.
    """

    def __init__(self, identity_manager: NodeIdentityManager):
        self.identity_manager = identity_manager
        self.peers: dict[str, RemoteNode] = {}
        self.client = httpx.AsyncClient(timeout=5.0)
        self._connected = False

    async def connect(self) -> None:
        """Initialize the adapter."""
        if not self._connected:
            self.identity_manager.ensure_identity()
            self._connected = True

    async def disconnect(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
        self._connected = False

    async def health_check(self) -> bool:
        """Verify the adapter is operational."""
        return self._connected

    def register_peer(self, node_id: str, base_url: str, public_key: str) -> None:
        """Register a new peer in the node's mesh registry."""
        if node_id not in self.peers:
            self.peers[node_id] = RemoteNode(
                node_id=node_id,
                base_url=base_url,
                public_key=public_key
            )

    async def send_heartbeat(self, peer_id: str) -> bool:
        """
        Send a signed heartbeat to a peer.
        This proves our identity and updates our status in the mesh.
        """
        if peer_id not in self.peers:
            return False

        peer = self.peers[peer_id]
        timestamp = str(time.time()).encode()

        # Sign the heartbeat with our private key
        signature = self.identity_manager.sign(timestamp)

        payload = {
            "node_id": settings.node_id,
            "timestamp": timestamp.decode(),
            "signature": signature.hex(),
            "public_key": self.identity_manager.get_public_key().hex()
        }

        try:
            response = await self.client.post(
                f"{peer.base_url}/mesh/heartbeat",
                json=payload
            )

            if response.status_code == 200:
                peer.last_seen = time.time()
                peer.status = "ONLINE"
                return True
            else:
                peer.status = "OFFLINE"
                return False
        except Exception:
            peer.status = "OFFLINE"
            return False

    async def broadcast_event(self, event_type: str, payload: dict[str, Any]) -> list[str]:
        """
        Broadcast an event to all known peers.
        Returns a list of node IDs that successfully received the event.
        """
        successful_peers = []
        for peer_id in self.peers:
            success = await self.send_delta(peer_id, event_type, payload)
            if success:
                successful_peers.append(peer_id)
        return successful_peers

    async def send_delta(self, peer_id: str, event_type: str, payload: dict[str, Any]) -> bool:
        """Send a delta sync payload to a specific peer."""
        if peer_id not in self.peers:
            return False

        peer = self.peers[peer_id]

        # Prepare signed envelope
        envelope = {
            "origin_id": settings.node_id,
            "event_type": event_type,
            "payload": payload,
            "timestamp": time.time()
        }

        # Sign the serialized envelope
        # (Simplified for this version - real implementation would stringify/canonicalize)
        sign_data = f"{envelope['origin_id']}:{envelope['timestamp']}:{event_type}".encode()
        signature = self.identity_manager.sign(sign_data)

        request_data = {
            "envelope": envelope,
            "signature": signature.hex()
        }

        try:
            response = await self.client.post(
                f"{peer.base_url}/mesh/sync",
                json=request_data
            )
            return response.status_code == 200
        except Exception:
            return False
