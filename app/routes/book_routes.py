from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from pydantic import BaseModel

from app.database import get_db
from app.models import Book, ReadingProgress, User
from app.auth import get_current_user_optional
from app.config import PDF_UPLOAD_DIR

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

class ProgressUpdate(BaseModel):
    page: int

@router.get("/books/{book_id}/read", response_class=HTMLResponse)
def read_book_page(book_id: int, request: Request, db: Session = Depends(get_db)):
    # Enforce login: Reading requires login!
    current_user = get_current_user_optional(request, db)
    if not current_user:
        return RedirectResponse(
            url=f"/login?next=/books/{book_id}/read",
            status_code=status.HTTP_302_FOUND
        )

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="ไม่พบหนังสือที่ต้องการอ่าน")

    # Increment views
    book.views = (book.views or 0) + 1
    db.commit()

    # Get user's saved progress
    progress = db.query(ReadingProgress).filter(
        ReadingProgress.user_id == current_user.id,
        ReadingProgress.book_id == book.id
    ).first()

    last_page = progress.last_page if progress else 1

    return templates.TemplateResponse(
        request=request,
        name="read.html",
        context={
            "book": book,
            "current_user": current_user,
            "last_page": last_page
        }
    )

@router.get("/api/books/{book_id}/pdf")
def stream_book_pdf(book_id: int, request: Request, db: Session = Depends(get_db)):
    # Enforce login: Reading stream requires authentication
    current_user = get_current_user_optional(request, db)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="กรุณาเข้าสู่ระบบก่อนเปิดอ่านเอกสาร PDF"
        )

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="ไม่พบหนังสือ")

    pdf_path = PDF_UPLOAD_DIR / book.pdf_filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="ไฟล์ PDF ไม่พบบนเซิร์ฟเวอร์")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=book.pdf_filename,
        content_disposition_type="inline"
    )

@router.post("/api/books/{book_id}/progress")
def save_reading_progress(
    book_id: int,
    payload: ProgressUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user_optional(request, db)
    if not current_user:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return JSONResponse(status_code=404, content={"error": "Book not found"})

    page_num = max(1, payload.page)
    progress = db.query(ReadingProgress).filter(
        ReadingProgress.user_id == current_user.id,
        ReadingProgress.book_id == book.id
    ).first()

    if not progress:
        progress = ReadingProgress(user_id=current_user.id, book_id=book.id, last_page=page_num)
        db.add(progress)
    else:
        progress.last_page = page_num

    db.commit()
    return {"status": "ok", "saved_page": page_num}
