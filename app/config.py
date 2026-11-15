import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "prct-lib-secret-key-render-2026-super-secure-token")
SESSION_COOKIE_NAME = "prct_lib_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

# Database URL (handles render postgresql prefix fix if used)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'prct_lib.db'}")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Upload directories
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "app" / "static" / "uploads"))
PDF_UPLOAD_DIR = UPLOAD_DIR / "pdfs"
COVER_UPLOAD_DIR = UPLOAD_DIR / "covers"

# Ensure upload folders exist
PDF_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
COVER_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions
ALLOWED_PDF_EXTENSIONS = {".pdf"}
ALLOWED_COVER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_SIZE_MB", "50"))  # 50MB
