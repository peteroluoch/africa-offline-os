from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from aos.api.state import community_state
from aos.core.security.auth import get_current_operator
from aos.db.models import CommunityGroupDTO

router = APIRouter(prefix="/community", tags=["community"])
templates = Jinja2Templates(directory="aos/api/templates")

@router.get("/", response_class=HTMLResponse)
async def community_dashboard(request: Request, operator=Depends(get_current_operator)):
    groups = community_state.module.list_groups() if community_state.module else []
    
    # Mock some counts for the dashboard
    broadcasts_count = 0
    if community_state.module:
        broadcasts_count = len(community_state.module._announcements.list_all())

    return templates.TemplateResponse("community.html", {
        "request": request,
        "operator": operator,
        "groups": groups,
        "broadcasts_count": broadcasts_count,
        "inquiry_hits": 0
    })

@router.get("/register", response_class=HTMLResponse)
async def community_register_form(request: Request):
    return templates.TemplateResponse("partials/community_group_form.html", {"request": request})

@router.post("/register")
async def register_community_group(
    request: Request,
    name: str = Form(...),
    group_type: str = Form(...),
    description: str = Form(""),
    operator=Depends(get_current_operator)
):
    if community_state.module:
        await community_state.module.register_group(
            name=name,
            group_type=group_type,
            admin_id=operator.id,
            description=description
        )
    return RedirectResponse(url="/community", status_code=303)
