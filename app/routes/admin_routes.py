import uuid
from pathlib import Path
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import pypdf

from app.database import get_db
from app.models import Book, User
from app.auth import get_current_user_optional
from app.config import (
    PDF_UPLOAD_DIR,
    COVER_UPLOAD_DIR,
    ALLOWED_PDF_EXTENSIONS,
    ALLOWED_COVER_EXTENSIONS,
)
from app.sample_data import generate_svg_cover

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

def verify_admin_access(request: Request, db: Session) -> User:
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login?next=/admin"}
        )
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="คุณไม่มีสิทธิ์เข้าถึงหน้านี้ (เฉพาะผู้ดูแลระบบ Admin เท่านั้น)"
        )
    return user

@router.get("", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    current_user = verify_admin_access(request, db)

    books = db.query(Book).order_by(Book.id.desc()).all()
    total_books = len(books)
    total_users = db.query(User).count()
    total_readers = db.query(User).filter(User.role == "reader").count()
    total_views = sum(b.views or 0 for b in books)
    total_storage_bytes = sum(b.file_size or 0 for b in books)

    if total_storage_bytes < 1024 * 1024:
        storage_str = f"{total_storage_bytes / 1024:.1f} KB"
    else:
        storage_str = f"{total_storage_bytes / (1024 * 1024):.1f} MB"

    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "current_user": current_user,
            "books": books,
            "stats": {
                "total_books": total_books,
                "total_users": total_users,
                "total_readers": total_readers,
                "total_views": total_views,
                "storage_str": storage_str
            },
            "success_msg": request.query_params.get("success"),
            "error_msg": request.query_params.get("error")
        }
    )

@router.get("/add-book", response_class=HTMLResponse)
def add_book_page(request: Request, db: Session = Depends(get_db)):
    current_user = verify_admin_access(request, db)
    return templates.TemplateResponse(
        request=request,
        name="admin/add_book.html",
        context={
            "current_user": current_user,
            "error": None
        }
    )

@router.post("/add-book", response_class=HTMLResponse)
async def add_book_post(
    request: Request,
    title: str = Form(...),
    author: str = Form("ไม่ระบุผู้แต่ง"),
    category: str = Form("ทั่วไป"),
    description: str = Form(""),
    pdf_file: UploadFile = File(...),
    cover_file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    current_user = verify_admin_access(request, db)

    clean_title = title.strip()
    clean_author = author.strip() or "ไม่ระบุผู้แต่ง"
    clean_category = category.strip() or "ทั่วไป"
    clean_desc = description.strip()

    if not clean_title:
        return templates.TemplateResponse(
            request=request,
            name="admin/add_book.html",
            context={
                "current_user": current_user,
                "error": "กรุณาระบุชื่อหนังสือ"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 1. Strictly Validate PDF file
    if not pdf_file or not pdf_file.filename:
        return templates.TemplateResponse(
            request=request,
            name="admin/add_book.html",
            context={
                "current_user": current_user,
                "error": "กรุณาเลือกไฟล์ PDF หนังสือต้นฉบับ"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    pdf_ext = Path(pdf_file.filename).suffix.lower()
    if pdf_ext not in ALLOWED_PDF_EXTENSIONS:
        return templates.TemplateResponse(
            request=request,
            name="admin/add_book.html",
            context={
                "current_user": current_user,
                "error": "ระบบรองรับเฉพาะไฟล์เอกสารรูปแบบ PDF (.pdf) เท่านั้น"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Save PDF
    safe_pdf_name = f"{uuid.uuid4().hex[:12]}_{Path(pdf_file.filename).name}"
    pdf_destination = PDF_UPLOAD_DIR / safe_pdf_name

    pdf_content = await pdf_file.read()
    if len(pdf_content) == 0:
        return templates.TemplateResponse(
            request=request,
            name="admin/add_book.html",
            context={
                "current_user": current_user,
                "error": "ไฟล์ PDF ว่างเปล่า กรุณาอัปโหลดไฟล์ที่ถูกต้อง"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    with open(pdf_destination, "wb") as f:
        f.write(pdf_content)

    # Inspect PDF with pypdf to get page count
    file_size = len(pdf_content)
    page_count = 1
    try:
        reader = pypdf.PdfReader(str(pdf_destination))
        page_count = len(reader.pages)
    except Exception:
        page_count = 1

    # 2. Handle Cover Image
    cover_filename = ""
    if cover_file and cover_file.filename:
        cover_ext = Path(cover_file.filename).suffix.lower()
        if cover_ext in ALLOWED_COVER_EXTENSIONS:
            safe_cover_name = f"cover_{uuid.uuid4().hex[:12]}{cover_ext}"
            cover_dest = COVER_UPLOAD_DIR / safe_cover_name
            cover_content = await cover_file.read()
            with open(cover_dest, "wb") as f:
                f.write(cover_content)
            cover_filename = safe_cover_name

    # If no cover was uploaded, generate a modern SVG cover!
    if not cover_filename:
        safe_cover_name = f"cover_{uuid.uuid4().hex[:12]}.svg"
        cover_dest = COVER_UPLOAD_DIR / safe_cover_name
        
        # Color palettes based on category hash
        palettes = [
            ("#3B82F6", "#1D4ED8"),
            ("#10B981", "#047857"),
            ("#8B5CF6", "#6D28D9"),
            ("#F59E0B", "#B45309"),
            ("#EC4899", "#BE185D"),
            ("#06B6D4", "#0E7490")
        ]
        color_idx = abs(hash(clean_category)) % len(palettes)
        g_start, g_end = palettes[color_idx]

        generate_svg_cover(
            cover_dest,
            title=clean_title,
            author=clean_author,
            category=clean_category,
            gradient_start=g_start,
            gradient_end=g_end
        )
        cover_filename = safe_cover_name

    # Save to database
    new_book = Book(
        title=clean_title,
        author=clean_author,
        category=clean_category,
        description=clean_desc,
        pdf_filename=safe_pdf_name,
        cover_filename=cover_filename,
        page_count=page_count,
        file_size=file_size,
        views=0
    )
    db.add(new_book)
    db.commit()

    return RedirectResponse(
        url="/admin?success=เพิ่มหนังสือเรียบร้อยแล้ว",
        status_code=status.HTTP_302_FOUND
    )

@router.post("/delete-book/{book_id}")
def delete_book(book_id: int, request: Request, db: Session = Depends(get_db)):
    verify_admin_access(request, db)

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return RedirectResponse(url="/admin?error=ไม่พบหนังสือที่ต้องการลบ", status_code=status.HTTP_302_FOUND)

    # Delete physical files
    try:
        pdf_path = PDF_UPLOAD_DIR / book.pdf_filename
        if pdf_path.exists():
            pdf_path.unlink()
        if book.cover_filename:
            cover_path = COVER_UPLOAD_DIR / book.cover_filename
            if cover_path.exists():
                cover_path.unlink()
    except Exception:
        pass

    db.delete(book)
    db.commit()

    return RedirectResponse(url="/admin?success=ลบหนังสือออกจากระบบสำเร็จ", status_code=status.HTTP_302_FOUND)
