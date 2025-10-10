"""Paper enrichment service.

Enriches papers with additional metadata:
- GitHub repository URLs
- Project website URLs
- YouTube video URLs
- Citation counts
"""
import asyncio
from typing import Optional
from ..models import Paper
from .url_extractor import URLExtractor
from .github_search import GitHubSearchService
from .citation_counter import CitationCounter


class PaperEnrichmentService:
    """Enrich papers with GitHub URLs, project URLs, citations, etc."""

    def __init__(self):
        """Initialize enrichment service with all extractors."""
        self.url_extractor = URLExtractor()
        self.github_search = GitHubSearchService()
        self.citation_counter = CitationCounter()

    async def enrich_paper(self, paper: Paper) -> Paper:
        """
        Enrich a paper with all available metadata.

        Args:
            paper: Paper object to enrich

        Returns:
            Enriched paper object (modified in place)
        """
        # Extract URLs from abstract
        if paper.abstract:
            urls = self.url_extractor.extract_urls_from_abstract(paper.abstract)

            # Set GitHub URL if found in abstract
            if urls['github_url'] and not paper.github_url:
                paper.github_url = self.url_extractor.normalize_github_url(urls['github_url'])

            # Set project page URL if found
            if urls['project_page_url'] and not paper.project_page_url:
                paper.project_page_url = urls['project_page_url']

            # Set YouTube URL if found
            if urls['youtube_url'] and not paper.youtube_url:
                paper.youtube_url = self.url_extractor.normalize_youtube_url(urls['youtube_url'])

        # Search for GitHub repository if not found in abstract
        if not paper.github_url:
            # Try searching by title first
            github_url = await self.github_search.search_repository(paper.title)

            # If not found by title, try arXiv ID
            if not github_url and paper.arxiv_id:
                github_url = await self.github_search.search_by_arxiv_id(paper.arxiv_id)

            if github_url:
                paper.github_url = github_url

        # Get citation count
        if paper.citation_count is None or paper.citation_count == 0:
            citation_count = await self.citation_counter.get_citation_count(paper.title)
            if citation_count is not None:
                paper.citation_count = citation_count

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
