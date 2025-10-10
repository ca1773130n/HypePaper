"""
Async GitHub API service with secure authentication and rate limiting.

Provides methods for searching GitHub repositories, fetching star counts,
and calculating hype scores based on star history.
"""

import asyncio
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

import aiohttp
from aiohttp import ClientError


class GitHubRepo:
    """Represents a GitHub repository with metadata."""

    def __init__(
        self,
        url: str,
        full_name: str,
        stars: int,
        description: Optional[str] = None
    ):
        self.url = url
        self.full_name = full_name
        self.stars = stars
        self.description = description


class AsyncGitHubService:
    """
    Async service for interacting with the GitHub API.

    Features:
    - Secure token authentication from environment
    - Rate limiting (5000 req/hour with authenticated requests)
    - Papers with Code API integration for paper-repo linking
    - Hype score calculation (avg/weekly/monthly)
    """

    GITHUB_API_URL = "https://api.github.com"
    PAPERS_WITH_CODE_API_URL = "https://paperswithcode.com/api/v1"

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize GitHub service with authentication.

        Args:
            api_token: GitHub API token (defaults to GITHUB_TOKEN env var)

        Note:
            If no token is provided, GitHub API calls will be skipped (no enrichment)
        """
        self.api_token = api_token or os.getenv('GITHUB_TOKEN')

        if self.api_token:
            self.headers = {
                'Authorization': f'token {self.api_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'HypePaper-Bot/1.0'
            }
        else:
            self.headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'HypePaper-Bot/1.0'
            }

        # Rate limiting: 5000 requests per hour = ~1.4 req/sec
        self.semaphore = asyncio.Semaphore(5)

    async def search_repository(
        self,
        paper_title: str,
        arxiv_id: Optional[str] = None
    ) -> Optional[GitHubRepo]:
        """
        Search for GitHub repository associated with a paper.

        First tries Papers with Code API if arxiv_id is provided,
        then falls back to direct GitHub search.

        Args:
            paper_title: Title of the paper
            arxiv_id: ArXiv ID (e.g., "2101.12345")

        Returns:
            GitHubRepo object if found, None otherwise
        """
        # Try Papers with Code API first (if arxiv_id provided)
        if arxiv_id:
            repo = await self._search_papers_with_code(arxiv_id)
            if repo:
                return repo

        # Fallback to direct GitHub search
        return await self._search_github_direct(paper_title)

    async def _search_papers_with_code(
        self,
        arxiv_id: str
    ) -> Optional[GitHubRepo]:
        """
        Search Papers with Code API for repository link.

        Args:
            arxiv_id: ArXiv ID without version (e.g., "2101.12345")

        Returns:
            GitHubRepo if found, None otherwise
        """
        # Remove version suffix from arxiv_id if present
        clean_arxiv_id = arxiv_id.split('v')[0]

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.PAPERS_WITH_CODE_API_URL}/papers/{clean_arxiv_id}"

                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Extract GitHub URL from paper data
                        if 'repository_url' in data and data['repository_url']:
                            repo_url = data['repository_url']
                            # Fetch additional repo details from GitHub
                            return await self._get_repo_details(repo_url)

        except Exception as e:
            # Log but don't fail - fallback to direct search
            print(f"Papers with Code API error: {e}")

        return None

    async def _search_github_direct(
        self,
        paper_title: str
    ) -> Optional[GitHubRepo]:
        """
        Search GitHub directly for repositories matching paper title.

        Args:
            paper_title: Title to search for

        Returns:
            GitHubRepo with highest star count if found
        """
        async with self.semaphore:
            try:
                async with aiohttp.ClientSession() as session:
                    params = {
                        'q': f'{paper_title} in:name,description',
                        'sort': 'stars',
                        'order': 'desc',
                        'per_page': 5
                    }

                    async with session.get(
                        f"{self.GITHUB_API_URL}/search/repositories",
                        headers=self.headers,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()

                            if data.get('items') and len(data['items']) > 0:
                                # Return top result
                                repo_data = data['items'][0]
                                return GitHubRepo(
                                    url=repo_data['html_url'],
                                    full_name=repo_data['full_name'],
                                    stars=repo_data['stargazers_count'],
                                    description=repo_data.get('description')
                                )

            except Exception as e:
                print(f"GitHub search error: {e}")

        return None

    async def _get_repo_details(self, repo_url: str) -> Optional[GitHubRepo]:
        """
        Fetch repository details from GitHub API.

        Args:
            repo_url: GitHub repository URL (https://github.com/owner/repo)

        Returns:
            GitHubRepo with current details
        """
        # Extract owner/repo from URL
        parts = repo_url.rstrip('/').split('/')
        if len(parts) < 2:
            return None

        owner, repo = parts[-2], parts[-1]
        full_name = f"{owner}/{repo}"

        async with self.semaphore:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.GITHUB_API_URL}/repos/{full_name}",
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return GitHubRepo(
                                url=data['html_url'],
                                full_name=data['full_name'],
                                stars=data['stargazers_count'],
                                description=data.get('description')
                            )

            except Exception as e:
                print(f"GitHub API error fetching repo details: {e}")

        return None

    async def get_star_count(self, repo_url: str) -> int:
        """
        Get current star count for a GitHub repository.

        Args:
            repo_url: GitHub repository URL

        Returns:
            Current star count (0 if error)
        """
        repo = await self._get_repo_details(repo_url)
        return repo.stars if repo else 0

    async def calculate_hype_scores(
        self,
        star_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate hype scores based on star history.

        Formula: hype = (citations * 100 + stars) / age_days

        Args:
            star_history: List of dicts with 'timestamp', 'stars', 'citations' (optional)
                Example: [{'timestamp': datetime, 'stars': 100, 'citations': 10}, ...]

        Returns:
            Dict with avg_hype, weekly_hype, monthly_hype
        """
        if not star_history or len(star_history) == 0:
            return {
                'avg_hype': 0.0,
                'weekly_hype': 0.0,
                'monthly_hype': 0.0
            }

        # Sort by timestamp
        sorted_history = sorted(star_history, key=lambda x: x['timestamp'])

        # Calculate overall average hype
        total_hype = 0.0
        for entry in sorted_history:
            stars = entry.get('stars', 0)
            citations = entry.get('citations', 0)
            timestamp = entry['timestamp']

            # Calculate age in days from first entry
            age_days = max(1, (timestamp - sorted_history[0]['timestamp']).days)

            hype = (citations * 100 + stars) / age_days
            total_hype += hype

        avg_hype = total_hype / len(sorted_history)

        # Calculate weekly hype (last 7 days)
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        recent_weekly = [e for e in sorted_history if e['timestamp'] >= week_ago]

        if recent_weekly:
            latest = recent_weekly[-1]
            oldest = recent_weekly[0]
            star_growth = latest.get('stars', 0) - oldest.get('stars', 0)
            citation_growth = latest.get('citations', 0) - oldest.get('citations', 0)
            weekly_hype = (citation_growth * 100 + star_growth) / 7
        else:
            weekly_hype = 0.0

        # Calculate monthly hype (last 30 days)
        month_ago = now - timedelta(days=30)
        recent_monthly = [e for e in sorted_history if e['timestamp'] >= month_ago]

        if recent_monthly:
            latest = recent_monthly[-1]
            oldest = recent_monthly[0]
            star_growth = latest.get('stars', 0) - oldest.get('stars', 0)
            citation_growth = latest.get('citations', 0) - oldest.get('citations', 0)
            monthly_hype = (citation_growth * 100 + star_growth) / 30
        else:
            monthly_hype = 0.0

        return {
            'avg_hype': round(avg_hype, 2),
            'weekly_hype': round(weekly_hype, 2),
            'monthly_hype': round(monthly_hype, 2)
        }
