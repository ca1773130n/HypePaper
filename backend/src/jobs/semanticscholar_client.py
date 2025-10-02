"""Semantic Scholar API client for fetching citation counts.

Fetches paper citations using the Semantic Scholar API.
Rate limit: 100 requests per second.
"""
import asyncio
from typing import Optional

import httpx


class SemanticScholarClient:
    """Client for Semantic Scholar API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    RATE_LIMIT_DELAY = 0.01  # 100 req/s = 10ms delay

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Semantic Scholar client.

        Args:
            api_key: Optional API key for higher rate limits
        """
        headers = {}
        if api_key:
            headers["x-api-key"] = api_key

        self.client = httpx.AsyncClient(timeout=30.0, headers=headers)
        self.last_request_time = 0.0

    async def _rate_limit(self):
        """Enforce rate limiting (100 req/s)."""
        elapsed = asyncio.get_event_loop().time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = asyncio.get_event_loop().time()

    async def get_paper_by_arxiv(self, arxiv_id: str) -> Optional[dict]:
        """Get paper details by arXiv ID.

        Args:
            arxiv_id: arXiv identifier (e.g., "2301.12345")

        Returns:
            Paper data with citations if found, None otherwise
        """
        await self._rate_limit()

        # Semantic Scholar uses arXiv format with version
        if "v" not in arxiv_id:
            # Try without version first, then with v1
            arxiv_id_search = arxiv_id
        else:
            arxiv_id_search = arxiv_id

        try:
            url = f"{self.BASE_URL}/paper/arXiv:{arxiv_id_search}"
            params = {"fields": "title,citationCount,externalIds"}

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # Try without version if we had one
                if "v" in arxiv_id:
                    arxiv_id_base = arxiv_id.split("v")[0]
                    url = f"{self.BASE_URL}/paper/arXiv:{arxiv_id_base}"
                    response = await self.client.get(url, params=params)
                    if response.status_code == 200:
                        return response.json()

            return None

        except httpx.HTTPError as e:
            print(f"Semantic Scholar API error for {arxiv_id}: {e}")
            return None

    async def get_paper_by_doi(self, doi: str) -> Optional[dict]:
        """Get paper details by DOI.

        Args:
            doi: Digital Object Identifier

        Returns:
            Paper data with citations if found, None otherwise
        """
        await self._rate_limit()

        try:
            url = f"{self.BASE_URL}/paper/DOI:{doi}"
            params = {"fields": "title,citationCount,externalIds"}

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                return response.json()

            return None

        except httpx.HTTPError as e:
            print(f"Semantic Scholar API error for DOI {doi}: {e}")
            return None

    async def get_citation_count(
        self, arxiv_id: Optional[str] = None, doi: Optional[str] = None
    ) -> Optional[int]:
        """Get citation count for a paper.

        Args:
            arxiv_id: arXiv identifier (optional)
            doi: Digital Object Identifier (optional)

        Returns:
            Citation count if found, None otherwise
        """
        paper = None

        # Try arXiv ID first
        if arxiv_id:
            paper = await self.get_paper_by_arxiv(arxiv_id)

        # Fall back to DOI
        if not paper and doi:
            paper = await self.get_paper_by_doi(doi)

        if paper:
            return paper.get("citationCount", 0)

        return None

    async def batch_get_citations(
        self, papers: list[dict]
    ) -> dict[str, Optional[int]]:
        """Batch fetch citation counts for multiple papers.

        Args:
            papers: List of paper dicts with 'arxiv_id' and/or 'doi' keys

        Returns:
            Dictionary mapping paper ID to citation count
        """
        results = {}

        for paper in papers:
            arxiv_id = paper.get("arxiv_id")
            doi = paper.get("doi")
            paper_id = paper.get("id") or arxiv_id or doi

            if not paper_id:
                continue

            citation_count = await self.get_citation_count(
                arxiv_id=arxiv_id, doi=doi
            )
            results[paper_id] = citation_count

        return results

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
