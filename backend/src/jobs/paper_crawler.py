"""
Background job for paper discovery from multiple sources.

Celery task that crawls papers from ArXiv, conferences, or citations
and stores them in the database with duplicate detection.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from celery import Task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .celery_app import celery_app
from ..database import AsyncSessionLocal
from ..services.arxiv_service import AsyncArxivService
from ..models.paper import Paper


logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='jobs.paper_crawler.crawl_papers')
def crawl_papers(self: Task, source: str, **kwargs) -> Dict[str, Any]:
    """
    Background task for paper discovery from multiple sources.

    Args:
        source: Source type - 'arxiv', 'conference', or 'citations'
        **kwargs: Source-specific parameters:
            - arxiv_keywords: Keywords for ArXiv search
            - arxiv_max_results: Maximum results (default: 100)
            - conference_name: Conference to crawl
            - citation_depth: Depth for citation-based discovery

    Returns:
        Dict with status and papers_discovered count

    Examples:
        >>> crawl_papers.delay('arxiv', arxiv_keywords='transformer', arxiv_max_results=10)
        >>> crawl_papers.delay('conference', conference_name='NeurIPS 2024')
        >>> crawl_papers.delay('citations', paper_id='uuid-here', citation_depth=2)
    """
    # Update initial state
    self.update_state(
        state='PROCESSING',
        meta={'current': 0, 'total': 0, 'status': f'Starting {source} crawl...'}
    )

    try:
        # Run async task in event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            _async_crawl_papers(self, source, **kwargs)
        )

        return result

    except Exception as e:
        logger.error(f"Paper crawl failed: {e}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'failed'}
        )
        raise


async def _async_crawl_papers(
    task: Task,
    source: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Async implementation of paper crawling.

    Args:
        task: Celery task instance for state updates
        source: Source type
        **kwargs: Source-specific parameters

    Returns:
        Dict with crawl results
    """
    papers_discovered = 0
    papers_stored = 0

    # Create database session
    async with AsyncSessionLocal() as session:
        try:
            if source == 'arxiv':
                papers_discovered, papers_stored = await _crawl_arxiv(
                    task, session, **kwargs
                )
            elif source == 'conference':
                papers_discovered, papers_stored = await _crawl_conference(
                    task, session, **kwargs
                )
            elif source == 'citations':
                papers_discovered, papers_stored = await _crawl_citations(
                    task, session, **kwargs
                )
            else:
                raise ValueError(f"Unknown source: {source}")

            # Commit all changes
            await session.commit()

            return {
                'status': 'completed',
                'source': source,
                'papers_discovered': papers_discovered,
                'papers_stored': papers_stored,
                'duplicates_skipped': papers_discovered - papers_stored
            }

        except Exception as e:
            await session.rollback()
            raise


async def _crawl_arxiv(
    task: Task,
    session: AsyncSession,
    arxiv_keywords: Optional[str] = None,
    arxiv_max_results: int = 100,
    **kwargs
) -> tuple[int, int]:
    """
    Crawl papers from ArXiv API.

    Args:
        task: Celery task for progress updates
        session: Database session
        arxiv_keywords: Search keywords
        arxiv_max_results: Maximum results

    Returns:
        Tuple of (papers_discovered, papers_stored)
    """
    if not arxiv_keywords:
        raise ValueError("arxiv_keywords is required for ArXiv crawl")

    logger.info(f"Crawling ArXiv for keywords: {arxiv_keywords}")

    # Initialize ArXiv service
    arxiv_service = AsyncArxivService()

    # Search for papers
    task.update_state(
        state='PROCESSING',
        meta={'current': 0, 'total': arxiv_max_results, 'status': 'Searching ArXiv...'}
    )

    paper_data = await arxiv_service.search_by_keywords(
        keywords=arxiv_keywords,
        max_results=arxiv_max_results
    )

    papers_discovered = len(paper_data)
    papers_stored = 0

    logger.info(f"Found {papers_discovered} papers from ArXiv")

    # Store papers in database
    for i, data in enumerate(paper_data):
        # Update progress
        task.update_state(
            state='PROCESSING',
            meta={
                'current': i + 1,
                'total': papers_discovered,
                'status': f"Storing paper {i + 1}/{papers_discovered}..."
            }
        )

        # Check for duplicates (by arxiv_id or legacy_id)
        existing = None
        if data.get('arxiv_id'):
            result = await session.execute(
                select(Paper).where(Paper.arxiv_id == data['arxiv_id'])
            )
            existing = result.scalar_one_or_none()

        if existing:
            logger.debug(f"Skipping duplicate paper: {data.get('title')}")
            continue

        # Create paper object
        try:
            paper = Paper(
                arxiv_id=data.get('arxiv_id'),
                doi=data.get('doi'),
                title=data['title'],
                authors=data.get('authors', []),
                abstract=data.get('abstract', ''),
                published_date=datetime.fromisoformat(data['published_date']).date() if data.get('published_date') else datetime.utcnow().date(),
                venue=data.get('journal_ref'),
                arxiv_url=data.get('url'),
                pdf_url=data.get('pdf_url'),
                year=data.get('year')
            )

            session.add(paper)
            papers_stored += 1
            logger.debug(f"Stored paper: {paper.title}")

        except Exception as e:
            logger.error(f"Failed to store paper: {e}", exc_info=True)
            continue

    return papers_discovered, papers_stored


async def _crawl_conference(
    task: Task,
    session: AsyncSession,
    conference_name: Optional[str] = None,
    **kwargs
) -> tuple[int, int]:
    """
    Crawl papers from conference proceedings.

    Args:
        task: Celery task for progress updates
        session: Database session
        conference_name: Name of conference to crawl

    Returns:
        Tuple of (papers_discovered, papers_stored)
    """
    if not conference_name:
        raise ValueError("conference_name is required for conference crawl")

    logger.info(f"Crawling conference: {conference_name}")

    # TODO: Implement conference crawling
    # This would integrate with conference-specific APIs or scrapers
    # For now, return placeholder

    task.update_state(
        state='PROCESSING',
        meta={'current': 0, 'total': 0, 'status': f'Conference crawling not yet implemented'}
    )

    logger.warning(f"Conference crawling not yet implemented for: {conference_name}")
    return 0, 0


async def _crawl_citations(
    task: Task,
    session: AsyncSession,
    paper_id: Optional[str] = None,
    citation_depth: int = 1,
    **kwargs
) -> tuple[int, int]:
    """
    Discover papers via citation relationships.

    Args:
        task: Celery task for progress updates
        session: Database session
        paper_id: Starting paper UUID
        citation_depth: How many levels to traverse

    Returns:
        Tuple of (papers_discovered, papers_stored)
    """
    if not paper_id:
        raise ValueError("paper_id is required for citation-based discovery")

    logger.info(f"Discovering papers via citations from: {paper_id}")

    # TODO: Implement citation-based discovery
    # This would:
    # 1. Get paper's references from PDF
    # 2. Parse citations with AnyStyle
    # 3. Fuzzy match to existing papers
    # 4. Search for unmatched citations
    # 5. Recursively traverse to specified depth

    task.update_state(
        state='PROCESSING',
        meta={'current': 0, 'total': 0, 'status': f'Citation-based discovery not yet implemented'}
    )

    logger.warning(f"Citation-based discovery not yet implemented for: {paper_id}")
    return 0, 0
