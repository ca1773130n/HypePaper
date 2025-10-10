"""PDF download and storage service."""
import os
from pathlib import Path
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Paper
from ..config import get_settings


class PDFService:
    """Service for PDF management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.storage_path = Path(self.settings.pdf_storage_base_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def download_pdf(self, paper_id: UUID) -> Path:
        """Download PDF for a paper if not already downloaded.

        Args:
            paper_id: Paper UUID

        Returns:
            Path to downloaded PDF

        Raises:
            ValueError: If paper not found or no PDF URL
            HTTPError: If download fails
        """
        # Get paper
        result = await self.db.execute(select(Paper).where(Paper.id == paper_id))
        paper = result.scalar_one_or_none()

        if not paper:
            raise ValueError(f"Paper {paper_id} not found")

        # Check if already downloaded
        if paper.pdf_local_path and Path(paper.pdf_local_path).exists():
            return Path(paper.pdf_local_path)

        # Download PDF
        if not paper.pdf_url:
            raise ValueError(f"Paper {paper_id} has no PDF URL")

        pdf_path = self.storage_path / f"{paper_id}.pdf"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(paper.pdf_url)
            response.raise_for_status()

            with open(pdf_path, "wb") as f:
                f.write(response.content)

        # Update paper record
        paper.pdf_local_path = str(pdf_path)
        from datetime import datetime
        paper.pdf_downloaded_at = datetime.utcnow()
        await self.db.commit()

        return pdf_path

    async def get_pdf_path(self, paper_id: UUID) -> Optional[Path]:
        """Get local PDF path if exists.

        Args:
            paper_id: Paper UUID

        Returns:
            Path to PDF or None if not downloaded
        """
        result = await self.db.execute(select(Paper).where(Paper.id == paper_id))
        paper = result.scalar_one_or_none()

        if not paper or not paper.pdf_local_path:
            return None

        path = Path(paper.pdf_local_path)
        return path if path.exists() else None
