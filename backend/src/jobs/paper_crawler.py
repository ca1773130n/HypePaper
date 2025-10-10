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
    conference_url: Optional[str] = None,
    conference_year: Optional[int] = None,
    **kwargs
) -> tuple[int, int]:
    """
    Crawl papers from conference proceedings using PaperCopilot tables.

    Supports CVPR and ICLR conferences from PaperCopilot website.

    Args:
        task: Celery task for progress updates
        session: Database session
        conference_name: Name of conference (CVPR or ICLR)
        conference_url: URL of PaperCopilot conference page
        conference_year: Conference year

    Returns:
        Tuple of (papers_discovered, papers_stored)

    Example:
        >>> _crawl_conference(
        ...     task, session,
        ...     conference_name="CVPR",
        ...     conference_url="https://www.papercopilot.com/statistics/cvpr-statistics/",
        ...     conference_year=2024
        ... )
    """
    if not conference_name:
        raise ValueError("conference_name is required for conference crawl")
    if not conference_url:
        raise ValueError("conference_url is required for conference crawl")
    if not conference_year:
        raise ValueError("conference_year is required for conference crawl")

    # Validate conference name
    if conference_name.upper() not in ['CVPR', 'ICLR']:
        raise ValueError(f"Unsupported conference: {conference_name}. Only CVPR and ICLR are supported.")

    logger.info(f"Crawling {conference_name} {conference_year} from {conference_url}")

    # Run scraping in thread pool to avoid blocking event loop
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    from ..utils.web_scraper import WebScraper
    from time import sleep

    papers_discovered = 0
    papers_stored = 0

    # Initialize web scraper
    with ThreadPoolExecutor(max_workers=1) as executor:
        loop = asyncio.get_event_loop()

        # Fetch and parse conference page
        task.update_state(
            state='PROCESSING',
            meta={'current': 0, 'total': 0, 'status': f'Loading {conference_name} {conference_year} page...'}
        )

        def scrape_conference_list():
            """Scrape conference paper list in separate thread."""
            scraper = WebScraper(request_timeout=300, headless=True)
            try:
                scraper.open()
                scraper.fetch_url(conference_url)

                # Click "Fetch All" button to load all papers
                button_name = 'btn_fetchall'
                scraper.click_element_by_id(button_name, wait_timeout=30, max_attempts=2, sleep_sec=5)

                # Wait for papers to load
                sleep_sec = 10
                logger.debug(f"Waiting {sleep_sec} seconds for papers to load")
                sleep(sleep_sec)

                # Get page source
                page_source = scraper.current_page_source()
                return page_source
            finally:
                scraper.close()

        # Run scraping in thread pool
        page_source = await loop.run_in_executor(executor, scrape_conference_list)

        # Parse paper list
        raw_paper_data = _parse_conference_papers_list(
            page_source,
            table_id='paperlist',
            conference_name=conference_name.upper()
        )

        papers_discovered = len(raw_paper_data)
        logger.info(f"Found {papers_discovered} papers from {conference_name} {conference_year}")

        task.update_state(
            state='PROCESSING',
            meta={'current': 0, 'total': papers_discovered, 'status': f'Processing {papers_discovered} papers...'}
        )

        # Process each paper
        for i, paper_data in enumerate(raw_paper_data):
            # Update progress
            task.update_state(
                state='PROCESSING',
                meta={
                    'current': i + 1,
                    'total': papers_discovered,
                    'status': f"Processing paper {i + 1}/{papers_discovered}: {paper_data['title'][:50]}..."
                }
            )

            # Skip rejected papers
            if paper_data.get('session_type') and 'rejected' in paper_data['session_type'].lower():
                logger.debug(f"Skipping rejected paper: {paper_data['title']}")
                continue

            # Fetch abstract in separate thread
            conf_url = paper_data.get('conf_url')
            if conf_url:
                def fetch_abstract():
                    return _get_abstract_from_conference_website(conf_url, conference_name.upper())

                abstract = await loop.run_in_executor(executor, fetch_abstract)
                paper_data['abstract'] = abstract

            # Check for duplicates
            existing = None
            if paper_data.get('arxiv_id'):
                result = await session.execute(
                    select(Paper).where(Paper.arxiv_id == paper_data['arxiv_id'])
                )
                existing = result.scalar_one_or_none()

            if not existing and paper_data.get('title'):
                # Check by title similarity
                from rapidfuzz import fuzz
                result = await session.execute(
                    select(Paper).where(Paper.venue.ilike(f"%{conference_name}%"))
                )
                conference_papers = result.scalars().all()
                for existing_paper in conference_papers:
                    similarity = fuzz.ratio(paper_data['title'].lower(), existing_paper.title.lower())
                    if similarity > 95:
                        existing = existing_paper
                        break

            if existing:
                logger.debug(f"Skipping duplicate paper: {paper_data['title']}")
                continue

            # Create paper object
            try:
                paper = _create_paper_from_conference_data(
                    paper_data,
                    conference_name=conference_name.upper(),
                    conference_year=conference_year
                )

                session.add(paper)
                papers_stored += 1
                logger.info(f"Stored conference paper: {paper.title}")

            except Exception as e:
                logger.error(f"Failed to store paper {paper_data.get('title')}: {e}", exc_info=True)
                continue

    logger.info(f"Conference crawl complete. Discovered: {papers_discovered}, Stored: {papers_stored}")
    return papers_discovered, papers_stored


async def _crawl_citations(
    task: Task,
    session: AsyncSession,
    paper_id: Optional[str] = None,
    citation_depth: int = 1,
    year_after: Optional[int] = None,
    keywords: Optional[List[str]] = None,
    crawl_backward: bool = True,
    crawl_forward: bool = True,
    **kwargs
) -> tuple[int, int]:
    """
    Discover papers via citation relationships.

    Implements bidirectional citation crawling:
    - Backward crawling: Extract references from PDF and discover cited papers
    - Forward crawling: Use Semantic Scholar API to discover citing papers

    Args:
        task: Celery task for progress updates
        session: Database session
        paper_id: Starting paper UUID
        citation_depth: How many levels to traverse (default: 1)
        year_after: Only include papers published after this year
        keywords: Filter papers by keywords in title (must match at least half)
        crawl_backward: Crawl references (papers cited by this paper)
        crawl_forward: Crawl citations (papers citing this paper)

    Returns:
        Tuple of (papers_discovered, papers_stored)
    """
    if not paper_id:
        raise ValueError("paper_id is required for citation-based discovery")

    logger.info(f"Discovering papers via citations from: {paper_id}, depth: {citation_depth}")

    # Import services
    # from ..services.pdf_service import PDFAnalysisService
    from ..services.citation_service import CitationMatcher
    from .semanticscholar_client import SemanticScholarClient
    from ..services.arxiv_service import AsyncArxivService
    from uuid import UUID

    # Initialize services
    pdf_service = PDFAnalysisService()
    citation_matcher = CitationMatcher(similarity_threshold=85)
    ss_client = SemanticScholarClient()
    arxiv_service = AsyncArxivService()

    # Get starting paper
    result = await session.execute(
        select(Paper).where(Paper.id == UUID(paper_id))
    )
    starting_paper = result.scalar_one_or_none()

    if not starting_paper:
        raise ValueError(f"Paper not found: {paper_id}")

    # Track discovered and stored papers
    papers_discovered = 0
    papers_stored = 0

    # Track visited papers to avoid cycles
    visited_papers = set()

    # Queue for BFS traversal: (paper, current_depth)
    paper_queue = [(starting_paper, 0)]

    task.update_state(
        state='PROCESSING',
        meta={
            'current': 0,
            'total': 0,
            'status': f'Starting citation discovery from: {starting_paper.title[:50]}...'
        }
    )

    while paper_queue:
        current_paper, current_depth = paper_queue.pop(0)

        # Skip if already visited
        if str(current_paper.id) in visited_papers:
            continue

        visited_papers.add(str(current_paper.id))

        # Skip if depth limit reached
        if current_depth >= citation_depth:
            continue

        logger.info(f"Processing paper at depth {current_depth}: {current_paper.title}")

        # Backward crawling: Extract references from PDF
        if crawl_backward and current_paper.pdf_url:
            backward_papers = await _crawl_backward_references(
                session=session,
                paper=current_paper,
                pdf_service=pdf_service,
                citation_matcher=citation_matcher,
                arxiv_service=arxiv_service,
                ss_client=ss_client,
                year_after=year_after,
                keywords=keywords,
                task=task
            )

            for ref_paper, match_score, ref_text in backward_papers:
                papers_discovered += 1

                # Check if paper already exists
                existing = await _find_existing_paper(session, ref_paper)

                if not existing:
                    # Store new paper
                    session.add(ref_paper)
                    await session.flush()  # Get ID for relationship
                    papers_stored += 1
                    logger.info(f"Stored new reference paper: {ref_paper.title}")

                    # Add to queue for recursive traversal
                    if current_depth + 1 < citation_depth:
                        paper_queue.append((ref_paper, current_depth + 1))
                else:
                    ref_paper = existing
                    logger.debug(f"Reference paper already exists: {ref_paper.title}")

                # Create citation relationship
                await _create_paper_reference(
                    session=session,
                    paper_id=current_paper.id,
                    reference_id=ref_paper.id,
                    reference_text=ref_text,
                    match_score=match_score,
                    match_method='fuzzy_title' if match_score < 100 else 'exact'
                )

        # Forward crawling: Get citing papers from Semantic Scholar
        if crawl_forward:
            forward_papers = await _crawl_forward_citations(
                session=session,
                paper=current_paper,
                ss_client=ss_client,
                arxiv_service=arxiv_service,
                year_after=year_after,
                keywords=keywords,
                task=task
            )

            for citing_paper_data in forward_papers:
                papers_discovered += 1

                # Check if paper already exists
                existing = await _find_existing_paper_by_arxiv(
                    session,
                    citing_paper_data.get('arxiv_id')
                )

                if not existing:
                    # Create paper from Semantic Scholar data
                    citing_paper = _create_paper_from_ss_data(citing_paper_data)
                    session.add(citing_paper)
                    await session.flush()
                    papers_stored += 1
                    logger.info(f"Stored new citing paper: {citing_paper.title}")

                    # Add to queue for recursive traversal
                    if current_depth + 1 < citation_depth:
                        paper_queue.append((citing_paper, current_depth + 1))
                else:
                    citing_paper = existing
                    logger.debug(f"Citing paper already exists: {citing_paper.title}")

                # Create reverse citation relationship
                await _create_paper_reference(
                    session=session,
                    paper_id=citing_paper.id,
                    reference_id=current_paper.id,
                    reference_text=None,
                    match_score=100.0,
                    match_method='semantic_scholar_api'
                )

        task.update_state(
            state='PROCESSING',
            meta={
                'current': papers_discovered,
                'total': papers_discovered,
                'status': f'Processed {len(visited_papers)} papers, discovered {papers_discovered}'
            }
        )

    # Cleanup
    await ss_client.close()

    logger.info(
        f"Citation crawl complete. Discovered: {papers_discovered}, "
        f"Stored: {papers_stored}, Visited: {len(visited_papers)}"
    )

    return papers_discovered, papers_stored


# ============================================================================
# CITATION CRAWLING HELPER FUNCTIONS
# ============================================================================


async def _crawl_backward_references(
    session: AsyncSession,
    paper: Paper,
    pdf_service,
    citation_matcher,
    arxiv_service,
    ss_client,
    year_after: Optional[int],
    keywords: Optional[List[str]],
    task: Task
) -> List[tuple]:
    """
    Crawl backward through references (papers cited by this paper).

    Extracts references from PDF, parses them, and matches to papers.

    Returns:
        List of tuples: (paper_object, match_score, reference_text)
    """
    from pathlib import Path
    import tempfile
    import httpx

    discovered_references = []

    try:
        # Download PDF if needed
        pdf_path = None
        if paper.pdf_url:
            logger.info(f"Downloading PDF for reference extraction: {paper.title}")

            # Download to temp file
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(paper.pdf_url)
                response.raise_for_status()

                # Save to temp file
                temp_dir = Path(tempfile.gettempdir()) / "hypepaper_pdfs"
                temp_dir.mkdir(exist_ok=True)
                pdf_path = temp_dir / f"{paper.id}.pdf"

                with open(pdf_path, 'wb') as f:
                    f.write(response.content)

            # Extract references from PDF
            logger.info(f"Extracting references from PDF: {paper.title}")
            reference_texts = await pdf_service.extract_references(pdf_path)

            if not reference_texts:
                logger.warning(f"No references found in PDF for: {paper.title}")
                return discovered_references

            logger.info(f"Found {len(reference_texts)} references in PDF")

            # Get all papers from database for matching
            result = await session.execute(select(Paper))
            all_papers = result.scalars().all()

            # Parse and match each reference
            for i, ref_text in enumerate(reference_texts):
                if not ref_text or len(ref_text) < 10:
                    continue

                task.update_state(
                    state='PROCESSING',
                    meta={
                        'status': f'Matching reference {i+1}/{len(reference_texts)}: {ref_text[:50]}...'
                    }
                )

                # Parse citation to extract structured data
                parsed = await citation_matcher.parse_citation(ref_text)

                if not parsed or 'title' not in parsed:
                    logger.debug(f"Failed to parse reference: {ref_text[:50]}...")
                    continue

                # Apply year filter
                ref_year = parsed.get('year')
                if year_after and ref_year and ref_year < year_after:
                    logger.debug(f"Skipping reference (year {ref_year} < {year_after}): {parsed['title']}")
                    continue

                # Apply keyword filter
                if keywords:
                    title_lower = parsed['title'].lower()
                    matched_keywords = [kw for kw in keywords if kw.lower() in title_lower]
                    if len(matched_keywords) < len(keywords) / 2:
                        logger.debug(f"Skipping reference (insufficient keywords): {parsed['title']}")
                        continue

                # Try to match to existing paper in database
                matched_paper = await citation_matcher.match_citation(ref_text, all_papers)

                if matched_paper:
                    # Found existing paper
                    match_score = citation_matcher.calculate_match_quality(
                        ref_text, matched_paper.title, matched_paper.year
                    )
                    logger.info(f"Matched reference to existing paper (score {match_score}): {matched_paper.title}")
                    discovered_references.append((matched_paper, match_score, ref_text))

                else:
                    # Search for paper on ArXiv
                    logger.info(f"Searching ArXiv for reference: {parsed['title']}")
                    arxiv_results = await arxiv_service.search_by_title(parsed['title'])

                    if arxiv_results and len(arxiv_results) > 0:
                        # Create paper from ArXiv data
                        arxiv_data = arxiv_results[0]
                        ref_paper = Paper(
                            arxiv_id=arxiv_data.get('arxiv_id'),
                            doi=arxiv_data.get('doi'),
                            title=arxiv_data['title'],
                            authors=arxiv_data.get('authors', []),
                            abstract=arxiv_data.get('abstract', ''),
                            published_date=datetime.fromisoformat(arxiv_data['published_date']).date() if arxiv_data.get('published_date') else datetime.utcnow().date(),
                            venue=arxiv_data.get('journal_ref'),
                            arxiv_url=arxiv_data.get('url'),
                            pdf_url=arxiv_data.get('pdf_url'),
                            year=arxiv_data.get('year')
                        )

                        match_score = citation_matcher.calculate_match_quality(
                            ref_text, ref_paper.title, ref_paper.year
                        )
                        logger.info(f"Found reference on ArXiv: {ref_paper.title}")
                        discovered_references.append((ref_paper, match_score, ref_text))

                    else:
                        logger.debug(f"Reference not found on ArXiv: {parsed['title']}")

    except Exception as e:
        logger.error(f"Error crawling backward references for {paper.title}: {e}", exc_info=True)

    finally:
        # Cleanup temp PDF
        if pdf_path and pdf_path.exists():
            try:
                pdf_path.unlink()
            except:
                pass

    return discovered_references


async def _crawl_forward_citations(
    session: AsyncSession,
    paper: Paper,
    ss_client,
    arxiv_service,
    year_after: Optional[int],
    keywords: Optional[List[str]],
    task: Task
) -> List[dict]:
    """
    Crawl forward through citing papers (papers that cite this paper).

    Uses Semantic Scholar API to fetch citing papers.

    Returns:
        List of paper data dictionaries
    """
    discovered_citations = []

    try:
        # Get paper from Semantic Scholar
        logger.info(f"Fetching citing papers from Semantic Scholar for: {paper.title}")

        ss_paper = None
        if paper.arxiv_id:
            ss_paper = await ss_client.get_paper_by_arxiv(paper.arxiv_id)
        elif paper.doi:
            ss_paper = await ss_client.get_paper_by_doi(paper.doi)

        if not ss_paper:
            logger.warning(f"Paper not found on Semantic Scholar: {paper.title}")
            return discovered_citations

        # Get paper ID from Semantic Scholar
        paper_id = ss_paper.get('paperId')
        if not paper_id:
            logger.warning(f"No paperId in Semantic Scholar response for: {paper.title}")
            return discovered_citations

        # Fetch citing papers with references field
        # Note: Semantic Scholar API requires fields parameter
        url = f"{ss_client.BASE_URL}/paper/{paper_id}/citations"
        params = {
            "fields": "title,year,abstract,authors,externalIds,citationCount,venue,openAccessPdf",
            "limit": 100  # Max per request
        }

        await ss_client._rate_limit()
        response = await ss_client.client.get(url, params=params)

        if response.status_code != 200:
            logger.warning(f"Failed to fetch citations from Semantic Scholar: {response.status_code}")
            return discovered_citations

        data = response.json()
        citations = data.get('data', [])

        logger.info(f"Found {len(citations)} citing papers on Semantic Scholar")

        for citation in citations:
            citing_paper_data = citation.get('citingPaper', {})

            if not citing_paper_data or 'title' not in citing_paper_data:
                continue

            # Apply year filter
            citing_year = citing_paper_data.get('year')
            if year_after and citing_year and citing_year < year_after:
                logger.debug(f"Skipping citing paper (year {citing_year} < {year_after}): {citing_paper_data['title']}")
                continue

            # Apply keyword filter
            if keywords:
                title_lower = citing_paper_data['title'].lower()
                matched_keywords = [kw for kw in keywords if kw.lower() in title_lower]
                if len(matched_keywords) < len(keywords) / 2:
                    logger.debug(f"Skipping citing paper (insufficient keywords): {citing_paper_data['title']}")
                    continue

            # Extract ArXiv ID if available
            external_ids = citing_paper_data.get('externalIds', {})
            arxiv_id = external_ids.get('ArXiv')
            doi = external_ids.get('DOI')

            # Extract PDF URL
            pdf_url = None
            open_access_pdf = citing_paper_data.get('openAccessPdf')
            if open_access_pdf:
                pdf_url = open_access_pdf.get('url')

            # Extract authors
            authors = []
            for author in citing_paper_data.get('authors', []):
                if 'name' in author:
                    authors.append(author['name'])

            discovered_citations.append({
                'title': citing_paper_data['title'],
                'arxiv_id': arxiv_id,
                'doi': doi,
                'authors': authors,
                'abstract': citing_paper_data.get('abstract', ''),
                'year': citing_year,
                'venue': citing_paper_data.get('venue'),
                'pdf_url': pdf_url,
                'citation_count': citing_paper_data.get('citationCount', 0)
            })

    except Exception as e:
        logger.error(f"Error crawling forward citations for {paper.title}: {e}", exc_info=True)

    return discovered_citations


async def _find_existing_paper(session: AsyncSession, paper: Paper) -> Optional[Paper]:
    """Find existing paper in database by arxiv_id, doi, or title."""
    # Try arxiv_id
    if paper.arxiv_id:
        result = await session.execute(
            select(Paper).where(Paper.arxiv_id == paper.arxiv_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    # Try DOI
    if paper.doi:
        result = await session.execute(
            select(Paper).where(Paper.doi == paper.doi)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    # Try fuzzy title match (normalized comparison)
    # This is expensive, so only use as fallback
    # For production, consider using full-text search or embedding similarity
    result = await session.execute(
        select(Paper).where(Paper.title.ilike(f"%{paper.title}%"))
    )
    candidates = result.scalars().all()

    if candidates:
        # Use Levenshtein distance for best match
        from rapidfuzz import fuzz
        best_match = None
        best_score = 0

        for candidate in candidates:
            score = fuzz.ratio(paper.title.lower(), candidate.title.lower())
            if score > best_score and score >= 90:  # High threshold for title match
                best_score = score
                best_match = candidate

        return best_match

    return None


async def _find_existing_paper_by_arxiv(
    session: AsyncSession,
    arxiv_id: Optional[str]
) -> Optional[Paper]:
    """Find existing paper by arxiv_id."""
    if not arxiv_id:
        return None

    result = await session.execute(
        select(Paper).where(Paper.arxiv_id == arxiv_id)
    )
    return result.scalar_one_or_none()


def _create_paper_from_ss_data(data: dict) -> Paper:
    """Create Paper object from Semantic Scholar data."""
    return Paper(
        arxiv_id=data.get('arxiv_id'),
        doi=data.get('doi'),
        title=data['title'],
        authors=data.get('authors', []),
        abstract=data.get('abstract', ''),
        published_date=datetime(data['year'], 1, 1).date() if data.get('year') else datetime.utcnow().date(),
        venue=data.get('venue'),
        pdf_url=data.get('pdf_url'),
        year=data.get('year')
    )


async def _create_paper_reference(
    session: AsyncSession,
    paper_id,
    reference_id,
    reference_text: Optional[str],
    match_score: float,
    match_method: str
):
    """Create PaperReference relationship if it doesn't exist."""
    from ..models.paper_reference import PaperReference

    # Check if relationship already exists
    result = await session.execute(
        select(PaperReference).where(
            PaperReference.paper_id == paper_id,
            PaperReference.reference_id == reference_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        logger.debug(f"Citation relationship already exists: {paper_id} -> {reference_id}")
        return

    # Create new relationship
    reference = PaperReference(
        paper_id=paper_id,
        reference_id=reference_id,
        reference_text=reference_text,
        match_score=match_score,
        match_method=match_method
    )

    session.add(reference)
    logger.debug(f"Created citation relationship: {paper_id} -> {reference_id} (score: {match_score})")


# ============================================================================
# CONFERENCE CRAWLING HELPER FUNCTIONS
# ============================================================================


def _parse_conference_papers_list(
    html: str,
    table_id: str,
    conference_name: str
) -> List[Dict[str, Any]]:
    """
    Parse conference papers from PaperCopilot HTML table.

    Args:
        html: HTML page source
        table_id: ID of the table element
        conference_name: Conference name (CVPR or ICLR)

    Returns:
        List of paper data dictionaries
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', {'id': table_id})

    if not table:
        logger.error(f"Table with ID '{table_id}' not found in HTML")
        return []

    # Get table headers
    header_tr = table.find('thead').find_all('tr')[1]
    header_th = header_tr.find_all('th')
    headers = [header.get_text(strip=True) for header in header_th]

    logger.debug(f"Table headers: {headers}")

    # Get table rows
    rows = table.find('tbody').find_all('tr')

    # Link text patterns
    pdf_link_text = 'PDF'
    youtube_link_text = 'Youtube'
    github_link_text = 'Github'
    project_page_link_text = 'Project Page'
    arxiv_link_text = 'Arxiv'

    if conference_name == 'CVPR':
        conf_url_text = 'CVF'
    elif conference_name == 'ICLR':
        conf_url_text = 'OR'
    else:
        raise ValueError(f'Invalid conference name: {conference_name}')

    papers_data = []

    for row in rows:
        tds = row.find_all('td')

        if len(tds) < 9:
            continue

        # Extract basic info
        title_col = tds[2]
        authors_col = tds[4]
        affiliations_col = tds[5]
        affiliations_country_col = tds[6]
        status_col = tds[7]
        citations_col = tds[8]

        title_a = title_col.find('a')
        if not title_a:
            continue

        title = title_a.text.strip()
        url = title_a['href']

        authors_list = authors_col.get('data-val', '').split(';') if authors_col.get('data-val') else []
        affiliations_list = affiliations_col.get('data-val', '').split(';') if affiliations_col.get('data-val') else []
        affiliations_country_list = affiliations_country_col.get('data-val', '').split(';') if affiliations_country_col.get('data-val') else []
        session_type = status_col.get('data-val', '')
        citations_str = citations_col.get('data-val', '0')
        citations = int(citations_str) if citations_str and citations_str.isdigit() else 0

        # Extract social links
        pdf_url = None
        youtube_url = None
        github_url = None
        project_page_url = None
        arxiv_url = None
        conf_url = None

        social_links_span = title_col.find('span')
        if social_links_span:
            social_links_ul = social_links_span.find('ul')
            if social_links_ul:
                social_links_lis = social_links_ul.find_all('li')

                for social_links_li in social_links_lis:
                    social_link_a = social_links_li.find('a')
                    if not social_link_a:
                        continue

                    social_link_a_href = social_link_a.get('href', '')
                    social_link_a_title = social_link_a.get('title', '')

                    if social_link_a_title == pdf_link_text:
                        pdf_url = social_link_a_href
                    elif social_link_a_title == youtube_link_text:
                        youtube_url = social_link_a_href
                    elif social_link_a_title == github_link_text:
                        github_url = social_link_a_href
                    elif social_link_a_title == project_page_link_text:
                        project_page_url = social_link_a_href
                    elif social_link_a_title == arxiv_link_text:
                        arxiv_url = social_link_a_href
                    elif social_link_a_title == conf_url_text:
                        conf_url = social_link_a_href

        if conf_url is None:
            conf_url = url

        # Extract arxiv_id from arxiv_url
        arxiv_id = None
        if arxiv_url:
            arxiv_id = arxiv_url.split('/')[-1] if '/' in arxiv_url else None

        paper_data = {
            'title': title,
            'url': url,
            'conf_url': conf_url,
            'authors': authors_list,
            'affiliations': affiliations_list,
            'affiliations_country': affiliations_country_list,
            'session_type': session_type,
            'citations': citations,
            'pdf_url': pdf_url,
            'youtube_url': youtube_url,
            'github_url': github_url,
            'project_page_url': project_page_url,
            'arxiv_url': arxiv_url,
            'arxiv_id': arxiv_id,
        }

        papers_data.append(paper_data)

    logger.info(f"Parsed {len(papers_data)} papers from table")
    return papers_data


def _get_abstract_from_conference_website(url: str, conference_name: str) -> Optional[str]:
    """
    Extract abstract from conference paper webpage.

    Args:
        url: Conference paper URL
        conference_name: Conference name (CVPR or ICLR)

    Returns:
        Abstract text or None if not found
    """
    from ..utils.web_scraper import WebScraper

    scraper = WebScraper(request_timeout=60, headless=True)
    abstract = None

    try:
        scraper.open()
        scraper.fetch_url(url)

        if 'openaccess.thecvf.com' in url:
            element = scraper.find_element_by_id('abstract')
            if element:
                abstract = element.text
        elif 'cvpr.thecvf.com' in url:
            element = scraper.find_element_by_id('abstractExample')
            if element:
                abstract = element.text
        elif 'iclr.cc' in url:
            scraper.click_element_by_classname('card-link')
            elements = scraper.find_element('div', {'id': 'abstractExample'})
            if len(elements) > 0:
                abstract_p = elements[0].find('p')
                if abstract_p:
                    abstract = abstract_p.text
                else:
                    abstract = elements[0].text.replace('Abstract:', '').strip()
        elif 'openreview.net' in url:
            elements = scraper.find_element('div', {'class': 'note-content-value markdown-rendered'})
            if len(elements) > 0:
                abstract_p = elements[0].find('p')
                if abstract_p:
                    abstract = abstract_p.text
                else:
                    abstract = elements[0].text.replace('Abstract:', '').strip()

        if abstract is None:
            logger.warning(f"Failed to get abstract from {url}")

    except Exception as e:
        logger.error(f"Error fetching abstract from {url}: {e}")
    finally:
        scraper.close()

    return abstract


def _create_paper_from_conference_data(
    paper_data: Dict[str, Any],
    conference_name: str,
    conference_year: int
) -> Paper:
    """
    Create Paper model instance from conference data.

    Args:
        paper_data: Paper data dictionary
        conference_name: Conference name
        conference_year: Conference year

    Returns:
        Paper model instance
    """
    from datetime import date

    # Map session type
    session_type = paper_data.get('session_type', '')
    paper_type = None
    accept_status = None

    if session_type in ['Highlight', 'Spotlight']:
        paper_type = 'oral'
        accept_status = 'accepted'
    elif session_type == 'Oral':
        paper_type = 'oral'
        accept_status = 'accepted'
    elif session_type == 'Poster':
        paper_type = 'poster'
        accept_status = 'accepted'
    elif session_type == 'Award Candidate':
        accept_status = 'accepted'
    elif session_type == 'Best Paper':
        accept_status = 'accepted'

    # Create affiliations dict
    affiliations_dict = {}
    affiliations_country_dict = {}

    authors = paper_data.get('authors', [])
    affiliations_list = paper_data.get('affiliations', [])
    affiliations_country_list = paper_data.get('affiliations_country', [])

    for i, author in enumerate(authors):
        if i < len(affiliations_list):
            affiliations_dict[author] = [affiliations_list[i]]
        if i < len(affiliations_country_list):
            affiliations_country_dict[author] = [affiliations_country_list[i]]

    # Create paper
    paper = Paper(
        arxiv_id=paper_data.get('arxiv_id'),
        title=paper_data['title'],
        authors=authors if authors else ['Unknown'],
        abstract=paper_data.get('abstract', ''),
        published_date=date(conference_year, 1, 1),
        venue=f"{conference_name} {conference_year}",
        year=conference_year,
        arxiv_url=paper_data.get('arxiv_url'),
        pdf_url=paper_data.get('pdf_url'),
        github_url=paper_data.get('github_url'),
        youtube_url=paper_data.get('youtube_url'),
        project_page_url=paper_data.get('project_page_url'),
        paper_type=paper_type,
        session_type=session_type,
        accept_status=accept_status,
        affiliations=affiliations_dict if affiliations_dict else None,
        affiliations_country=affiliations_country_dict if affiliations_country_dict else None,
    )

    return paper
