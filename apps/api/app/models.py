import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def uid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    complete = "complete"
    complete_with_warnings = "complete_with_warnings"
    failed = "failed"
    cancelled = "cancelled"


class ElementStatus(str, enum.Enum):
    detected = "detected"
    translated = "translated"
    unchanged = "unchanged"
    low_confidence = "low_confidence"
    failed = "failed"
    unsupported = "unsupported"
    manually_edited = "manually_edited"
    reviewed = "reviewed"


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    filename: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(Integer)
    source_path: Mapped[str] = mapped_column(Text)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    source_language: Mapped[str | None] = mapped_column(String(24))
    target_language: Mapped[str | None] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(40), default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    pages: Mapped[list["Page"]] = relationship(cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_index: Mapped[int] = mapped_column(Integer)
    width: Mapped[float] = mapped_column(Float)
    height: Mapped[float] = mapped_column(Float)
    page_type: Mapped[str] = mapped_column(String(24), default="digital")
    elements: Mapped[list["DocumentElement"]] = relationship(cascade="all, delete-orphan")


class DocumentElement(Base):
    __tablename__ = "document_elements"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    page_id: Mapped[str] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"), index=True)
    element_type: Mapped[str] = mapped_column(String(32), default="text")
    bounding_box: Mapped[dict] = mapped_column(JSON)
    rotation: Mapped[float] = mapped_column(Float, default=0)
    z_index: Mapped[int] = mapped_column(Integer, default=0)
    original_text: Mapped[str] = mapped_column(Text)
    translated_text: Mapped[str | None] = mapped_column(Text)
    source_language: Mapped[str | None] = mapped_column(String(24))
    target_language: Mapped[str | None] = mapped_column(String(24))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    translation_status: Mapped[str] = mapped_column(String(32), default=ElementStatus.detected.value)
    style_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(40), default=JobStatus.queued.value)
    current_stage: Mapped[str] = mapped_column(String(64), default="queued")
    current_page: Mapped[int] = mapped_column(Integer, default=0)
    total_pages: Mapped[int] = mapped_column(Integer, default=0)
    progress_percent: Mapped[float] = mapped_column(Float, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProviderConfiguration(Base):
    __tablename__ = "provider_configurations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(100))
    provider_type: Mapped[str] = mapped_column(String(40))
    base_url: Mapped[str] = mapped_column(String(500))
    encrypted_api_key: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(String(200))
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=60)
    max_retries: Mapped[int] = mapped_column(Integer, default=2)
    batch_size: Mapped[int] = mapped_column(Integer, default=12)
    context_size: Mapped[int] = mapped_column(Integer, default=8192)
    temperature: Mapped[float] = mapped_column(Float, default=0.1)
    custom_system_prompt: Mapped[str | None] = mapped_column(Text)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)


class Export(Base):
    __tablename__ = "exports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    export_type: Mapped[str] = mapped_column(String(40))
    path: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReviewIssue(Base):
    __tablename__ = "review_issues"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    element_id: Mapped[str | None] = mapped_column(ForeignKey("document_elements.id", ondelete="CASCADE"))
    issue_type: Mapped[str] = mapped_column(String(40))
    severity: Mapped[str] = mapped_column(String(16), default="warning")
    message: Mapped[str] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)

