"""Paper enrichment service.

Enriches papers with additional metadata:
- GitHub repository URLs (using smart detection)
- Project website URLs
- YouTube video URLs
- Citation counts
- GitHub stars (scraped from repo pages)
"""
import asyncio
from typing import Optional
from ..models import Paper
from .url_extractor import URLExtractor
from .github_search import GitHubSearchService
from .smart_github_detector import SmartGitHubDetector
from .citation_counter import CitationCounter
from .github_scraper import GitHubScraper


class PaperEnrichmentService:
    """Enrich papers with GitHub URLs, project URLs, citations, etc."""

    def __init__(self):
        """Initialize enrichment service with all extractors."""
        self.url_extractor = URLExtractor()
        self.github_search = GitHubSearchService()  # Fallback for old method
        self.citation_counter = CitationCounter()

    async def enrich_paper(self, paper: Paper) -> Paper:
        """
        Enrich a paper with all available metadata.

        Args:
            paper: Paper object to enrich

        Returns:
            Enriched paper object (modified in place)
        """
        # Extract URLs from abstract using legacy extractor for non-GitHub URLs
        if paper.abstract:
            urls = self.url_extractor.extract_urls_from_abstract(paper.abstract)

            # Set project page URL if found
            if urls['project_page_url'] and not paper.project_page_url:
                paper.project_page_url = urls['project_page_url']

            # Set YouTube URL if found
            if urls['youtube_url'] and not paper.youtube_url:
                paper.youtube_url = self.url_extractor.normalize_youtube_url(urls['youtube_url'])

        # Use smart GitHub detection for better accuracy
        if not paper.github_url:
            try:
                async with SmartGitHubDetector() as smart_detector:
                    github_url = await smart_detector.detect_github_url(
                        paper.title,
                        paper.abstract or "",
                        paper.arxiv_id
                    )
                    if github_url:
                        paper.github_url = github_url
                        print(f"[ENRICHMENT] Smart detector found GitHub URL: {github_url}")
            except Exception as e:
                print(f"[ENRICHMENT] Smart GitHub detection failed: {e}")

                # Fallback to old method
                github_url = await self.github_search.search_repository(paper.title)
                if not github_url and paper.arxiv_id:
                    github_url = await self.github_search.search_by_arxiv_id(paper.arxiv_id)

                if github_url:
                    paper.github_url = github_url
                    print(f"[ENRICHMENT] Fallback search found GitHub URL: {github_url}")

        # Get citation count
        if paper.citation_count is None or paper.citation_count == 0:
            citation_count = await self.citation_counter.get_citation_count(paper.title)
            if citation_count is not None:
                paper.citation_count = citation_count

        # Scrape GitHub stars if GitHub URL is available
        if paper.github_url and not paper.github_stars_scraped:
            try:
                async with GitHubScraper() as scraper:
                    github_data = await scraper.scrape_github_stars(paper.github_url)
                    if github_data and github_data.get('stars') is not None:
                        paper.github_stars_scraped = github_data['stars']
                        print(f"[ENRICHMENT] Scraped {github_data['stars']} stars for {paper.github_url}")
            except Exception as e:
                print(f"[ENRICHMENT] Failed to scrape GitHub stars for {paper.github_url}: {e}")

        return paper

    async def enrich_papers_batch(self, papers: list[Paper], max_concurrent: int = 5) -> list[Paper]:
        """
        Enrich multiple papers concurrently with rate limiting.

        Args:
            papers: List of papers to enrich
            max_concurrent: Maximum concurrent enrichment operations

        Returns:
            List of enriched papers
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def enrich_with_semaphore(paper):
            async with semaphore:
                return await self.enrich_paper(paper)

        tasks = [enrich_with_semaphore(paper) for paper in papers]
        return await asyncio.gather(*tasks, return_exceptions=True)
