"""Policy pages router - Privacy Policy, Terms & Conditions, Cookie Policy."""
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from aos.core.security.auth import get_current_operator

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/privacy")
async def privacy_policy(request: Request, current_user: dict = Depends(get_current_operator)):
    """Privacy Policy page."""
    return templates.TemplateResponse("privacy.html", {
        "request": request,
        "user": current_user
    })


@router.get("/terms")
async def terms_conditions(request: Request, current_user: dict = Depends(get_current_operator)):
    """Terms & Conditions page."""
    return templates.TemplateResponse("terms.html", {
        "request": request,
        "user": current_user
    })


@router.get("/cookies")
async def cookie_policy(request: Request, current_user: dict = Depends(get_current_operator)):
    """Cookie Policy page."""
    return templates.TemplateResponse("cookies.html", {
        "request": request,
        "user": current_user
    })
