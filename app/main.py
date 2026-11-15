from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database import engine, Base, SessionLocal
from app.sample_data import seed_initial_data
from app.routes import home_routes, auth_routes, book_routes, admin_routes

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and seed initial users/books
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="PRCT Mobile PDF Library",
    description="เว็บแอพสำหรับอ่านหนังสือไฟล์ PDF เน้นประสบการณ์อ่านบนมือถือ พร้อมระบบสมาชิกและแอดมิน",
    version="1.0.0",
    lifespan=lifespan
)

# Mount Static Files
static_dir = BASE_DIR / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Include Routers
app.include_router(home_routes.router)
app.include_router(auth_routes.router)
app.include_router(book_routes.router)
app.include_router(admin_routes.router)

@app.get("/healthz")
def health_check():
    return {"status": "healthy", "service": "prct-lib-python"}

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={"current_user": None},
        status_code=404
    )
