from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import get_db
from app.models import User
from app.auth import (
    hash_password,
    verify_password,
    create_session_token,
    get_current_user_optional,
)
from app.config import SESSION_COOKIE_NAME, SESSION_MAX_AGE

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str = "/", db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url=next or "/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "next": next,
            "error": None,
            "current_user": None
        }
    )

@router.post("/login", response_class=HTMLResponse)
def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
    db: Session = Depends(get_db)
):
    clean_username = username.strip()
    user = db.query(User).filter(
        (User.username == clean_username) | (User.email == clean_username)
    ).first()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "next": next,
                "error": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง",
                "username": username,
                "current_user": None
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Valid login -> set session cookie
    token = create_session_token(user.id, user.role)
    redirect_target = next if next and next.startswith("/") else "/"
    response = RedirectResponse(url=redirect_target, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False  # Allow both http and https for render/local
    )
    return response

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "error": None,
            "current_user": None
        }
    )

@router.post("/register", response_class=HTMLResponse)
def register_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(""),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    clean_username = username.strip().lower()
    clean_email = email.strip().lower()

    # Validation
    if len(clean_username) < 3:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "error": "ชื่อผู้ใช้ต้องมีความยาวอย่างน้อย 3 ตัวอักษร",
                "username": username,
                "email": email,
                "full_name": full_name,
                "current_user": None
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    if len(password) < 6:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "error": "รหัสผ่านต้องมีความยาวอย่างน้อย 6 ตัวอักษร",
                "username": username,
                "email": email,
                "full_name": full_name,
                "current_user": None
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    if password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "error": "รหัสผ่านและยืนยันรหัสผ่านไม่ตรงกัน",
                "username": username,
                "email": email,
                "full_name": full_name,
                "current_user": None
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Check duplicate
    existing = db.query(User).filter((User.username == clean_username) | (User.email == clean_email)).first()
    if existing:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "error": "ชื่อผู้ใช้หรืออีเมลนี้ถูกใช้งานแล้ว กรุณาใช้ชื่ออื่น",
                "username": username,
                "email": email,
                "full_name": full_name,
                "current_user": None
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Create new reader user
    new_user = User(
        username=clean_username,
        email=clean_email,
        full_name=full_name.strip() or clean_username,
        password_hash=hash_password(password),
        role="reader"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Automatically log the new user in
    token = create_session_token(new_user.id, new_user.role)
    response = RedirectResponse(url="/?registered=1", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False
    )
    return response

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response
