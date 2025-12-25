from __future__ import annotations
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from aos.api.state import transport_state
from aos.core.security.auth import get_current_operator
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter(prefix="/transport", tags=["transport"])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/", response_class=HTMLResponse)
async def transport_root(request: Request, current_user: dict = Depends(get_current_operator)):
    """Main Transport Dashboard."""
    if not transport_state.module:
        return HTMLResponse("TransportModule not initialized", status_code=500)
    
    routes = transport_state.module.list_routes()
    
    return templates.TemplateResponse(
        "transport.html",
        {
            "request": request,
            "user": current_user,
            "routes": routes
        }
    )

@router.get("/route/{route_id}", response_class=HTMLResponse)
async def route_details(route_id: str, request: Request, current_user: dict = Depends(get_current_operator)):
    """View details and vehicle status for a specific route."""
    if not transport_state.module:
        return HTMLResponse("TransportModule not initialized", status_code=500)
    
    status = transport_state.module.get_route_status(route_id)
    
    return templates.TemplateResponse(
        "partials/transport_route_details.html",
        {
            "request": request,
            "route_status": status
        }
    )

@router.post("/vehicle/status", response_class=HTMLResponse)
async def update_vehicle_status(
    plate: str = Form(...),
    status: str = Form(...),
    route_id: str = Form(None),
    current_user: dict = Depends(get_current_operator)
):
    """Update vehicle status (Matatu-facing logic)."""
    if not transport_state.module:
        return HTMLResponse("TransportModule not initialized", status_code=500)
    
    success = transport_state.module.update_vehicle_status(plate, status, route_id)
    
    if success:
        return f'<div class="aos-badge aos-badge-success fade-in">Status Updated: {plate} -> {status}</div>'
    return f'<div class="aos-badge aos-badge-error fade-in">Update Failed for {plate}</div>'
