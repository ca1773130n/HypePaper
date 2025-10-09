"""LLM extraction model for AI-extracted metadata.

AI-extracted metadata from paper content with verification workflow.
Many-to-one relationship with Paper.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID
import enum

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .paper import Paper


class ExtractionType(enum.Enum):
    """Types of LLM extractions."""
    TASK = "task"
    METHOD = "method"
    DATASET = "dataset"
    METRIC = "metric"
    LIMITATION = "limitation"
    COMPARISON = "comparison"


class VerificationStatus(enum.Enum):
    """Verification workflow states."""
    PENDING_REVIEW = "pending_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    AUTO_ACCEPTED = "auto_accepted"  # Future: ML-based auto-verification


class LLMExtraction(Base):
    """AI-extracted metadata from paper content.

    Many-to-one relationship with Paper.
    Supports manual verification workflow.
    """

    __tablename__ = "llm_extractions"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Foreign key
    paper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Extraction type
    extraction_type: Mapped[ExtractionType] = mapped_column(
        Enum(ExtractionType),
        nullable=False,
        index=True,
        comment="Type of metadata extracted"
    )

    # Extracted data
    primary_value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Primary extracted value"
    )

    secondary_value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Secondary extracted value"
    )

    tertiary_value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Tertiary extracted value"
    )

    all_values: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="All extracted values (for datasets/metrics)"
    )

    # LLM metadata
    llm_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="LLM provider: 'openai', 'llamacpp'"
    )

    llm_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Model name: 'gpt-4', 'Polaris-7B-preview'"
    )

    prompt_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Prompt template version for reproducibility"
    )

    raw_response: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Raw LLM response for debugging"
    )

    # Verification workflow
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus),
        default=VerificationStatus.PENDING_REVIEW,
        server_default=text("'pending_review'"),
        nullable=False,
        index=True,
        comment="Manual verification state"
    )

    verified_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Username of verifier"
    )

    verified_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Verification timestamp"
    )

    verification_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Verifier notes or rejection reason"
    )

    # Timestamps
    extracted_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        nullable=False
    )

    # Relationships
    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="llm_extractions"
    )

    __table_args__ = (
        Index("idx_llm_extractions_paper", "paper_id"),
        Index("idx_llm_extractions_type_status", "extraction_type", "verification_status"),
        Index("idx_llm_extractions_pending", "verification_status",
              postgresql_where=text("verification_status = 'pending_review'")),
    )

    def __repr__(self) -> str:
        return f"<LLMExtraction({self.extraction_type.value}, {self.verification_status.value})>"
