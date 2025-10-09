"""
PDF storage service for managing structured filesystem paths.

Provides utilities for organizing PDF files and extracted tables in a
consistent directory structure based on paper metadata.
"""

import asyncio
from pathlib import Path
from typing import List, Optional
from datetime import datetime

import aiohttp


class PDFStorageService:
    """
    Service for managing PDF file storage and retrieval.

    Features:
    - Structured filesystem paths: /data/papers/{year}/{arxiv_id}/
    - Table CSV management
    - Async PDF download
    - Path generation from paper metadata
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize PDF storage service.

        Args:
            base_path: Base directory for PDF storage
                      (defaults to /data/papers)
        """
        if base_path is None:
            base_path = Path('/data/papers')

        self.base_path = Path(base_path)

        # Ensure base path exists
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_pdf_path(self, paper: any) -> Path:
        """
        Get structured filesystem path for paper's PDF.

        Structure: {base_path}/{year}/{paper_id}/{paper_id}.pdf

        Args:
            paper: Paper object with year, arxiv_id, and id attributes

        Returns:
            Path to PDF file
        """
        # Determine year directory
        year = getattr(paper, 'year', None) or 'unknown'

        # Determine paper identifier (prefer arxiv_id)
        if hasattr(paper, 'arxiv_id') and paper.arxiv_id:
            paper_id = paper.arxiv_id
        elif hasattr(paper, 'id') and paper.id:
            paper_id = str(paper.id)
        else:
            # Fallback to timestamp-based ID
            paper_id = f"paper_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Create paper directory
        paper_dir = self.base_path / str(year) / paper_id
        paper_dir.mkdir(parents=True, exist_ok=True)

        # Return PDF path
        return paper_dir / f"{paper_id}.pdf"

    def get_table_paths(self, paper: any) -> List[Path]:
        """
        Get paths to all table CSV files for a paper.

        Tables are named: {paper_id}.table00.csv, {paper_id}.table01.csv, etc.

        Args:
            paper: Paper object

        Returns:
            List of paths to table CSV files (sorted)
        """
        pdf_path = self.get_pdf_path(paper)
        parent_dir = pdf_path.parent

        # Find all table CSV files
        pattern = f"{pdf_path.stem}.table*.csv"
        table_paths = sorted(parent_dir.glob(pattern))

        return list(table_paths)

    def get_paper_directory(self, paper: any) -> Path:
        """
        Get directory containing all files for a paper.

        Args:
            paper: Paper object

        Returns:
            Path to paper's directory
        """
        pdf_path = self.get_pdf_path(paper)
        return pdf_path.parent

    async def download_pdf(
        self,
        paper: any,
        url: Optional[str] = None
    ) -> Path:
        """
        Download PDF file for a paper.

        Args:
            paper: Paper object with pdf_url attribute
            url: Override PDF URL (optional)

        Returns:
            Path to downloaded PDF file

        Raises:
            ValueError: If no PDF URL available
            aiohttp.ClientError: If download fails
        """
        # Determine PDF URL
        pdf_url = url
        if not pdf_url:
            if hasattr(paper, 'pdf_url') and paper.pdf_url:
                pdf_url = paper.pdf_url
            else:
                raise ValueError("No PDF URL available for paper")

        # Get target path
        pdf_path = self.get_pdf_path(paper)

        # Skip if already exists
        if pdf_path.exists():
            return pdf_path

        # Download PDF
        async with aiohttp.ClientSession() as session:
            async with session.get(
                pdf_url,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response.raise_for_status()

                # Write to file
                with open(pdf_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)

        return pdf_path

    def delete_paper_files(self, paper: any) -> bool:
        """
        Delete all files associated with a paper.

        Removes PDF and all table CSV files.

        Args:
            paper: Paper object

        Returns:
            True if successful, False otherwise
        """
        try:
            paper_dir = self.get_paper_directory(paper)

            if paper_dir.exists():
                # Delete all files in directory
                for file in paper_dir.iterdir():
                    if file.is_file():
                        file.unlink()

                # Remove directory if empty
                if not any(paper_dir.iterdir()):
                    paper_dir.rmdir()

                return True

        except Exception as e:
            print(f"Error deleting paper files: {e}")

        return False

    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage info (total files, size, etc.)
        """
        stats = {
            'total_papers': 0,
            'total_pdfs': 0,
            'total_tables': 0,
            'total_size_bytes': 0
        }

        try:
            # Walk through all year directories
            for year_dir in self.base_path.iterdir():
                if not year_dir.is_dir():
                    continue

                # Walk through paper directories
                for paper_dir in year_dir.iterdir():
                    if not paper_dir.is_dir():
                        continue

                    stats['total_papers'] += 1

                    # Count files
                    for file in paper_dir.iterdir():
                        if file.is_file():
                            if file.suffix == '.pdf':
                                stats['total_pdfs'] += 1
                            elif file.suffix == '.csv':
                                stats['total_tables'] += 1

                            stats['total_size_bytes'] += file.stat().st_size

        except Exception as e:
            print(f"Error calculating storage stats: {e}")

        return stats

    def ensure_directory_structure(self, year: int, paper_id: str) -> Path:
        """
        Ensure directory structure exists for a paper.

        Args:
            year: Publication year
            paper_id: Paper identifier

        Returns:
            Path to paper directory
        """
        paper_dir = self.base_path / str(year) / paper_id
        paper_dir.mkdir(parents=True, exist_ok=True)
        return paper_dir

    def get_all_pdf_paths(self) -> List[Path]:
        """
        Get paths to all PDF files in storage.

        Returns:
            List of paths to all PDF files
        """
        pdf_paths = []

        try:
            # Recursively find all PDF files
            pdf_paths = list(self.base_path.rglob('*.pdf'))
        except Exception as e:
            print(f"Error finding PDF files: {e}")

        return sorted(pdf_paths)

    def paper_exists(self, paper: any) -> bool:
        """
        Check if PDF exists for a paper.

        Args:
            paper: Paper object

        Returns:
            True if PDF file exists
        """
        pdf_path = self.get_pdf_path(paper)
        return pdf_path.exists()


# Global singleton instance
_storage_service: Optional[PDFStorageService] = None


def get_storage_service(base_path: Optional[Path] = None) -> PDFStorageService:
    """
    Get or create global PDFStorageService instance.

    Args:
        base_path: Override base path for storage

    Returns:
        Singleton PDFStorageService instance
    """
    global _storage_service
    if _storage_service is None:
        _storage_service = PDFStorageService(base_path)
    return _storage_service
