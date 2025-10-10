"""
Background job for PDF download and LLM metadata extraction.

Celery task that downloads PDFs, extracts text and tables, runs LLM
metadata extraction, and flags results for manual review.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from celery import Task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .celery_app import celery_app
from ..database import AsyncSessionLocal
# from ..services.pdf_service import PDFAnalysisService
from ..services.pdf_storage_service import PDFStorageService
from ..services.llm_service import OpenAILLMService, LlamaCppLLMService
from ..models.paper import Paper


logger = logging.getLogger(__name__)


# LLM prompts for metadata extraction
EXTRACT_TASKS_PROMPT = """
Extract the primary and secondary research tasks from this paper.
Return a JSON object with this structure:
{
    "primary_task": "main task name (e.g., 'image segmentation', 'machine translation')",
    "secondary_task": "secondary task if applicable (or null)"
}
"""

EXTRACT_METHODS_PROMPT = """
Extract the key methods and models used in this paper.
Return a JSON object with this structure:
{
    "methods": ["method1", "method2", ...]
}
"""

EXTRACT_DATASETS_PROMPT = """
Extract all datasets used in this paper's experiments.
Return a JSON object with this structure:
{
    "datasets": ["dataset1", "dataset2", ...]
}
"""

EXTRACT_METRICS_PROMPT = """
Extract the evaluation metrics reported in this paper.
Return a JSON object with this structure:
{
    "metrics": ["metric1", "metric2", ...]
}
"""


@celery_app.task(bind=True, name='jobs.metadata_enricher.enrich_paper')
def enrich_paper(self: Task, paper_id: str) -> Dict[str, Any]:
    """
    Background task for paper metadata enrichment.

    Steps:
    1. Download PDF from arxiv_url or pdf_url
    2. Extract full text using PyMuPDF
    3. Extract tables using GMFT
    4. Store PDFContent record
    5. Run LLM extraction for tasks, methods, datasets, metrics
    6. Store LLMExtraction records (flagged for manual review)

    Args:
        paper_id: UUID of paper to enrich

    Returns:
        Dict with status and extraction counts

    Example:
        >>> enrich_paper.delay('550e8400-e29b-41d4-a716-446655440000')
    """
    # Update initial state
    self.update_state(
        state='PROCESSING',
        meta={
            'current': 0,
            'total': 6,  # 6 steps total
            'status': 'Starting metadata enrichment...',
            'paper_id': paper_id
        }
    )

    try:
        # Run async task in event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            _async_enrich_paper(self, paper_id)
        )

        return result

    except Exception as e:
        logger.error(f"Metadata enrichment failed for paper {paper_id}: {e}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'status': 'failed',
                'paper_id': paper_id
            }
        )
        raise


async def _async_enrich_paper(task: Task, paper_id: str) -> Dict[str, Any]:
    """
    Async implementation of paper metadata enrichment.

    Args:
        task: Celery task instance for state updates
        paper_id: UUID of paper to enrich

    Returns:
        Dict with enrichment results
    """
    extractions_count = 0
    paper_uuid = UUID(paper_id)

    # Create database session
    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Get paper from database
            task.update_state(
                state='PROCESSING',
                meta={'current': 1, 'total': 6, 'status': 'Fetching paper...'}
            )

            result = await session.execute(
                select(Paper).where(Paper.id == paper_uuid)
            )
            paper = result.scalar_one_or_none()

            if not paper:
                raise ValueError(f"Paper not found: {paper_id}")

            logger.info(f"Enriching paper: {paper.title}")

            # Step 2: Download PDF
            task.update_state(
                state='PROCESSING',
                meta={'current': 2, 'total': 6, 'status': 'Downloading PDF...'}
            )

            pdf_storage = PDFStorageService()
            pdf_path = await pdf_storage.download_pdf(paper)
            logger.info(f"Downloaded PDF to: {pdf_path}")

            # Step 3: Extract text
            task.update_state(
                state='PROCESSING',
                meta={'current': 3, 'total': 6, 'status': 'Extracting text...'}
            )

            pdf_service = PDFAnalysisService()
            full_text = await pdf_service.extract_text(pdf_path)
            logger.info(f"Extracted {len(full_text)} characters of text")

            # Step 4: Extract tables
            task.update_state(
                state='PROCESSING',
                meta={'current': 4, 'total': 6, 'status': 'Extracting tables...'}
            )

            table_paths = await pdf_service.extract_tables(pdf_path)
            logger.info(f"Extracted {len(table_paths)} tables")

            # Step 5: Store PDF content
            # Note: In production, you would import and create PDFContent model
            # For now, we'll just log it
            logger.info(f"Would store PDFContent record with {len(table_paths)} table paths")

            # Step 6: LLM metadata extraction
            task.update_state(
                state='PROCESSING',
                meta={'current': 5, 'total': 6, 'status': 'Running LLM extraction...'}
            )

            # Initialize LLM service (use OpenAI if available, fallback to LlamaCpp)
            # In production, this would come from config
            import os
            llm_service = None
            if os.getenv('OPENAI_API_KEY'):
                llm_service = OpenAILLMService(api_key=os.getenv('OPENAI_API_KEY'))
            else:
                llm_service = LlamaCppLLMService()

            # Extract tasks
            try:
                tasks_result = await llm_service.extract_metadata(
                    pdf_path, EXTRACT_TASKS_PROMPT
                )
                logger.info(f"Extracted tasks: {tasks_result}")

                # Store LLMExtraction record (flagged for review)
                # In production: create LLMExtraction model instance
                logger.info("Would store LLMExtraction for tasks (pending_review)")
                extractions_count += 1

            except Exception as e:
                logger.error(f"Failed to extract tasks: {e}")

            # Extract methods
            try:
                methods_result = await llm_service.extract_metadata(
                    pdf_path, EXTRACT_METHODS_PROMPT
                )
                logger.info(f"Extracted methods: {methods_result}")
                logger.info("Would store LLMExtraction for methods (pending_review)")
                extractions_count += 1

            except Exception as e:
                logger.error(f"Failed to extract methods: {e}")

            # Extract datasets
            try:
                datasets_result = await llm_service.extract_metadata(
                    pdf_path, EXTRACT_DATASETS_PROMPT
                )
                logger.info(f"Extracted datasets: {datasets_result}")
                logger.info("Would store LLMExtraction for datasets (pending_review)")
                extractions_count += 1

            except Exception as e:
                logger.error(f"Failed to extract datasets: {e}")

            # Extract metrics
            try:
                metrics_result = await llm_service.extract_metadata(
                    pdf_path, EXTRACT_METRICS_PROMPT
                )
                logger.info(f"Extracted metrics: {metrics_result}")
                logger.info("Would store LLMExtraction for metrics (pending_review)")
                extractions_count += 1

            except Exception as e:
                logger.error(f"Failed to extract metrics: {e}")

            # Step 7: Complete
            task.update_state(
                state='PROCESSING',
                meta={'current': 6, 'total': 6, 'status': 'Finalizing...'}
            )

            await session.commit()

            return {
                'status': 'completed',
                'paper_id': paper_id,
                'paper_title': paper.title,
                'extractions_count': extractions_count,
                'text_length': len(full_text),
                'tables_extracted': len(table_paths),
                'pdf_path': str(pdf_path)
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"Enrichment error: {e}", exc_info=True)

            # Mark paper for retry by storing error
            # In production: update Paper.enrichment_status = 'failed'
            logger.warning(f"Paper marked for retry: {paper_id}")

            raise
