"""GitHub API client for fetching repository star counts.

Fetches star counts with rate limiting.
Rate limit: 5000 req/hour (authenticated), 60 req/hour (unauthenticated)
"""
import asyncio
import os
import re
from typing import Optional

import httpx


class GitHubClient:
    """Client for GitHub API with rate limiting."""

    BASE_URL = "https://api.github.com"
    RATE_LIMIT_DELAY = 0.72  # 5000 req/hour = ~1.4 req/s = 0.72s delay

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token (optional, increases rate limit)
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HypePaper/1.0",
        }

        # Use token from env if not provided
        token = token or os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        self.client = httpx.AsyncClient(timeout=30.0, headers=headers)
        self.last_request_time = 0.0
        self.authenticated = bool(token)

    async def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = asyncio.get_event_loop().time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = asyncio.get_event_loop().time()

    def _parse_github_url(self, url: str) -> Optional[tuple[str, str]]:
        """Parse GitHub URL to extract owner and repo.

        Args:
            url: GitHub repository URL

        Returns:
            Tuple of (owner, repo) or None if invalid
        """
        # Match various GitHub URL formats
        patterns = [
            r"github\.com/([^/]+)/([^/]+)",  # HTTPS
            r"github\.com:([^/]+)/([^/]+)",  # SSH
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                owner, repo = match.groups()
                # Remove .git suffix if present
                repo = repo.replace(".git", "")
                return owner, repo

        return None

    async def get_repo_info(self, owner: str, repo: str) -> Optional[dict]:
        """Get repository information including star count.

        Args:
            owner: Repository owner/organization
            repo: Repository name

        Returns:
            Repository data with stars, or None if not found
        """
        await self._rate_limit()

        try:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}"
            response = await self.client.get(url)

            if response.status_code == 200:
                data = response.json()
                return {
                    "owner": owner,
                    "repo": repo,
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "description": data.get("description"),
                    "language": data.get("language"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "url": data.get("html_url"),
                }
            elif response.status_code == 404:
                return None
            else:
                print(f"GitHub API error for {owner}/{repo}: {response.status_code}")
                return None

        except httpx.HTTPError as e:
            print(f"GitHub API error for {owner}/{repo}: {e}")
            return None

    async def get_star_count(self, github_url: str) -> Optional[int]:
        """Get star count for a GitHub repository.

        Args:
            github_url: Full GitHub repository URL

        Returns:
            Star count if found, None otherwise
        """
        parsed = self._parse_github_url(github_url)
        if not parsed:
            return None

        owner, repo = parsed
        repo_info = await self.get_repo_info(owner, repo)

        return repo_info.get("stars") if repo_info else None

    async def batch_get_stars(self, github_urls: list[str]) -> dict[str, Optional[int]]:
        """Batch fetch star counts for multiple repositories.

        Args:
            github_urls: List of GitHub repository URLs

        Returns:
            Dictionary mapping URL to star count
        """
        results = {}

        for url in github_urls:
            stars = await self.get_star_count(url)
            results[url] = stars

        return results

    async def check_rate_limit(self) -> dict:
        """Check current rate limit status.

        Returns:
            Dictionary with rate limit info (limit, remaining, reset)
        """
        try:
            url = f"{self.BASE_URL}/rate_limit"
            response = await self.client.get(url)

            if response.status_code == 200:
                data = response.json()
                core = data.get("resources", {}).get("core", {})
                return {
                    "limit": core.get("limit", 0),
                    "remaining": core.get("remaining", 0),
                    "reset": core.get("reset", 0),
                }

            return {}

        except httpx.HTTPError as e:
            print(f"GitHub rate limit check error: {e}")
            return {}

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
