from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
import sqlite3
from pathlib import Path

from aos.api.app import get_db
from aos.core.security.auth import auth_manager
from aos.core.security.password import verify_password
from aos.db.models import OperatorDTO # Actually we query raw DB for now or need Repo

router = APIRouter(tags=["auth"])

@router.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve login page."""
    template_path = Path(__file__).parent.parent / "templates" / "login.html"
    if not template_path.exists():
        return HTMLResponse("Login template not found", status_code=404)
    return HTMLResponse(template_path.read_text(encoding="utf-8"))

@router.post("/auth/login")
async def login(
    username: str = Form(...), 
    password: str = Form(...),
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Authenticate user and return JWT or Redirect.
    We use Form data to support standard HTML submission easily.
    """
    try:
        print(f"[Auth] Attempting login for: {username}")
        cursor = db.execute(
            "SELECT id, username, password_hash, role_id FROM operators WHERE username=?", 
            (username,)
        )
        row = cursor.fetchone()
        
        if not row:
            print(f"[Auth] User not found: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )
            
        op_id, op_username, op_hash, op_role = row
        
        if not verify_password(password, op_hash):
            print(f"[Auth] Invalid password for: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )
            
        print(f"[Auth] Success for {username}. Issuing token...")
        # Generate Token
        token = auth_manager.issue_token(payload={
            "sub": op_id,
            "username": op_username,
            "role": op_role
        })
        
        print(f"[Auth] Token issued. Setting cookie and redirecting...")
        # Return JSON with token
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {token}",
            httponly=True,
            max_age=3600,
            samesite="lax",
            secure=False  # Allow http for localhost
        )
        return response
    except Exception as e:
        print(f"[Auth] CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
