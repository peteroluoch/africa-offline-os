"""
Mesh API Router - Inbound P2P Communication.
Handles signed heartbeats and delta-sync delivery from remote nodes.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, Body, Form
from typing import Dict, Any
from pydantic import BaseModel
from aos.core.security.identity import NodeIdentityManager
from aos.core.config import Settings
from aos.api.state import mesh_state

router = APIRouter(tags=["mesh"])

# Core identity manager (needs to be injected or retrieved from app state)
_identity_manager = NodeIdentityManager()

class HeartbeatPayload(BaseModel):
    node_id: str
    timestamp: str
    signature: str
    public_key: str

class SyncEnvelope(BaseModel):
    origin_id: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: float

class SyncRequest(BaseModel):
    envelope: SyncEnvelope
    signature: str

@router.post("/mesh/heartbeat")
async def receive_heartbeat(payload: HeartbeatPayload):
    """
    Receive and verify a heartbeat from a remote node.
    """
    # 1. Verify Signature
    is_valid = _identity_manager.verify(
        data=payload.timestamp.encode(),
        signature=bytes.fromhex(payload.signature),
        public_key_bytes=bytes.fromhex(payload.public_key)
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid node signature"
        )
    
    # 2. Logic to update mesh registry goes here
    # For now, we just acknowledge
    return {"status": "ok", "message": f"Heartbeat verified from {payload.node_id}"}

@router.post("/mesh/sync")
async def receive_sync(request: SyncRequest):
    """
    Receive and verify a delta sync payload.
    """
    # 1. Reconstruct signing data
    # Note: Must match RemoteNodeAdapter.send_delta logic
    envelope = request.envelope
    sign_data = f"{envelope.origin_id}:{envelope.timestamp}:{envelope.event_type}".encode()
    
    # 2. In a real scenario, we'd lookup the public key for origin_id in our Peer DB
    # For this batch, we assume the peer must have performed a heartbeat first 
    # and we have their public key.
    # TEMPORARY: Assume we have their key from a registry (Stubbed for now)
    # is_valid = _identity_manager.verify(sign_data, ...)
    
    # 3. Process the event (dispatch to local event bus)
    return {"status": "accepted", "origin": envelope.origin_id}

@router.post("/sys/mesh/register")
async def register_peer_ui(
    node_id: str = Form(...),
    base_url: str = Form(...),
    public_key: str = Form(...)
):
    """
    Handle peer registration from the UI.
    Returns an HTML fragment for HTMX.
    """
    if not mesh_state.manager:
        raise HTTPException(status_code=500, detail="Mesh Manager not initialized")
    
    mesh_state.manager.register_peer(node_id, base_url, public_key)
    
    # Return HTMX fragment for the new peer row
    return f"""
    <div class="fade-in bg-white/5 border border-white/10 p-4 rounded-xl flex items-center justify-between hover:bg-white/[0.08] transition-all">
        <div class="flex items-center space-x-4">
            <div class="w-10 h-10 rounded-lg bg-blue-600/20 flex items-center justify-center text-blue-400">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path></svg>
            </div>
            <div>
                <div class="text-sm font-bold text-white aos-text-display">{node_id}</div>
                <div class="text-[10px] text-slate-500 aos-text-mono">{base_url}</div>
            </div>
        </div>
        <div class="flex items-center space-x-4">
            <span class="text-[10px] text-slate-400 aos-text-mono opacity-50">{public_key[:16]}...</span>
            <span class="px-3 py-1 bg-yellow-500/10 text-yellow-500 text-[10px] font-bold rounded-full uppercase tracking-wider">SYNCING</span>
        </div>
    </div>
    """
