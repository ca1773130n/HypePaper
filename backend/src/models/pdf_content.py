"""PDF content model for extracted paper content.

Extracted content from paper PDFs including full text and tables.
One-to-one relationship with Paper.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .paper import Paper


class PDFContent(Base):
    """Extracted content from paper PDFs.

    One-to-one relationship with Paper.
    Stores full text, tables, and references.
    """

    __tablename__ = "pdf_contents"

    # Primary key (also foreign key)
    paper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        primary_key=True
    )

    # Extracted text content
    full_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Complete extracted text from PDF"
    )

    # References section
    references_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Raw text from References/Bibliography section"
    )

    parsed_references: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of parsed citation strings"
    )

    # Table extraction
    table_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
        comment="Number of tables extracted"
    )

    table_csv_paths: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of CSV file paths: ['paper.table00.csv', ...]"
    )

    # Extraction metadata
    extraction_method: Mapped[str] = mapped_column(
        String(50),
        default="pymupdf",
        nullable=False,
        comment="PDF parser used: 'pymupdf', 'pdfplumber'"
    )

    table_extraction_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Table extractor used: 'gmft', 'camelot'"
    )

    extraction_success: Mapped[bool] = mapped_column(
        default=True,
        server_default=text("true"),
        nullable=False,
        comment="Whether extraction succeeded"
    )

    extraction_errors: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of error messages if extraction failed"
    )

    # Parser versions
    pymupdf_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="PyMuPDF version used"
    )

    gmft_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="GMFT version used for table extraction"
    )

    # Timestamps
    extracted_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        nullable=False,
        comment="When PDF was processed"
    )

    # Relationships
    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="pdf_content"
    )

    __table_args__ = (
        Index(
            "idx_pdf_contents_fulltext_fts",
            text("to_tsvector('english', full_text)"),
            postgresql_using="gin",
        ),
        Index(
            "idx_pdf_contents_references_fts",
            text("to_tsvector('english', references_text)"),
            postgresql_using="gin",
        ),
    )

    def __repr__(self) -> str:
        return f"<PDFContent({self.paper_id}: {len(self.full_text)} chars, {self.table_count} tables)>"
