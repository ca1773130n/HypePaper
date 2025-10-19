"""GitHub repository scraper for extracting stars and metadata."""
import re
import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import aiohttp
from bs4 import BeautifulSoup


class GitHubScraper:
    """Scrapes GitHub repositories to extract stars and metadata."""

    def __init__(self):
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def extract_github_urls(self, text: str) -> list[str]:
        """Extract GitHub repository URLs from text.

        Args:
            text: Text content to search for GitHub URLs

        Returns:
            List of GitHub repository URLs found
        """
        if not text:
            return []

        # Pattern to match GitHub repository URLs
        github_pattern = r'https?://(?:www\.)?github\.com/([^/\s]+)/([^/\s]+)(?:/[^\s]*)?'
        matches = re.findall(github_pattern, text, re.IGNORECASE)

        # Convert matches to clean repo URLs
        urls = []
        for owner, repo in matches:
            # Clean repo name (remove .git, trailing chars, etc.)
            repo = repo.split('.')[0].split('?')[0].split('#')[0]
            if repo and not repo.startswith('.'):
                urls.append(f"https://github.com/{owner}/{repo}")

        return list(set(urls))  # Remove duplicates

    async def scrape_github_stars(self, github_url: str) -> Optional[Dict[str, Any]]:
        """Scrape GitHub repository to get stars and metadata.

        Args:
            github_url: GitHub repository URL

        Returns:
            Dict with stars, forks, and other metadata, or None if failed
        """
        if not self.session:
            raise RuntimeError("GitHubScraper must be used as async context manager")

        try:
            # Normalize URL
            parsed = urlparse(github_url)
            if parsed.netloc != 'github.com':
                return None

            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                return None

            owner, repo = path_parts[0], path_parts[1]
            clean_url = f"https://github.com/{owner}/{repo}"

            print(f"[GITHUB] Scraping {clean_url}")

            async with self.session.get(clean_url) as response:
                if response.status != 200:
                    print(f"[GITHUB] HTTP {response.status} for {clean_url}")
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Extract stars - try multiple selectors
                stars = self._extract_stars(soup)
                forks = self._extract_forks(soup)
                language = self._extract_language(soup)
                description = self._extract_description(soup)

                if stars is None:
                    print(f"[GITHUB] Could not find stars for {clean_url}")
                    return None

                result = {
                    'url': clean_url,
                    'owner': owner,
                    'repo': repo,
                    'stars': stars,
                    'forks': forks,
                    'language': language,
                    'description': description
                }

                print(f"[GITHUB] Success: {clean_url} -> {stars} stars")
                return result

        except asyncio.TimeoutError:
            print(f"[GITHUB] Timeout scraping {github_url}")
            return None
        except Exception as e:
            print(f"[GITHUB] Error scraping {github_url}: {e}")
            return None

    def _extract_stars(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract star count from GitHub page HTML."""
        # Try multiple selectors for stars
        selectors = [
            # New GitHub layout
            'a[href$="/stargazers"] strong',
            'a[href$="/stargazers"] span',
            '#repo-stars-counter-star',
            '[data-target="repo-stars-counter.stars"]',
            # Older layouts
            '.js-social-count[href$="/stargazers"]',
            'a.social-count[href$="/stargazers"]',
            # Alternative patterns
            'span.Counter[title*="star"]',
            'span[title*="star"]'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                stars = self._parse_number(text)
                if stars is not None:
                    return stars

        return None

    def _extract_forks(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract fork count from GitHub page HTML."""
        selectors = [
            'a[href$="/forks"] strong',
            'a[href$="/forks"] span',
            '#repo-network-counter',
            '[data-target="repo-network-counter.forks"]',
            '.js-social-count[href$="/forks"]',
            'a.social-count[href$="/forks"]'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                forks = self._parse_number(text)
                if forks is not None:
                    return forks

        return None

    def _extract_language(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract primary language from GitHub page."""
        selectors = [
            '[data-target="repo-language-color-picker.text"]',
            '.BorderGrid-cell .ml-md-3 span[title]',
            'span.ml-0.mr-3 span'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                lang = element.get_text(strip=True)
                if lang and len(lang) < 20:  # Reasonable language name
                    return lang

        return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract repository description."""
        selectors = [
            '[data-target="repository-description.text"]',
            '.f4.my-3',
            'p.f4.mt-3'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                desc = element.get_text(strip=True)
                if desc and len(desc) > 5:  # Non-empty description
                    return desc[:500]  # Limit length

        return None

    def _parse_number(self, text: str) -> Optional[int]:
        """Parse number from text (handles k, M suffixes)."""
        if not text:
            return None

        text = text.strip().replace(',', '')

        # Handle suffixes like 1.2k, 5.6M
        if text.lower().endswith('k'):
            try:
                num = float(text[:-1])
                return int(num * 1000)
            except ValueError:
                pass
        elif text.lower().endswith('m'):
            try:
                num = float(text[:-1])
                return int(num * 1000000)
            except ValueError:
                pass
        else:
            # Try to parse as integer
            try:
                return int(text)
            except ValueError:
                pass

        return None


async def scrape_github_stars_for_paper(paper_text: str) -> list[Dict[str, Any]]:
    """Scrape GitHub stars for all repos found in paper text.

    Args:
        paper_text: Combined text from paper (title, abstract, etc.)

    Returns:
        List of GitHub repository data with stars
    """
    if not paper_text:
        return []

    async with GitHubScraper() as scraper:
        github_urls = scraper.extract_github_urls(paper_text)

        if not github_urls:
            return []

        # Scrape all URLs concurrently with rate limiting
        tasks = []
        for url in github_urls[:5]:  # Limit to 5 repos per paper
            tasks.append(scraper.scrape_github_stars(url))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        github_data = []
        for result in results:
            if isinstance(result, dict) and result.get('stars') is not None:
                github_data.append(result)

        return github_data