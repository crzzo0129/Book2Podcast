import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text, Float
from sqlalchemy.dialects.sqlite import JSON
from database import Base
import enum


class BookStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ChapterStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Book(Base):
    __tablename__ = "books"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_path = Column(String(1000), nullable=False)
    status = Column(String(20), default=BookStatus.UPLOADED.value)
    total_chapters = Column(Integer, default=0)
    completed_chapters = Column(Integer, default=0)
    chapter_list = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id = Column(String(36), nullable=False, index=True)
    index = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    content_text = Column(Text, nullable=True)
    status = Column(String(20), default=ChapterStatus.PENDING.value)
    script = Column(Text, nullable=True)
    audio_path = Column(String(1000), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id = Column(String(36), nullable=False, index=True)
    chapter_id = Column(String(36), nullable=True, index=True)
    task_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    progress = Column(Integer, default=0)
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
