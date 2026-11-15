from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import get_db
from app.models import Book, ReadingProgress
from app.auth import get_current_user_optional

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    q: str = "",
    category: str = "",
    db: Session = Depends(get_db)
):
    current_user = get_current_user_optional(request, db)

    # Base query
    query = db.query(Book)

    if q.strip():
        search_term = f"%{q.strip()}%"
        query = query.filter(
            (Book.title.ilike(search_term)) |
            (Book.author.ilike(search_term)) |
            (Book.description.ilike(search_term))
        )

    if category.strip() and category != "all":
        query = query.filter(Book.category == category.strip())

    books = query.order_by(Book.id.desc()).all()

    # Get distinct categories
    all_categories = [r[0] for r in db.query(Book.category).distinct().all() if r[0]]

    # If user is logged in, attach their reading progress
    progress_map = {}
    if current_user:
        user_progresses = db.query(ReadingProgress).filter(ReadingProgress.user_id == current_user.id).all()
        for p in user_progresses:
            progress_map[p.book_id] = p.last_page

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "books": books,
            "categories": all_categories,
            "selected_category": category or "all",
            "search_query": q,
            "current_user": current_user,
            "progress_map": progress_map,
            "registered": request.query_params.get("registered") == "1",
            "book_added": request.query_params.get("book_added") == "1"
        }
    )
