from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    full_name = Column(String(100), default="")
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="reader", nullable=False)  # 'admin' or 'reader'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    progresses = relationship("ReadingProgress", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True, nullable=False)
    author = Column(String(150), default="ไม่ระบุผู้แต่ง", nullable=False)
    description = Column(Text, default="")
    category = Column(String(50), default="ทั่วไป", index=True)
    pdf_filename = Column(String(255), nullable=False)
    cover_filename = Column(String(255), default="")
    page_count = Column(Integer, default=0)
    file_size = Column(Integer, default=0)  # bytes
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    progresses = relationship("ReadingProgress", back_populates="book", cascade="all, delete-orphan")

    @property
    def formatted_size(self) -> str:
        if self.file_size <= 0:
            return "ไม่ระบุขนาด"
        if self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        return f"{self.file_size / (1024 * 1024):.1f} MB"


class ReadingProgress(Base):
    __tablename__ = "reading_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    last_page = Column(Integer, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="progresses")
    book = relationship("Book", back_populates="progresses")
