"""URL extraction service for papers.

Extracts various URLs from paper abstracts and metadata:
- Project website URLs
- GitHub repository URLs
- YouTube video URLs
"""
import re
from typing import Optional, Dict
from urllib.parse import urlparse


class URLExtractor:
    """Extract and classify URLs from paper text."""

    # Common project page domains
    PROJECT_DOMAINS = {
        'github.io',
        'gitlab.io',
        'pages.dev',
        'vercel.app',
        'netlify.app',
        'web.app',
        'firebaseapp.com'
    }

    # GitHub URL patterns
    GITHUB_PATTERNS = [
        r'https?://github\.com/[\w-]+/[\w.-]+',
        r'github\.com/[\w-]+/[\w.-]+'
    ]

    # YouTube URL patterns
    YOUTUBE_PATTERNS = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://youtu\.be/[\w-]+',
        r'youtube\.com/watch\?v=[\w-]+'
    ]

    # General URL pattern
    URL_PATTERN = r'https?://[^\s<>"{}|\\^`\[\]]+'

    def extract_urls_from_abstract(self, abstract: str) -> Dict[str, Optional[str]]:
        """
        Extract all URLs from abstract and classify them.

        Args:
            abstract: Paper abstract text

        Returns:
            Dictionary with keys: github_url, project_page_url, youtube_url
        """
        result = {
            'github_url': None,
            'project_page_url': None,
            'youtube_url': None
        }

        if not abstract:
            return result

        # Find all URLs
        urls = re.findall(self.URL_PATTERN, abstract, re.IGNORECASE)

        for url in urls:
            # Clean up URL (remove trailing punctuation)
            url = url.rstrip('.,;:!?)')

            # Classify URL
            if self._is_github_url(url) and not result['github_url']:
                result['github_url'] = url
            elif self._is_youtube_url(url) and not result['youtube_url']:
                result['youtube_url'] = url
            elif self._is_project_page(url) and not result['project_page_url']:
                result['project_page_url'] = url

        return result

    def _is_github_url(self, url: str) -> bool:
        """Check if URL is a GitHub repository URL."""
        for pattern in self.GITHUB_PATTERNS:
            if re.match(pattern, url, re.IGNORECASE):
                # Make sure it's not just github.io (project page)
                parsed = urlparse(url)
                if parsed.hostname and 'github.com' in parsed.hostname:
                    return True
        return False

    def _is_youtube_url(self, url: str) -> bool:
        """Check if URL is a YouTube video URL."""
        for pattern in self.YOUTUBE_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def _is_project_page(self, url: str) -> bool:
        """
        Check if URL is likely a project website.

        Returns True for:
        - Common project hosting domains (github.io, etc)
        - Personal/academic domains with paths suggesting a project
        """
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ''

            # Check if it's a known project hosting domain
            for domain in self.PROJECT_DOMAINS:
                if domain in hostname:
                    return True

            # Check for academic/personal sites with project-like paths
            # e.g., username.edu/project-name, lab.university.edu/research/project
            if any(tld in hostname for tld in ['.edu', '.ac.']):
                path = parsed.path.lower()
                if any(keyword in path for keyword in ['project', 'demo', 'research', 'paper']):
                    return True

            # If it's not GitHub, YouTube, or a common service, assume it's a project page
            common_services = ['arxiv.org', 'doi.org', 'scholar.google', 'semanticscholar.org',
                             'twitter.com', 'linkedin.com', 'facebook.com']
            if not any(service in hostname for service in common_services):
                return True

            return False

        except Exception:
            return False

    def normalize_github_url(self, url: str) -> str:
        """
        Normalize GitHub URL to standard format.

        Args:
            url: Raw GitHub URL

        Returns:
            Normalized GitHub URL (https://github.com/owner/repo)
        """
        if not url:
            return url

        # Extract owner and repo name
        match = re.search(r'github\.com/([\w-]+)/([\w.-]+)', url, re.IGNORECASE)
        if match:
            owner, repo = match.groups()
            # Remove .git suffix if present
            repo = repo.rstrip('.git')
            return f"https://github.com/{owner}/{repo}"

        return url

    def normalize_youtube_url(self, url: str) -> str:
        """
        Normalize YouTube URL to standard watch format.

        Args:
            url: Raw YouTube URL

        Returns:
            Normalized YouTube URL (https://www.youtube.com/watch?v=VIDEO_ID)
        """
        if not url:
            return url

        # Extract video ID from various formats
        video_id = None

        # youtu.be format
        match = re.search(r'youtu\.be/([\w-]+)', url)
        if match:
            video_id = match.group(1)

        # youtube.com/watch format
        if not video_id:
            match = re.search(r'[?&]v=([\w-]+)', url)
            if match:
                video_id = match.group(1)

        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"

        return url
