"""GitHub repository search service.

Searches for research paper implementations on GitHub using the GitHub API.
"""
import os
from typing import Optional
import aiohttp


class GitHubSearchService:
    """Search for GitHub repositories related to research papers."""

    GITHUB_API_URL = "https://api.github.com/search/repositories"

    def __init__(self):
        """Initialize with GitHub token if available."""
        self.token = os.environ.get("GITHUB_TOKEN")

    async def search_repository(self, title: str) -> Optional[str]:
        """
        Search for a research paper's implementation on GitHub using its title.

        Args:
            title: The title of the research paper

        Returns:
            The URL of the top search result, or None if not found
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        # Construct the search query to look for the title in the name,
        # description, or README of a repository
        query = f'"{title}" in:name,description,readme'
        params = {
            "q": query,
            "sort": "stars",  # Sort by stars for most popular implementation
            "order": "desc",
            "per_page": 1  # We only need the top result
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.GITHUB_API_URL,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        print(f"GitHub API error: {response.status}")
                        return None

                    data = await response.json()

                    if data.get("items"):
                        # Return the URL of the first search result
                        top_result = data["items"][0]
                        return top_result["html_url"]

                    return None

        except Exception as e:
            print(f"Error searching GitHub: {e}")
            return None

    async def search_by_arxiv_id(self, arxiv_id: str) -> Optional[str]:
        """
        Search for repository using arXiv ID.

        Many GitHub repos include the arXiv ID in their description or README.

        Args:
            arxiv_id: arXiv ID (e.g., 2410.12345)

        Returns:
            GitHub repository URL or None
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        # Search for arXiv ID
        query = f'"{arxiv_id}" in:description,readme'
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 1
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.GITHUB_API_URL,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()

                    if data.get("items"):
                        return data["items"][0]["html_url"]

                    return None

        except Exception as e:
            print(f"Error searching GitHub by arXiv ID: {e}")
            return None
