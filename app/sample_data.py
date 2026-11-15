from pathlib import Path
from sqlalchemy.orm import Session
from app.config import PDF_UPLOAD_DIR, COVER_UPLOAD_DIR
from app.models import User, Book
from app.auth import hash_password

def generate_svg_cover(filepath: Path, title: str, author: str, category: str, gradient_start: str, gradient_end: str):
    """Generate a clean, modern SVG book cover."""
    # Truncate strings if too long
    display_title = title if len(title) <= 30 else title[:27] + "..."
    display_author = author if len(author) <= 30 else author[:27] + "..."
    
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 580" width="400" height="580">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{gradient_start};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{gradient_end};stop-opacity:1" />
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="6" flood-opacity="0.3"/>
    </filter>
  </defs>
  <!-- Background -->
  <rect width="400" height="580" rx="16" fill="url(#grad)" />
  <!-- Spine effect -->
  <rect x="0" y="0" width="22" height="580" rx="0" fill="rgba(0,0,0,0.18)" />
  <line x1="22" y1="0" x2="22" y2="580" stroke="rgba(255,255,255,0.15)" stroke-width="2" />
  
  <!-- Category Badge -->
  <g transform="translate(45, 50)">
    <rect width="110" height="28" rx="14" fill="rgba(255,255,255,0.2)" />
    <text x="55" y="18" fill="#ffffff" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="600" text-anchor="middle">{category}</text>
  </g>

  <!-- Decorative Book Icon / Pattern -->
  <g transform="translate(200, 200)" filter="url(#shadow)">
    <circle cx="0" cy="0" r="48" fill="rgba(255,255,255,0.15)" />
    <path d="M-22,-14 C-10,-20 0,-14 0,-14 C0,-14 10,-20 22,-14 L22,18 C10,12 0,18 0,18 C0,18 -10,12 -22,18 Z" fill="none" stroke="#ffffff" stroke-width="3.5" stroke-linejoin="round" />
    <line x1="0" y1="-14" x2="0" y2="18" stroke="#ffffff" stroke-width="3" />
  </g>

  <!-- Title & Author Card -->
  <g transform="translate(45, 330)">
    <text x="0" y="0" fill="#ffffff" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="24" font-weight="bold" width="310">
      <tspan x="0" dy="0">{display_title}</tspan>
    </text>
    <line x1="0" y1="50" x2="60" y2="50" stroke="rgba(255,255,255,0.6)" stroke-width="3" stroke-linecap="round" />
    <text x="0" y="85" fill="rgba(255,255,255,0.85)" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="15" font-weight="500">
      โดย {display_author}
    </text>
  </g>

  <!-- Footer Tag -->
  <text x="200" y="535" fill="rgba(255,255,255,0.5)" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" text-anchor="middle" letter-spacing="2">
    PRCT DIGITAL LIBRARY - PDF
  </text>
</svg>"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(svg)


def create_simple_pdf(filepath: Path, pages: list[str]):
    """Generate a clean, valid PDF file with pages."""
    num_pages = len(pages)
    page_obj_ids = [4 + 2 * i for i in range(num_pages)]
    font_obj_id = 4 + 2 * num_pages

    objs = []
    objs.append((1, b"<< /Type /Catalog /Pages 3 0 R >>"))
    objs.append((2, b"<< /Type /Outlines /Count 0 >>"))

    kids_str = " ".join([f"{pid} 0 R" for pid in page_obj_ids])
    objs.append((3, f"<< /Type /Pages /Count {num_pages} /Kids [ {kids_str} ] >>".encode("ascii")))

    for i, p_text in enumerate(pages):
        page_id = page_obj_ids[i]
        content_id = page_id + 1

        lines = p_text.split("\n")
        stream_cmds = ["BT", "/F1 15 Tf", "50 780 Td", "24 TL"]
        for line in lines:
            safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream_cmds.append(f"({safe}) Tj")
            stream_cmds.append("T*")
        stream_cmds.append("ET")
        stream_bytes = "\n".join(stream_cmds).encode("latin1", "replace")

        page_body = f"<< /Type /Page /Parent 3 0 R /MediaBox [0 0 595 842] /Contents {content_id} 0 R /Resources << /Font << /F1 {font_obj_id} 0 R >> >> >>".encode("ascii")
        content_body = f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii") + stream_bytes + b"\nendstream"

        objs.append((page_id, page_body))
        objs.append((content_id, content_body))

    objs.append((font_obj_id, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"))

    with open(filepath, "wb") as f:
        f.write(b"%PDF-1.4\n")
        xref_offsets = [0]
        for obj_id, body in objs:
            xref_offsets.append(f.tell())
            f.write(f"{obj_id} 0 obj\n".encode("ascii"))
            f.write(body)
            f.write(b"\nendobj\n")

        xref_pos = f.tell()
        f.write(f"xref\n0 {len(objs)+1}\n".encode("ascii"))
        f.write(b"0000000000 65535 f \n")
        for offset in xref_offsets[1:]:
            f.write(f"{offset:010d} 00000 n \n".encode("ascii"))
        f.write(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii"))


def seed_initial_data(db: Session):
    """Seed default users and sample books if database is empty."""
    # 1. Seed Users
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        admin_user = User(
            username="admin",
            email="admin@prctlib.local",
            full_name="ผู้ดูแลระบบ (Admin)",
            password_hash=hash_password("admin123"),
            role="admin"
        )
        db.add(admin_user)

    reader_user = db.query(User).filter(User.username == "reader").first()
    if not reader_user:
        reader_user = User(
            username="reader",
            email="reader@prctlib.local",
            full_name="นักอ่านทั่วไป (Reader)",
            password_hash=hash_password("reader123"),
            role="reader"
        )
        db.add(reader_user)

    db.commit()

    # 2. Seed Sample Books if none exist
    book_count = db.query(Book).count()
    if book_count == 0:
        sample_books = [
            {
                "title": "FastAPI & Python Web Development",
                "author": "Antigravity Team",
                "category": "เทคโนโลยี",
                "description": "คู่มือการพัฒนาเว็บแอพพลิเคชันสมัยใหม่ด้วย FastAPI และ Python สำหรับนักพัฒนา รองรับ High-Performance Asynchronous IO และการ Deploy บน Render.com อย่างราบรื่น",
                "pdf_file": "fastapi_guide.pdf",
                "cover_file": "fastapi_guide.svg",
                "grad_start": "#4F46E5",
                "grad_end": "#06B6D4",
                "pages": [
                    "FastAPI & Modern Python Web Guide\n\nChapter 1: Introduction to FastAPI\nFastAPI is a modern, fast (high-performance) web framework\nfor building APIs with Python 3.8+ based on standard Python type hints.\n\nKey Highlights:\n- Fast: Very high performance, on par with NodeJS and Go\n- Fast to code: Increases speed to develop features by 200% to 300%\n- Fewer bugs: Reduces about 40% of developer induced errors\n- Intuitive: Great editor support, auto-completion everywhere\n- Easy: Designed to be easy to use and learn\n- Standards-based: Based on OpenAPI and JSON Schema\n\nPage 1 of 3",
                    "Chapter 2: Production Deployment on Render.com\n\nDeploying FastAPI on Render.com is simple and powerful:\n\n1. Web Service Configuration:\n   - Environment: Python 3.12\n   - Build Command: pip install -r requirements.txt\n   - Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT\n\n2. Environment Variables:\n   - Set SECRET_KEY for secure cookie sessions\n   - Connect managed PostgreSQL or SQLite\n\n3. Mobile Responsiveness:\n   - The mobile-first reader provides smooth PDF canvas rendering\n   - Touch zoom, dark mode, and page bookmarks.\n\nPage 2 of 3",
                    "Chapter 3: PDF Document Architecture & Best Practices\n\nWhen building digital libraries:\n- Validate PDF mime types on upload (application/pdf)\n- Stream files with range requests for fast mobile reading\n- Track user reading progress across devices\n- Role-based access control ensures secure content delivery\n\nThank you for reading this guide!\nPRCT Digital Library System.\n\nPage 3 of 3"
                ]
            },
            {
                "title": "The Art of Reading & Habit Building",
                "author": "Dr. S. K. Walker",
                "category": "พัฒนาตนเอง",
                "description": "ศาสตร์และศิลป์แห่งการอ่านหนังสือในยุคข้อมูลล้นหลาม เทคนิคการจดจำ การสร้างนิสัยรักการอ่านวันละ 20 นาที และการนำความรู้ไปประยุกต์ใช้ในชีวิตจริง",
                "pdf_file": "art_of_reading.pdf",
                "cover_file": "art_of_reading.svg",
                "grad_start": "#059669",
                "grad_end": "#10B981",
                "pages": [
                    "The Art of Reading in the Digital Age\n\nChapter 1: The Habit of Continuous Reading\nReading is not just about finishing pages; it is about expanding\nyour mental models and transforming perspective.\n\nBenefits of Daily 20-minute Reading:\n- Enhanced cognitive flexibility\n- Reduced cortisol and stress levels\n- Deep focused attention span in a distracted world\n- Continuous compounding of knowledge\n\nPage 1 of 2",
                    "Chapter 2: Digital vs Physical Reading Experience\n\nWith modern mobile e-readers:\n- You carry an entire library in your pocket\n- High resolution mobile screens provide comfortable reading anywhere\n- Bookmark progress saves your exact position automatically\n\nEnjoy your reading journey today!\n\nPage 2 of 2"
                ]
            },
            {
                "title": "Mobile UX Design Systems 2026",
                "author": "Elena Chen & Studio Design",
                "category": "การออกแบบ",
                "description": "แนวทางการออกแบบส่วนต่อประสานผู้ใช้ (UI) และประสบการณ์ผู้ใช้ (UX) บนหน้าจอมือถือ เน้น Touch Gestures, Typography, Dark Mode และ Navigation ที่ใช้งานง่ายที่สุด",
                "pdf_file": "mobile_ux_design.pdf",
                "cover_file": "mobile_ux_design.svg",
                "grad_start": "#D97706",
                "grad_end": "#EA580C",
                "pages": [
                    "Mobile UX Design Systems 2026\n\nChapter 1: The Thumb Zone & Touch Targets\nOver 75% of smartphone users navigate with one thumb.\nEssential navigation and action buttons must be placed within easy reach\nat the bottom portion of the display.\n\nKey Principles:\n- Minimum touch target: 48x48 dp\n- Clear typography contrast for outdoor daylight reading\n- Smooth gesture handling for page swipes and zooms\n\nPage 1 of 2",
                    "Chapter 2: Immersive Reader UI\n\nWhen users read a document on a mobile device:\n- Eliminate clutter and distraction\n- Use subtle, floating controls that fade when reading\n- Support seamless toggle between Day and Night themes\n- Provide immediate visual feedback for loading and page flips\n\nCreated for PRCT Mobile Library.\n\nPage 2 of 2"
                ]
            }
        ]

        for item in sample_books:
            pdf_path = PDF_UPLOAD_DIR / item["pdf_file"]
            cover_path = COVER_UPLOAD_DIR / item["cover_file"]

            create_simple_pdf(pdf_path, item["pages"])
            generate_svg_cover(
                cover_path,
                title=item["title"],
                author=item["author"],
                category=item["category"],
                gradient_start=item["grad_start"],
                gradient_end=item["grad_end"]
            )

            file_size = pdf_path.stat().st_size if pdf_path.exists() else 0
            page_count = len(item["pages"])

            book = Book(
                title=item["title"],
                author=item["author"],
                description=item["description"],
                category=item["category"],
                pdf_filename=item["pdf_file"],
                cover_filename=item["cover_file"],
                page_count=page_count,
                file_size=file_size,
                views=12
            )
            db.add(book)

        db.commit()
