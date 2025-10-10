"""Crawler job model for persistent job tracking."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String, Text, Integer, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CrawlerJob(Base):
    """Crawler job tracking with logs.

    Stores crawler job status and metadata in database instead of in-memory.
    Persists across server restarts.
    """

    __tablename__ = "crawler_jobs"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Job metadata
    job_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # processing, completed, failed

    # Job configuration
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # arxiv, etc.
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    period: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # daily, weekly, monthly

    # Progress tracking
    papers_crawled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    references_crawled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Logs stored as JSONB array
    logs: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    next_run: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
        nullable=False,
    )
