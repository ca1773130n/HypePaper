"""Papers With Code API client for linking papers to GitHub repos.

Fetches GitHub repository links for research papers.
"""
from typing import Optional

import httpx


class PapersWithCodeClient:
    """Client for Papers With Code API."""

    BASE_URL = "https://paperswithcode.com/api/v1"

    def __init__(self):
        """Initialize Papers With Code client."""
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search_paper_by_arxiv(self, arxiv_id: str) -> Optional[dict]:
        """Search for paper by arXiv ID.

        Args:
            arxiv_id: arXiv identifier (e.g., "2301.12345")

        Returns:
            Paper data with GitHub repo if found, None otherwise
        """
        # Papers With Code uses URL format with version (v1, v2, etc.)
        # Try without version first
        arxiv_id_base = arxiv_id.split("v")[0]

        try:
            url = f"{self.BASE_URL}/papers/"
            params = {"arxiv_id": arxiv_id_base}

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                if data.get("count", 0) > 0:
                    results = data.get("results", [])
                    if results:
                        return results[0]  # Return first match

            return None

        except httpx.HTTPError as e:
            print(f"Papers With Code API error for {arxiv_id}: {e}")
            return None

    async def get_paper_repos(self, paper_id: str) -> list[dict]:
        """Get GitHub repositories for a paper.

        Args:
            paper_id: Papers With Code paper ID

        Returns:
            List of repository dictionaries with URLs and metadata
        """
        try:
            url = f"{self.BASE_URL}/papers/{paper_id}/repositories/"
            response = await self.client.get(url)

            if response.status_code == 200:
                data = response.json()
                repos = data.get("results", [])

                # Extract relevant info
                return [
                    {
                        "url": repo.get("url"),
                        "owner": repo.get("owner"),
                        "name": repo.get("name"),
                        "description": repo.get("description"),
                        "stars": repo.get("stars"),
                        "is_official": repo.get("is_official", False),
                    }
                    for repo in repos
                ]

            return []

        except httpx.HTTPError as e:
            print(f"Papers With Code repos error for {paper_id}: {e}")
            return []

    async def get_github_url_for_arxiv(self, arxiv_id: str) -> Optional[str]:
        """Get primary GitHub URL for an arXiv paper.

        Args:
            arxiv_id: arXiv identifier

        Returns:
            GitHub repo URL if found, None otherwise
        """
        paper = await self.search_paper_by_arxiv(arxiv_id)
        if not paper:
            return None

        paper_id = paper.get("id")
        if not paper_id:
            return None

        repos = await self.get_paper_repos(paper_id)
        if not repos:
            return None

        # Prefer official repos, then by stars
        official_repos = [r for r in repos if r.get("is_official")]
        if official_repos:
            return official_repos[0].get("url")

        # Fall back to most starred repo
        sorted_repos = sorted(repos, key=lambda r: r.get("stars", 0), reverse=True)
        return sorted_repos[0].get("url") if sorted_repos else None

    async def batch_get_github_urls(
        self, arxiv_ids: list[str]
    ) -> dict[str, Optional[str]]:
        """Batch fetch GitHub URLs for multiple arXiv papers.

        Args:
            arxiv_ids: List of arXiv identifiers

        Returns:
            Dictionary mapping arXiv ID to GitHub URL (or None if not found)
        """
        results = {}

        for arxiv_id in arxiv_ids:
            github_url = await self.get_github_url_for_arxiv(arxiv_id)
            results[arxiv_id] = github_url

        return results

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
