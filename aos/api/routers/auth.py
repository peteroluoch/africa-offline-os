import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from aos.api.dependencies import get_db
from aos.api.state import auth_manager, community_state
from aos.core.security.password import verify_password, get_password_hash
from aos.core.security.auth import AosRole

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request, db: sqlite3.Connection = Depends(get_db)):
    """Serve signup page with community selection."""
    cursor = db.execute("SELECT id, name FROM community_groups WHERE active=1")
    communities = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]
    return templates.TemplateResponse("signup.html", {"request": request, "communities": communities})

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
            """
            SELECT o.id, o.username, o.password_hash, r.name, o.community_id 
            FROM operators o
            JOIN roles r ON o.role_id = r.id
            WHERE o.username=?
            """,
            (username,)
        )
        row = cursor.fetchone()

        if not row:
            print(f"[Auth] User not found: {username}")
            return HTMLResponse(
                content="<html><body><h1>Login Failed</h1><p>Incorrect username or password</p><a href='/login'>Try again</a></body></html>",
                status_code=401
            )

        op_id, op_username, op_hash, op_role, op_community_id = row

        if not verify_password(password, op_hash):
            print(f"[Auth] Invalid password for: {username}")
            return HTMLResponse(
                content="<html><body><h1>Login Failed</h1><p>Incorrect username or password</p><a href='/login'>Try again</a></body></html>",
                status_code=401
            )

        print(f"[Auth] Success for {username}. Issuing token...")
        # Generate Token
        token = auth_manager.issue_token(payload={
            "sub": op_id,
            "username": op_username,
            "role": op_role,
            "community_id": op_community_id
        })

        print("[Auth] Token issued. Setting cookie and redirecting...")
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
@router.get("/auth/logout")
@router.post("/auth/logout")
async def logout():
    """
    Clear authentication session and redirect to login.
    Supports both GET and POST for maximum compatibility.
    """
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    # Clear the access_token cookie
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=None,
        httponly=True,
        samesite="lax",
        secure=False  # Keep consistent with login
    )
    print("[Auth] Logout successful. Session cleared.")
    return response

@router.post("/auth/signup")
async def signup(
    username: str = Form(...),
    password: str = Form(...),
    community_id: str = Form(None),
    create_new: bool = Form(False),
    community_name: str = Form(None),
    community_type: str = Form(None),
    location: str = Form(None),
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Self-Registration for Field Agents.
    Defaults to 'operator' role for safety.
    """
    try:
        from aos.core.security.password import get_password_hash
        import uuid
        from datetime import UTC, datetime

        # 1. Check if username exists
        check = db.execute("SELECT id FROM operators WHERE username=?", (username,)).fetchone()
        if check:
            return HTMLResponse(
                content="<html><body><h1>Signup Failed</h1><p>Username already taken</p><a href='/signup'>Try again</a></body></html>",
                status_code=400
            )

        # 2. Assign role and generate ID
        # Default to 'operator' unless they are creating a community, then they are 'admin'
        role_name = 'admin' if create_new else 'operator'
        role_row = db.execute("SELECT id FROM roles WHERE name=?", (role_name,)).fetchone()
        if not role_row:
             return HTMLResponse(content=f"System misconfigured: {role_name} role missing.", status_code=500)
        
        role_id = role_row[0]
        op_id = str(uuid.uuid4())
        pw_hash = get_password_hash(password)

        # 3. Handle Community Creation if requested
        final_community_id = community_id
        if create_new:
            if not community_name:
                return HTMLResponse(content="Community name required for new registration", status_code=400)
            
            if community_state.module:
                new_group = await community_state.module.register_group(
                    name=community_name,
                    tags=[community_type] if community_type else [],
                    location=location or "Remote",
                    admin_id=op_id,
                    group_type=community_type or "Generic"
                )
                final_community_id = new_group.id
            else:
                return HTMLResponse(content="Community module not initialized", status_code=500)

        if not final_community_id:
             return HTMLResponse(content="Please select a community or create a new one.", status_code=400)

        # 4. Create the user
        db.execute(
            "INSERT INTO operators (id, username, password_hash, role_id, community_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (op_id, username, pw_hash, role_id, final_community_id, datetime.now(UTC).isoformat())
        )
        db.commit()

        print(f"[Auth] New {role_name} registered: {username} for community {final_community_id}")
        
        # 5. Redirect to login with success message
        return RedirectResponse(url="/login?msg=Signup+success!+Please+login.", status_code=status.HTTP_303_SEE_OTHER)

    except Exception as e:
        print(f"[Auth] Signup Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during registration")
