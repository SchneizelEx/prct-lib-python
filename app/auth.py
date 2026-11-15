import hashlib
import hmac
import secrets
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.config import SECRET_KEY, SESSION_COOKIE_NAME, SESSION_MAX_AGE
from app.database import get_db
from app.models import User

serializer = URLSafeTimedSerializer(SECRET_KEY)

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with secure random salt."""
    salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return f"{salt}:{pw_hash}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored salt:hash."""
    try:
        salt, stored_hash = hashed_password.split(":")
        calc_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
        return hmac.compare_digest(stored_hash, calc_hash)
    except Exception:
        return False

def create_session_token(user_id: int, role: str) -> str:
    """Create signed session token containing user_id and role."""
    return serializer.dumps({"user_id": user_id, "role": role})

def decode_session_token(token: str) -> Optional[dict]:
    """Decode and verify signed session token."""
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
        return data
    except (BadSignature, SignatureExpired, Exception):
        return None

def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get current user from session cookie, returns None if not logged in."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    data = decode_session_token(token)
    if not data or "user_id" not in data:
        return None
    user = db.query(User).filter(User.id == data["user_id"]).first()
    return user

def require_login(request: Request, db: Session = Depends(get_db)) -> User:
    """Ensure user is logged in. Raises 401 redirect or error if unauthenticated."""
    user = get_current_user_optional(request, db)
    if not user:
        # Check if requested format is HTML or API
        accept = request.headers.get("accept", "")
        if "text/html" in accept or not request.url.path.startswith("/api/"):
            login_url = f"/login?next={request.url.path}"
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": login_url}
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="กรุณาเข้าสู่ระบบก่อนใช้งาน"
        )
    return user

def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    """Ensure user is logged in AND is an admin."""
    user = require_login(request, db)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="คุณไม่มีสิทธิ์เข้าถึงส่วนนี้ (สำหรับผู้ดูแลระบบเท่านั้น)"
        )
    return user
