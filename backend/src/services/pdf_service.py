"""
PDF analysis service with text and table extraction.

Provides async wrappers around synchronous PDF processing libraries
(PyMuPDF for text, GMFT for tables) using ThreadPoolExecutor.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF
# Import from gmft v0.2.1 API (no 'auto' module)
from gmft import (
    AutoTableDetector,
    AutoTableFormatter,
    AutoFormatConfig,
    TATRFormatConfig
)
from gmft.table_detection import TATRTableDetector, TableDetectorConfig
from gmft.pdf_bindings import PyPDFium2Document


class PDFAnalysisService:
    """
    Service for extracting text and tables from PDF files.

    Uses:
    - PyMuPDF (fitz) for text extraction
    - GMFT (AutoTableDetector) for table detection and extraction
    - ThreadPoolExecutor for async wrapper around sync libraries
    """

    def __init__(self, max_workers: int = 4):
        """
        Initialize PDF analysis service.

        Args:
            max_workers: Maximum number of threads for PDF processing
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Initialize GMFT table detector (reusable across requests)
        # For gmft v0.2.1, use TableDetectorConfig
        detector_config = TableDetectorConfig()
        detector_config.detector_base_threshold = 0.75
        self.table_detector = AutoTableDetector(detector_config)

        # Initialize table formatter
        formatter_config = AutoFormatConfig()
        formatter_config.verbosity = 3
        formatter_config.enable_multi_header = True
        formatter_config.semantic_spanning_cells = True
        self.table_formatter = AutoTableFormatter(config=formatter_config)

    async def extract_text(self, pdf_path: Path) -> str:
        """
        Extract full text from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text as string

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If text extraction fails
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._extract_text_sync,
            pdf_path
        )

    def _extract_text_sync(self, pdf_path: Path) -> str:
        """
        Synchronous text extraction using PyMuPDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text
        """
        try:
            doc = fitz.open(pdf_path)
            text_parts = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                text_parts.append(text)

            doc.close()

            return '\n\n'.join(text_parts)

        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {e}")

    async def extract_tables(self, pdf_path: Path) -> List[Path]:
        """
        Extract tables from PDF and save as CSV files.

        Tables are saved as:
        - {pdf_path}.table00.csv
        - {pdf_path}.table01.csv
        - etc.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of paths to generated CSV files

        Raises:
            FileNotFoundError: If PDF file doesn't exist
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._extract_tables_sync,
            pdf_path
        )

    def _extract_tables_sync(self, pdf_path: Path) -> List[Path]:
        """
        Synchronous table extraction using GMFT.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of CSV file paths
        """
        table_paths = []

        try:
            # Open PDF with PyPDFium2 (required by GMFT)
            doc = PyPDFium2Document(str(pdf_path))
            table_index = 0

            # Process each page
            for page in doc:
                # Detect tables on page
                tables = self.table_detector.extract(page)

                # Extract and save each table
                for table in tables:
                    try:
                        # Format table to DataFrame
                        extracted = self.table_formatter.extract(table)
                        df = extracted.df()

                        # Save as CSV with zero-padded index
                        csv_filename = f"{pdf_path.stem}.table{table_index:02d}.csv"
                        csv_path = pdf_path.parent / csv_filename
                        df.to_csv(csv_path, index=False)

                        table_paths.append(csv_path)
                        table_index += 1

                    except Exception as e:
                        # Log but continue processing other tables
                        print(f"Failed to extract table {table_index}: {e}")
                        continue

            doc.close()

        except Exception as e:
            print(f"Failed to extract tables from PDF: {e}")

        return table_paths

    async def extract_references(self, pdf_path: Path) -> List[str]:
        """
        Extract reference section from PDF.

        Attempts to find and extract the references/bibliography section
        from the PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of reference strings
        """
        full_text = await self.extract_text(pdf_path)

        # Find references section (common headers)
        ref_headers = [
            'References',
            'REFERENCES',
            'Bibliography',
            'BIBLIOGRAPHY',
            'Works Cited'
        ]

        references = []
        lines = full_text.split('\n')

        # Find start of references section
        ref_start_idx = -1
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if line_stripped in ref_headers:
                ref_start_idx = i + 1
                break

        if ref_start_idx > 0:
            # Extract lines after references header
            # Stop at next section header or end
            for i in range(ref_start_idx, len(lines)):
                line = lines[i].strip()

                # Skip empty lines
                if not line:
                    continue

                # Stop at next major section
                if line.isupper() and len(line) > 20:
                    break

                # Add to references
                references.append(line)

        return references

    def __del__(self):
        """Cleanup executor on deletion."""
        self.executor.shutdown(wait=False)
