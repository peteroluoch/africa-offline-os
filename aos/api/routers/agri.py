from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from aos.api.state import agri_state
from aos.core.security.auth import get_current_operator
from aos.db.models import FarmerDTO, HarvestDTO

router = APIRouter(prefix="/agri", tags=["agri"])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/", response_class=HTMLResponse)
async def agri_root(request: Request, current_user: dict = Depends(get_current_operator)):
    """Main Agricultural Dashboard."""
    if not agri_state.module:
        return HTMLResponse("AgriModule not initialized", status_code=500)

    farmers = agri_state.module.list_all_farmers()
    crops = agri_state.module.list_crops()

    return templates.TemplateResponse(
        "agri.html",
        {
            "request": request,
            "user": current_user,
            "farmers": farmers,
            "crops": crops
        }
    )

@router.post("/farmer", response_class=HTMLResponse)
async def register_farmer(
    request: Request,
    name: str = Form(...),
    location: str = Form(...),
    contact: str = Form(...),
    current_user: dict = Depends(get_current_operator)
):
    """Register a new farmer."""
    if not agri_state.module:
         return HTMLResponse("AgriModule not initialized", status_code=500)

    farmer = FarmerDTO(
        id=str(uuid.uuid4()),
        name=name,
        location=location,
        contact=contact
    )

    await agri_state.module.register_farmer(farmer)

    # Return HTMX snippet - redirected or just updated list
    # For now, let's refresh the page via HTMX header or return a simple fragment
    return templates.TemplateResponse(
        "partials/farmer_list.html",
        {"request": request, "farmers": agri_state.module.list_all_farmers()}
    )

@router.get("/farmer/new", response_class=HTMLResponse)
async def new_farmer_form(request: Request, current_user: dict = Depends(get_current_operator)):
    """Return the farmer registration form."""
    return templates.TemplateResponse(
        "partials/farmer_form.html",
        {"request": request}
    )

@router.get("/harvest/new", response_class=HTMLResponse)
async def new_harvest_form(request: Request, farmer_id: str, current_user: dict = Depends(get_current_operator)):
    """Return the harvest recording form."""
    if not agri_state.module:
         return HTMLResponse("AgriModule not initialized", status_code=500)

    crops = agri_state.module.list_crops()
    return templates.TemplateResponse(
        "partials/harvest_form.html",
        {"request": request, "farmer_id": farmer_id, "crops": crops}
    )

@router.post("/harvest", response_class=HTMLResponse)
async def record_harvest(
    request: Request,
    farmer_id: str = Form(...),
    crop_id: str = Form(...),
    quantity: float = Form(...),
    unit: str = Form("kg"),
    quality_grade: str = Form(...),
    current_user: dict = Depends(get_current_operator)
):
    """Record a harvest."""
    if not agri_state.module:
         return HTMLResponse("AgriModule not initialized", status_code=500)

    harvest = HarvestDTO(
        id=str(uuid.uuid4()),
        farmer_id=farmer_id,
        crop_id=crop_id,
        quantity=quantity,
        unit=unit,
        quality_grade=quality_grade,
        harvest_date=datetime.now(UTC),
        status="stored"
    )

    await agri_state.module.record_harvest(harvest)

    return f'<div class="aos-badge aos-badge-success fade-in">Harvest Recorded: {quantity}{unit}</div>'
