"""Background reference crawler for citation network extraction.

Crawls papers and recursively extracts references to build citation networks.
Now uses database-backed job tracking for persistence across restarts.
"""
import asyncio
import tempfile
import uuid
from datetime import datetime as dt, timedelta
from pathlib import Path
from typing import Optional, List

import aiohttp
import fitz

from ..database import AsyncSessionLocal
from ..models import Paper, PaperReference, CrawlerJob, CitationSnapshot
from ..services import AsyncArxivService
from ..services.citation_service import CitationMatcher
from ..services.paper_enrichment import PaperEnrichmentService
from sqlalchemy import select
from datetime import date as dt_date


def _calculate_next_run(period: Optional[str]) -> Optional[dt]:
    """Calculate next run time based on period."""
    if not period:
        return None

    now = dt.utcnow()
    if period == "daily":
        next_run = now + timedelta(days=1)
    elif period == "weekly":
        next_run = now + timedelta(weeks=1)
    elif period == "monthly":
        next_run = now + timedelta(days=30)
    else:
        return None

    return next_run


async def _log(db, job_id: str, message: str, level: str = "INFO"):
    """Add log entry to database for a job."""
    result = await db.execute(
        select(CrawlerJob).where(CrawlerJob.job_id == job_id)
    )
    job = result.scalar_one_or_none()

    if job:
        # Append log to JSONB array
        logs = job.logs or []
        logs.append({
            "timestamp": dt.utcnow().isoformat(),
            "level": level,
            "message": message
        })
        job.logs = logs
        await db.commit()

    print(f"[{job_id}] {message}")


async def get_active_jobs() -> List[dict]:
    """Get list of active crawler jobs from database."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CrawlerJob).where(CrawlerJob.status == "processing")
        )
        jobs = result.scalars().all()

        return [{
            "job_id": job.job_id,
            "status": job.status,
            "started_at": job.started_at.isoformat(),
            "papers_crawled": job.papers_crawled,
            "reference_depth": job.reference_depth,
            "source_type": job.source_type,
            "keywords": job.keywords,
            "period": job.period,
            "next_run": job.next_run.isoformat() if job.next_run else None,
        } for job in jobs]


async def get_job_logs(job_id: str) -> List[dict]:
    """Get logs for a specific job from database."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CrawlerJob).where(CrawlerJob.job_id == job_id)
        )
        job = result.scalar_one_or_none()
        return job.logs if job else []


async def crawl_references_background(
    job_id: str,
    arxiv_keywords: Optional[str],
    arxiv_max_results: int,
    reference_depth: int,
    period: Optional[str] = None
):
    """
    Background task to crawl papers and extract references recursively.

    Args:
        job_id: Unique job identifier
        arxiv_keywords: Keywords to search arXiv
        arxiv_max_results: Maximum papers to crawl initially
        reference_depth: How deep to crawl references (1-3)
        period: Crawling period (daily, weekly, monthly) for periodic updates
    """
    try:
        async with AsyncSessionLocal() as db:
            # Initialize job tracking in database
            crawler_job = CrawlerJob(
                job_id=job_id,
                status="processing",
                started_at=dt.utcnow(),
                source_type="arxiv",
                keywords=arxiv_keywords,
                reference_depth=reference_depth,
                period=period,
                next_run=_calculate_next_run(period),
                papers_crawled=0,
                references_crawled=0,
                logs=[]
            )
            db.add(crawler_job)
            await db.commit()

            arxiv_service = AsyncArxivService()
            citation_matcher = CitationMatcher()
            enrichment_service = PaperEnrichmentService()

            await _log(db, job_id, f"Starting reference crawl: keywords='{arxiv_keywords}', max={arxiv_max_results}, depth={reference_depth}")

            # Search arXiv for initial papers
            papers_data = await arxiv_service.search_by_keywords(
                keywords=arxiv_keywords,
                max_results=arxiv_max_results
            )

            await _log(db, job_id, f"Found {len(papers_data)} papers from arXiv")

            # Store initial papers
            stored_papers = []
            crawled_titles = set()

            for paper_data in papers_data:
                # Check if already exists
                existing_result = await db.execute(
                    select(Paper).where(Paper.arxiv_id == paper_data.get("arxiv_id"))
                )
                existing_paper = existing_result.scalar_one_or_none()

                if existing_paper:
                    # For periodic jobs, add existing papers to be tracked and crawl their references
                    if period:
                        await _log(db, job_id, f"Paper exists, will crawl references and update metrics: {existing_paper.title[:50]}")
                        stored_papers.append({
                            "id": str(existing_paper.id),
                            "title": existing_paper.title,
                            "pdf_url": existing_paper.pdf_url
                        })
                        crawled_titles.add(citation_matcher.normalize_title(existing_paper.title))
                        continue
                    else:
                        await _log(db, job_id, f"Paper already exists, skipping: {paper_data.get('title')[:50]}")
                        continue

                # Convert date
                pub_date = paper_data.get("published_date")
                if isinstance(pub_date, str):
                    pub_date = dt.fromisoformat(pub_date.replace('Z', '+00:00')).date()
                elif isinstance(pub_date, dt):
                    pub_date = pub_date.date()

                # Extract venue (use journal_ref if available, otherwise primary_category)
                venue = paper_data.get("journal_ref")
                if not venue and paper_data.get("primary_category"):
                    venue = paper_data.get("primary_category")

                # Create paper
                paper = Paper(
                    id=uuid.uuid4(),
                    arxiv_id=paper_data.get("arxiv_id"),
                    title=paper_data.get("title"),
                    authors=paper_data.get("authors", []),
                    abstract=paper_data.get("abstract", ""),
                    published_date=pub_date,
                    venue=venue,
                    pdf_url=paper_data.get("pdf_url"),
                    arxiv_url=paper_data.get("arxiv_url"),
                )
                db.add(paper)
                await db.flush()

                # Enrich paper with GitHub URL, project page, YouTube, citations
                try:
                    await enrichment_service.enrich_paper(paper)

                    # Create citation snapshot if citation count was found
                    if paper.citation_count and paper.citation_count > 0:
                        snapshot = CitationSnapshot(
                            paper_id=paper.id,
                            citation_count=paper.citation_count,
                            snapshot_date=dt_date.today(),
                            source="google_scholar"
                        )
                        db.add(snapshot)

                    await db.flush()
                except Exception as e:
                    await _log(db, job_id, f"Enrichment failed for {paper.title[:30]}: {e}", "WARNING")

                stored_papers.append({
                    "id": str(paper.id),
                    "title": paper.title,
                    "pdf_url": paper.pdf_url
                })
                crawled_titles.add(citation_matcher.normalize_title(paper.title))

                await _log(db, job_id, f"Stored new paper: {paper.title[:50]}")

            await db.commit()

            # Update job progress
            crawler_job.papers_crawled = len(stored_papers)
            await db.commit()

            # Now crawl references recursively
            references_crawled = 0
            papers_to_crawl = [(p, 1) for p in stored_papers]  # (paper_dict, current_depth)

            while papers_to_crawl:
                current_paper, current_depth = papers_to_crawl.pop(0)

                if current_depth > reference_depth:
                    continue

                print(f"[{job_id}] Processing references for: {current_paper['title'][:50]} (depth {current_depth})")

                # Get paper from database
                paper_result = await db.execute(
                    select(Paper).where(Paper.id == uuid.UUID(current_paper["id"]))
                )
                paper = paper_result.scalar_one_or_none()
                if not paper or not paper.pdf_url:
                    print(f"[{job_id}] Skipping - no PDF URL")
                    continue

                try:
                    # Download PDF
                    async with aiohttp.ClientSession() as session:
                        async with session.get(paper.pdf_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                            if resp.status != 200:
                                print(f"[{job_id}] Failed to download PDF: {resp.status}")
                                continue

                            pdf_content = await resp.read()

                            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                                tmp.write(pdf_content)
                                pdf_path = Path(tmp.name)

                    # Extract references from PDF
                    doc = fitz.open(pdf_path)
                    references_text = ""
                    found_references = False

                    for page_num in range(doc.page_count):
                        page = doc[page_num]
                        text = page.get_text("text")

                        if not found_references:
                            if "References" in text or "REFERENCES" in text:
                                found_references = True
                                remaining = text.split("References", 1)[-1]
                                references_text += remaining.strip()
                        else:
                            references_text += "\n" + text

                    doc.close()
                    pdf_path.unlink()

                    if not references_text:
                        print(f"[{job_id}] No references section found")
                        continue

                    # Parse references (limit to first 20)
                    citation_lines = [line.strip() for line in references_text.split('\n') if line.strip()]
                    ref_count = 0

                    for citation_text in citation_lines[:20]:
                        if len(citation_text) < 20:
                            continue

                        # Parse citation
                        parsed = await citation_matcher.parse_citation(citation_text)
                        if not parsed or 'title' not in parsed:
                            continue

                        ref_title = parsed['title']
                        normalized_title = citation_matcher.normalize_title(ref_title)

                        # Skip if already crawled
                        if normalized_title in crawled_titles:
                            continue

                        # Search arXiv for this reference
                        try:
                            ref_papers = await arxiv_service.search_by_keywords(
                                keywords=ref_title,
                                max_results=1
                            )

                            if not ref_papers:
                                continue

                            ref_paper_data = ref_papers[0]
                            ref_arxiv_id = ref_paper_data.get("arxiv_id")

                            # Check if exists
                            existing_ref = await db.execute(
                                select(Paper).where(Paper.arxiv_id == ref_arxiv_id)
                            )
                            ref_paper = existing_ref.scalar_one_or_none()

                            if not ref_paper:
                                # Create new paper
                                ref_pub_date = ref_paper_data.get("published_date")
                                if isinstance(ref_pub_date, str):
                                    ref_pub_date = dt.fromisoformat(ref_pub_date.replace('Z', '+00:00')).date()
                                elif isinstance(ref_pub_date, dt):
                                    ref_pub_date = ref_pub_date.date()

                                # Extract venue
                                ref_venue = ref_paper_data.get("journal_ref")
                                if not ref_venue and ref_paper_data.get("primary_category"):
                                    ref_venue = ref_paper_data.get("primary_category")

                                ref_paper = Paper(
                                    id=uuid.uuid4(),
                                    arxiv_id=ref_paper_data.get("arxiv_id"),
                                    title=ref_paper_data.get("title"),
                                    authors=ref_paper_data.get("authors", []),
                                    abstract=ref_paper_data.get("abstract", ""),
                                    published_date=ref_pub_date,
                                    venue=ref_venue,
                                    pdf_url=ref_paper_data.get("pdf_url"),
                                    arxiv_url=ref_paper_data.get("arxiv_url"),
                                )
                                db.add(ref_paper)
                                await db.flush()

                                # Enrich referenced paper
                                try:
                                    await enrichment_service.enrich_paper(ref_paper)
                                    if ref_paper.citation_count and ref_paper.citation_count > 0:
                                        snapshot = CitationSnapshot(
                                            paper_id=ref_paper.id,
                                            citation_count=ref_paper.citation_count,
                                            snapshot_date=dt_date.today(),
                                            source="google_scholar"
                                        )
                                        db.add(snapshot)
                                    await db.flush()
                                except Exception:
                                    pass  # Silent fail for references

                                crawled_titles.add(normalized_title)
                                references_crawled += 1
                                ref_count += 1

                                print(f"[{job_id}] Found reference: {ref_paper.title[:50]}")

                                # Queue for next depth
                                if current_depth < reference_depth:
                                    papers_to_crawl.append(({
                                        "id": str(ref_paper.id),
                                        "title": ref_paper.title,
                                        "pdf_url": ref_paper.pdf_url
                                    }, current_depth + 1))

                            # Create citation relationship
                            existing_citation = await db.execute(
                                select(PaperReference).where(
                                    PaperReference.paper_id == paper.id,
                                    PaperReference.reference_id == ref_paper.id
                                )
                            )
                            if not existing_citation.scalar_one_or_none():
                                citation = PaperReference(
                                    paper_id=paper.id,
                                    reference_id=ref_paper.id,
                                    reference_text=citation_text[:500],  # Limit length
                                    match_method='fuzzy_arxiv_search'
                                )
                                db.add(citation)

                        except Exception as e:
                            print(f"[{job_id}] Error crawling reference: {e}")
                            continue

                    await db.commit()
                    await _log(db, job_id, f"Processed {ref_count} new references from this paper")

                    # Update job progress
                    crawler_job.papers_crawled = len(stored_papers)
                    crawler_job.references_crawled = references_crawled
                    await db.commit()

                except Exception as e:
                    await _log(db, job_id, f"Error extracting references: {e}", "ERROR")
                    continue

            await _log(db, job_id, f"Completed! Initial papers: {len(stored_papers)}, References crawled: {references_crawled}")

            # Mark job as completed
            crawler_job.status = "completed"
            crawler_job.papers_crawled = len(stored_papers)
            crawler_job.references_crawled = references_crawled
            crawler_job.completed_at = dt.utcnow()
            await db.commit()

    except Exception as e:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(CrawlerJob).where(CrawlerJob.job_id == job_id)
            )
            job = result.scalar_one_or_none()
            if job:
                await _log(db, job_id, f"Fatal error: {str(e)}", "ERROR")
                job.status = "failed"
                job.completed_at = dt.utcnow()
                await db.commit()
        print(f"[{job_id}] Fatal error: {str(e)}")
