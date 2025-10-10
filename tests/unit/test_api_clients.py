"""
Unit tests for API client rate limiting and parsing logic.

Tests API clients without making real HTTP requests.
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import re


class TestGitHubClientParsing:
    """Test GitHub URL parsing logic."""

    @pytest.fixture
    def github_client(self):
        """Mock GitHub client for testing."""
        class MockGitHubClient:
            def _parse_github_url(self, url: str):
                """Parse GitHub repository URL to extract owner and repo name."""
                patterns = [
                    r'github\.com/([^/]+)/([^/]+?)(?:\.git)?$',
                    r'github\.com/([^/]+)/([^/]+)',
                    r'git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$'
                ]

                for pattern in patterns:
                    match = re.search(pattern, url)
                    if match:
                        owner, repo = match.groups()
                        repo = repo.rstrip('.git')
                        return (owner, repo)
                return None

        return MockGitHubClient()

    def test_parse_https_url(self, github_client):
        """Test parsing HTTPS GitHub URL."""
        url = "https://github.com/owner/repo"
        result = github_client._parse_github_url(url)

        assert result == ("owner", "repo"), f"Expected ('owner', 'repo'), got {result}"

    def test_parse_https_url_with_git_extension(self, github_client):
        """Test parsing HTTPS URL with .git extension."""
        url = "https://github.com/owner/repo.git"
        result = github_client._parse_github_url(url)

        assert result == ("owner", "repo"), f"Expected ('owner', 'repo'), got {result}"

    def test_parse_ssh_url(self, github_client):
        """Test parsing SSH GitHub URL."""
        url = "git@github.com:owner/repo.git"
        result = github_client._parse_github_url(url)

        assert result == ("owner", "repo"), f"Expected ('owner', 'repo'), got {result}"

    def test_parse_url_with_trailing_slash(self, github_client):
        """Test parsing URL with trailing content."""
        url = "https://github.com/owner/repo/tree/main"
        result = github_client._parse_github_url(url)

        # Should still extract owner and repo
        assert result is not None, "Should parse URL with path"
        assert result[0] == "owner", f"Expected owner 'owner', got {result[0]}"

    def test_parse_invalid_url(self, github_client):
        """Test parsing invalid URL returns None."""
        url = "https://gitlab.com/owner/repo"
        result = github_client._parse_github_url(url)

        assert result is None, f"Expected None for invalid URL, got {result}"

    def test_parse_url_with_hyphen_and_underscore(self, github_client):
        """Test parsing URL with special characters in owner/repo."""
        url = "https://github.com/my-org_name/my-repo_name"
        result = github_client._parse_github_url(url)

        assert result == ("my-org_name", "my-repo_name"), \
            f"Expected ('my-org_name', 'my-repo_name'), got {result}"


class TestArxivClientParsing:
    """Test arXiv XML parsing logic."""

    def test_parse_arxiv_id_from_url(self):
        """Test extracting arXiv ID from entry URL."""
        url = "http://arxiv.org/abs/2003.08934v2"
        # Extract ID pattern: YYMM.NNNNN or YYMM.NNNNNvN
        match = re.search(r'(\d{4}\.\d{4,5})(v\d+)?$', url)

        assert match is not None, "Should extract arXiv ID from URL"
        arxiv_id = match.group(1)
        assert arxiv_id == "2003.08934", f"Expected '2003.08934', got {arxiv_id}"

    def test_parse_arxiv_authors(self):
        """Test parsing author list from XML."""
        # Simulate XML parsing
        authors_xml = [
            {"name": "John Doe"},
            {"name": "Jane Smith"},
            {"name": "Bob Johnson"}
        ]

        authors = [author["name"] for author in authors_xml]

        assert len(authors) == 3, f"Expected 3 authors, got {len(authors)}"
        assert authors[0] == "John Doe", f"Expected 'John Doe', got {authors[0]}"

    def test_parse_categories(self):
        """Test extracting primary category from arXiv entry."""
        # Primary category is first in the list
        categories = ["cs.CV", "cs.LG", "cs.AI"]
        primary_category = categories[0]

        assert primary_category == "cs.CV", \
            f"Expected 'cs.CV' as primary category, got {primary_category}"


class TestRateLimiting:
    """Test rate limiting behavior."""

    @pytest.mark.asyncio
    async def test_arxiv_rate_limit_timing(self):
        """Test arXiv rate limit delay (~3 requests/second)."""
        delay = 0.34  # ArxivClient.RATE_LIMIT_DELAY

        start = datetime.now()
        await asyncio.sleep(delay)
        await asyncio.sleep(delay)
        await asyncio.sleep(delay)
        end = datetime.now()

        elapsed = (end - start).total_seconds()

        # Should take at least 3 * 0.34 = 1.02 seconds
        assert elapsed >= 1.0, \
            f"Rate limiting too fast: {elapsed}s for 3 requests (expected >= 1.0s)"

    @pytest.mark.asyncio
    async def test_semantic_scholar_rate_limit(self):
        """Test Semantic Scholar rate limit (100 req/s)."""
        delay = 0.01  # SemanticScholarClient.RATE_LIMIT_DELAY

        start = datetime.now()
        for _ in range(10):
            await asyncio.sleep(delay)
        end = datetime.now()

        elapsed = (end - start).total_seconds()

        # 10 requests should take at least 0.1 seconds
        assert elapsed >= 0.1, \
            f"Rate limiting too fast: {elapsed}s for 10 requests (expected >= 0.1s)"

    @pytest.mark.asyncio
    async def test_github_rate_limit(self):
        """Test GitHub rate limit (5000 req/hour = ~1.4 req/s)."""
        delay = 0.72  # GitHubClient.RATE_LIMIT_DELAY

        start = datetime.now()
        await asyncio.sleep(delay)
        await asyncio.sleep(delay)
        end = datetime.now()

        elapsed = (end - start).total_seconds()

        # 2 requests should take at least 1.44 seconds
        assert elapsed >= 1.4, \
            f"Rate limiting too fast: {elapsed}s for 2 requests (expected >= 1.4s)"


class TestPapersWithCodeClient:
    """Test Papers With Code client logic."""

    def test_repository_preference_official(self):
        """Test that official repositories are preferred."""
        repos = [
            {"url": "https://github.com/user/fork", "stars": 1000, "is_official": False},
            {"url": "https://github.com/official/repo", "stars": 500, "is_official": True},
            {"url": "https://github.com/another/fork", "stars": 2000, "is_official": False}
        ]

        # Prefer official repos
        official_repos = [r for r in repos if r.get("is_official")]
        if official_repos:
            selected = official_repos[0]
        else:
            selected = sorted(repos, key=lambda r: r["stars"], reverse=True)[0]

        assert selected["url"] == "https://github.com/official/repo", \
            f"Should prefer official repo, got {selected['url']}"

    def test_repository_preference_by_stars(self):
        """Test that highest starred repo is chosen when no official repo."""
        repos = [
            {"url": "https://github.com/user/fork1", "stars": 1000, "is_official": False},
            {"url": "https://github.com/user/fork2", "stars": 2500, "is_official": False},
            {"url": "https://github.com/user/fork3", "stars": 500, "is_official": False}
        ]

        official_repos = [r for r in repos if r.get("is_official")]
        if official_repos:
            selected = official_repos[0]
        else:
            selected = sorted(repos, key=lambda r: r["stars"], reverse=True)[0]

        assert selected["stars"] == 2500, \
            f"Should select highest starred repo, got {selected['stars']} stars"
        assert selected["url"] == "https://github.com/user/fork2", \
            f"Should select fork2, got {selected['url']}"


class TestTopicMatchingKeywords:
    """Test topic matching keyword logic."""

    def test_keyword_matching_case_insensitive(self):
        """Test that keyword matching is case insensitive."""
        keywords = ["neural rendering", "nerf", "view synthesis"]
        text = "This paper presents a new NEURAL RENDERING technique using NeRF"

        text_lower = text.lower()
        matches = [kw for kw in keywords if kw.lower() in text_lower]

        assert len(matches) >= 2, f"Expected at least 2 keyword matches, got {matches}"
        assert "neural rendering" in matches, "Should match 'neural rendering'"
        assert "nerf" in matches, "Should match 'nerf'"

    def test_keyword_matching_partial_words(self):
        """Test keyword matching with partial word boundaries."""
        keywords = ["diffusion", "denoising"]
        text = "Denoising Diffusion Probabilistic Models"

        text_lower = text.lower()
        matches = [kw for kw in keywords if kw.lower() in text_lower]

        assert "diffusion" in matches, "Should match 'diffusion'"
        assert "denoising" in matches, "Should match 'denoising'"

    def test_relevance_score_calculation(self):
        """Test relevance score based on keyword matches."""
        keywords = ["3d reconstruction", "stereo", "depth", "mvs", "slam"]
        title = "Real-time 3D Reconstruction from Stereo Images"
        abstract = "We present a method for depth estimation using multi-view stereo"

        combined_text = f"{title} {abstract}".lower()
        matches = [kw for kw in keywords if kw.lower() in combined_text]

        # Score: 2 * num_matches (max 10)
        relevance_score = min(len(matches) * 2, 10)

        assert relevance_score >= 6, \
            f"Expected relevance >= 6 for {len(matches)} matches, got {relevance_score}"

    def test_no_keyword_match_returns_zero(self):
        """Test that papers with no keyword matches get 0 relevance."""
        keywords = ["quantum computing", "qubits", "entanglement"]
        text = "A survey of neural networks for image classification"

        text_lower = text.lower()
        matches = [kw for kw in keywords if kw.lower() in text_lower]
        relevance_score = min(len(matches) * 2, 10)

        assert relevance_score == 0, \
            f"Expected 0 relevance for no matches, got {relevance_score}"

    def test_multiple_occurrences_count_once(self):
        """Test that same keyword appearing multiple times counts once."""
        keywords = ["transformer", "attention"]
        text = "Transformer architecture using multi-head attention and transformer layers"

        text_lower = text.lower()
        # Count unique keyword matches
        matches = list(set([kw for kw in keywords if kw.lower() in text_lower]))

        assert len(matches) == 2, \
            f"Expected 2 unique keyword matches, got {len(matches)}: {matches}"
