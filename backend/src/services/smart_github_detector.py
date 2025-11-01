"""Smart GitHub URL detection service.

Improved GitHub repository detection that:
1. Distinguishes between direct GitHub URLs and project websites in abstracts
2. Parses project websites to find CODE buttons/links
3. Uses Google search with intelligent filtering to avoid paper list repos
4. Filters out repositories that are collections/lists rather than implementations
"""
import re
import asyncio
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse, urljoin
import aiohttp
from bs4 import BeautifulSoup
import json


class SmartGitHubDetector:
    """Intelligent GitHub repository detection for research papers."""

    def __init__(self):
        """Initialize the detector."""
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def detect_github_url(self, paper_title: str, abstract: str, arxiv_id: Optional[str] = None) -> Optional[str]:
        """
        Main method to detect GitHub URL for a paper.

        Args:
            paper_title: Title of the research paper
            abstract: Paper abstract text
            arxiv_id: arXiv ID if available

        Returns:
            GitHub repository URL if found, None otherwise
        """
        print(f"[SMART_DETECTOR] Starting detection for: {paper_title[:50]}...")

        # Step 1: Extract URLs from abstract and classify them
        urls_info = self._extract_and_classify_urls(abstract)
        print(f"[SMART_DETECTOR] Found URLs: {urls_info}")

        # Step 2: If direct GitHub URL found, validate it's not a paper list repo
        if urls_info['direct_github']:
            print(f"[SMART_DETECTOR] Checking direct GitHub URLs...")
            for github_url in urls_info['direct_github']:
                print(f"[SMART_DETECTOR] Validating: {github_url}")
                if await self._is_valid_implementation_repo(github_url, paper_title):
                    print(f"[SMART_DETECTOR] ✅ Valid implementation repo: {github_url}")
                    return github_url
                else:
                    print(f"[SMART_DETECTOR] ❌ Invalid/paper list repo: {github_url}")

        # Step 3: If project website found, parse it for CODE buttons
        if urls_info['project_websites']:
            print(f"[SMART_DETECTOR] Parsing project websites...")
            for website in urls_info['project_websites']:
                print(f"[SMART_DETECTOR] Parsing website: {website}")
                github_url = await self._parse_project_website_for_github(website)
                if github_url:
                    print(f"[SMART_DETECTOR] Found GitHub URL from website: {github_url}")
                    if await self._is_valid_implementation_repo(github_url, paper_title):
                        print(f"[SMART_DETECTOR] ✅ Valid implementation repo from website: {github_url}")
                        return github_url

        # Step 4: Use GitHub search as fallback
        print(f"[SMART_DETECTOR] Falling back to GitHub search...")
        github_url = await self._google_search_for_github(paper_title, arxiv_id)
        if github_url:
            print(f"[SMART_DETECTOR] Found from search: {github_url}")
            if await self._is_valid_implementation_repo(github_url, paper_title):
                print(f"[SMART_DETECTOR] ✅ Valid implementation repo from search: {github_url}")
                return github_url

        print(f"[SMART_DETECTOR] ❌ No GitHub URL found")
        return None

    def _extract_and_classify_urls(self, abstract: str) -> Dict[str, List[str]]:
        """
        Extract URLs from abstract and classify them.

        Returns:
            Dict with 'direct_github' and 'project_websites' lists
        """
        result = {
            'direct_github': [],
            'project_websites': []
        }

        if not abstract:
            return result

        # Find all URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, abstract, re.IGNORECASE)

        for url in urls:
            # Clean up URL
            url = url.rstrip('.,;:!?)')

            if self._is_direct_github_url(url):
                result['direct_github'].append(url)
            elif self._is_project_website(url):
                result['project_websites'].append(url)

        return result

    def _is_direct_github_url(self, url: str) -> bool:
        """Check if URL is a direct GitHub repository URL."""
        github_patterns = [
            r'https?://github\.com/[\w-]+/[\w.-]+',
            r'github\.com/[\w-]+/[\w.-]+'
        ]

        for pattern in github_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                parsed = urlparse(url)
                # Make sure it's github.com, not github.io
                if parsed.hostname and parsed.hostname.lower() == 'github.com':
                    return True
        return False

    def _is_github_io_url(self, url: str) -> bool:
        """
        Check if URL is a GitHub.io project website.

        GitHub.io URLs are project websites, not repositories.
        We need to parse these pages to find the actual repository URL.
        """
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ''
            return hostname.lower().endswith('.github.io')
        except Exception:
            return False

    def _is_project_website(self, url: str) -> bool:
        """
        Check if URL is likely a project website (not GitHub, arXiv, or academic services).
        """
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ''
            hostname = hostname.lower()

            # Skip academic/paper services
            academic_services = [
                'github.com', 'arxiv.org', 'doi.org', 'scholar.google',
                'semanticscholar.org', 'acm.org', 'ieee.org', 'springer.com',
                'twitter.com', 'linkedin.com', 'facebook.com'
            ]

            if any(service in hostname for service in academic_services):
                return False

            # Common project hosting domains (including GitHub.io)
            project_domains = [
                'github.io', 'gitlab.io', 'pages.dev', 'vercel.app',
                'netlify.app', 'web.app', 'firebaseapp.com', 'herokuapp.com',
                'xyz'  # Added .xyz domains which are popular for project sites
            ]

            if any(domain in hostname for domain in project_domains):
                return True

            # Academic/research domains with project-like paths
            if any(tld in hostname for tld in ['.edu', '.ac.', '.org']):
                path = parsed.path.lower()
                if any(keyword in path for keyword in ['project', 'demo', 'research', 'paper', 'code']):
                    return True

            # Personal/lab websites (common patterns)
            personal_patterns = [
                r'[\w-]+\.github\.io',
                r'people\.[\w.-]+',
                r'[\w-]+\.[\w-]+\.edu',
                r'[\w-]+lab\.[\w.-]+',
                r'[\w-]+\.xyz'  # Added .xyz pattern
            ]

            for pattern in personal_patterns:
                if re.match(pattern, hostname):
                    return True

            # If it's not a known academic service and looks like a website, consider it a project page
            if hostname and '.' in hostname:
                return True

            return False

        except Exception:
            return False

    async def _parse_github_io_for_repo(self, github_io_url: str) -> Optional[str]:
        """
        Specialized parser for GitHub.io pages to extract repository URL.

        GitHub.io pages have specific patterns:
        1. Often have a "View on GitHub" corner ribbon
        2. Meta tags containing repository info
        3. GitHub icons/links in header/footer
        4. Jekyll/Sphinx template patterns
        """
        if not self.session:
            return None

        try:
            print(f"[GITHUB_IO_PARSER] Parsing GitHub.io page: {github_io_url}")
            async with self.session.get(github_io_url) as response:
                if response.status != 200:
                    print(f"[GITHUB_IO_PARSER] Failed to fetch page, status: {response.status}")
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Strategy 1: Check meta tags (common in GitHub.io pages)
                meta_patterns = [
                    ('property', 'og:url'),
                    ('name', 'github-repo'),
                    ('property', 'al:web:url')
                ]
                for attr_name, attr_value in meta_patterns:
                    meta = soup.find('meta', {attr_name: attr_value})
                    if meta and meta.get('content'):
                        content = meta.get('content')
                        if self._is_direct_github_url(content):
                            print(f"[GITHUB_IO_PARSER] Found in meta tag: {content}")
                            return self._normalize_github_url(content)

                # Strategy 2: Look for "View on GitHub" / "Fork me on GitHub" ribbons
                ribbon_patterns = [
                    r'view\s+on\s+github', r'fork\s+me', r'github\s+repository',
                    r'star\s+on\s+github', r'source\s+on\s+github'
                ]
                for pattern in ribbon_patterns:
                    elements = soup.find_all(['a', 'div', 'span'], string=re.compile(pattern, re.IGNORECASE))
                    for element in elements:
                        # Check element itself if it's a link
                        if element.name == 'a':
                            href = element.get('href')
                            if href and self._is_direct_github_url(href):
                                print(f"[GITHUB_IO_PARSER] Found in ribbon: {href}")
                                return self._normalize_github_url(href)
                        # Check for nested links
                        parent = element.find_parent('a', href=True)
                        if parent:
                            href = parent.get('href')
                            if href and self._is_direct_github_url(href):
                                print(f"[GITHUB_IO_PARSER] Found in ribbon parent: {href}")
                                return self._normalize_github_url(href)

                # Strategy 3: Check for GitHub icons/SVG (common in headers)
                github_icons = soup.find_all('svg', class_=re.compile(r'octicon|github', re.IGNORECASE))
                for icon in github_icons:
                    parent_link = icon.find_parent('a', href=True)
                    if parent_link:
                        href = parent_link.get('href')
                        if href and self._is_direct_github_url(href):
                            print(f"[GITHUB_IO_PARSER] Found via GitHub icon: {href}")
                            return self._normalize_github_url(href)

                # Strategy 4: Check for links with GitHub icons (FontAwesome, etc.)
                icon_links = soup.find_all('a', href=True)
                for link in icon_links:
                    # Check for GitHub-related classes or aria-labels
                    classes = ' '.join(link.get('class', [])).lower()
                    aria_label = (link.get('aria-label') or '').lower()
                    if 'github' in classes or 'github' in aria_label:
                        href = link.get('href')
                        if href and self._is_direct_github_url(href):
                            print(f"[GITHUB_IO_PARSER] Found via icon class/label: {href}")
                            return self._normalize_github_url(href)

                # Strategy 5: Extract username from GitHub.io URL and construct repo URL
                # Pattern: username.github.io/repo-name or username.github.io (user page)
                parsed = urlparse(github_io_url)
                hostname = parsed.hostname or ''
                if hostname.endswith('.github.io'):
                    username = hostname.replace('.github.io', '')
                    path_parts = parsed.path.strip('/').split('/')

                    # If there's a path, the first part is likely the repo name
                    if path_parts and path_parts[0]:
                        repo_name = path_parts[0]
                        inferred_url = f"https://github.com/{username}/{repo_name}"
                        print(f"[GITHUB_IO_PARSER] Inferred from URL structure: {inferred_url}")
                        # We'll validate this in the next step
                        return inferred_url
                    else:
                        # It might be a user page (username.github.io)
                        # Try to find any link to that user's repositories
                        inferred_url = f"https://github.com/{username}"
                        print(f"[GITHUB_IO_PARSER] Found user page, checking: {inferred_url}")

                # Strategy 6: Look for any github.com links as fallback
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href')
                    if href and self._is_direct_github_url(href):
                        # Prefer repository links over user profiles
                        if href.count('/') >= 4:  # github.com/user/repo
                            print(f"[GITHUB_IO_PARSER] Found generic GitHub link: {href}")
                            return self._normalize_github_url(href)

                print(f"[GITHUB_IO_PARSER] No repository URL found")
                return None

        except Exception as e:
            print(f"[GITHUB_IO_PARSER] Error parsing GitHub.io page {github_io_url}: {e}")
            return None

    async def _parse_project_website_for_github(self, website_url: str) -> Optional[str]:
        """
        Parse project website to find GitHub repository link.

        Looks for common patterns like:
        - Links with text "Code", "GitHub", "Source Code"
        - <a> tags with GitHub URLs
        - Common button/link patterns

        For GitHub.io URLs, uses specialized parsing logic.
        """
        if not self.session:
            return None

        # Use specialized parser for GitHub.io pages
        if self._is_github_io_url(website_url):
            print(f"[PARSER] Detected GitHub.io URL, using specialized parser")
            return await self._parse_github_io_for_repo(website_url)

        try:
            async with self.session.get(website_url) as response:
                if response.status != 200:
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Strategy 1: Look for links with specific text patterns
                code_text_patterns = [
                    r'\bcode\b', r'\bgithub\b', r'\bsource\s*code\b',
                    r'\brepository\b', r'\brepo\b', r'\bimplementation\b'
                ]

                for pattern in code_text_patterns:
                    links = soup.find_all('a', string=re.compile(pattern, re.IGNORECASE))
                    for link in links:
                        href = link.get('href')
                        if href and self._is_direct_github_url(href):
                            return self._normalize_github_url(href)
                        elif href and not href.startswith('http'):
                            # Relative URL, make it absolute
                            absolute_url = urljoin(website_url, href)
                            if self._is_direct_github_url(absolute_url):
                                return self._normalize_github_url(absolute_url)

                # Strategy 2: Look for any GitHub URLs in href attributes
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href')
                    if href and self._is_direct_github_url(href):
                        return self._normalize_github_url(href)

                # Strategy 3: Look for GitHub URLs in button elements
                buttons = soup.find_all(['button', 'div'], class_=re.compile(r'btn|button|code|github', re.IGNORECASE))
                for button in buttons:
                    # Check if button contains or links to GitHub
                    onclick = button.get('onclick', '')
                    if 'github.com' in onclick:
                        github_match = re.search(r'github\.com/[\w-]+/[\w.-]+', onclick)
                        if github_match:
                            return f"https://{github_match.group()}"

                    # Check for nested links
                    nested_link = button.find('a', href=True)
                    if nested_link:
                        href = nested_link.get('href')
                        if href and self._is_direct_github_url(href):
                            return self._normalize_github_url(href)

                return None

        except Exception as e:
            print(f"Error parsing project website {website_url}: {e}")
            return None

    async def _google_search_for_github(self, paper_title: str, arxiv_id: Optional[str] = None) -> Optional[str]:
        """
        Use GitHub's own search to find repository for the paper.

        This is more reliable than Google search and doesn't require web scraping.
        """
        if not self.session:
            return None

        github_search_url = "https://api.github.com/search/repositories"

        search_queries = []

        # Strategy 1: Search with paper title
        search_queries.append(f'"{paper_title}"')

        # Strategy 2: If we have arXiv ID, search with that
        if arxiv_id:
            search_queries.append(f'"{arxiv_id}"')

        # Strategy 3: Search with key terms from title
        title_words = re.findall(r'\b\w{4,}\b', paper_title.lower())
        if len(title_words) >= 2:
            key_terms = ' '.join(title_words[:3])  # Take first 3 significant words
            search_queries.append(f'{key_terms} implementation')

        for query in search_queries:
            try:
                params = {
                    'q': query,
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 5
                }

                async with self.session.get(github_search_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if 'items' in data:
                            for item in data['items']:
                                github_url = item['html_url']
                                if await self._is_valid_implementation_repo(github_url, paper_title):
                                    return github_url

            except Exception as e:
                print(f"Error in GitHub search: {e}")
                continue

        return None

    def _extract_github_urls_from_google_results(self, html: str) -> List[str]:
        """Extract GitHub URLs from Google search results HTML."""
        github_urls = []

        # Look for GitHub URLs in the HTML
        github_pattern = r'https://github\.com/[\w-]+/[\w.-]+'
        matches = re.findall(github_pattern, html, re.IGNORECASE)

        for match in matches:
            normalized = self._normalize_github_url(match)
            if normalized not in github_urls:
                github_urls.append(normalized)

        return github_urls

    async def _is_valid_implementation_repo(self, github_url: str, paper_title: str) -> bool:
        """
        Check if GitHub repository is a valid implementation (not a paper list).

        Filters out repositories that are:
        - Paper collections/lists
        - Awesome lists
        - Too generic
        """
        if not self.session:
            return False

        try:
            # Get repository info via GitHub API
            parsed = urlparse(github_url)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                return False

            owner, repo = path_parts[0], path_parts[1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}"

            async with self.session.get(api_url) as response:
                if response.status != 200:
                    return False

                repo_data = await response.json()

                # Handle API rate limiting or errors
                if 'message' in repo_data:
                    print(f"GitHub API message: {repo_data['message']}")
                    return False

                # Check 1: Repository name and description patterns
                repo_name = repo_data.get('name', '').lower()
                description = repo_data.get('description', '').lower()

                # Red flags - likely paper collection repos
                paper_list_indicators = [
                    'arvix', 'awesome', 'papers', 'collection', 'list', 'survey',
                    'reading', 'resources', 'curated', 'bibliography',
                    'must-read', 'paper-list', 'research-papers',
                    'daily-ai', 'daily-papers', 'ai-papers', 'paper-digest',
                    'trending-papers', 'arxiv-digest', 'ml-papers', 'ai-news',
                    'paper-feed', 'research-digest', 'academic-papers'
                ]

                for indicator in paper_list_indicators:
                    if indicator in repo_name or indicator in description:
                        return False

                # Check 2: Repository structure (get top-level files)
                contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
                async with self.session.get(contents_url) as contents_response:
                    if contents_response.status == 200:
                        contents = await contents_response.json()

                        # Handle API errors
                        if isinstance(contents, dict) and 'message' in contents:
                            return True  # Assume valid if we can't check contents

                        if isinstance(contents, list):
                            # Look for implementation indicators
                            implementation_files = [
                                'main.py', 'train.py', 'model.py', 'requirements.txt',
                                'package.json', 'Dockerfile', 'Makefile', 'setup.py',
                                'src/', 'lib/', 'models/', 'data/', 'scripts/'
                            ]

                            file_names = [item.get('name', '').lower() for item in contents]

                            # Check if we have implementation files
                            has_implementation = any(
                                any(impl_file in fname for impl_file in implementation_files)
                                for fname in file_names
                            )

                            # Check for paper list indicators in file structure
                            paper_list_files = ['papers.md', 'readme.md', 'paper-list.md']
                            has_paper_list = any(
                                any(list_file in fname for list_file in paper_list_files)
                                for fname in file_names
                            )

                            # If it has paper list structure but no implementation, likely a collection
                            if has_paper_list and not has_implementation:
                                return False

                # Check 3: Repository size and activity (basic heuristics)
                size_kb = repo_data.get('size', 0)
                stargazers = repo_data.get('stargazers_count', 0)

                # Very small repos with many stars might be paper lists
                if size_kb < 100 and stargazers > 50:
                    return False

                # Check 4: Language distribution (implementation repos usually have substantial code)
                languages_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
                async with self.session.get(languages_url) as lang_response:
                    if lang_response.status == 200:
                        languages = await lang_response.json()

                        # If mostly markdown/text, likely a paper collection
                        total_bytes = sum(languages.values()) if languages else 0
                        markdown_bytes = languages.get('Markdown', 0)

                        if total_bytes > 0 and (markdown_bytes / total_bytes) > 0.8:
                            return False

                return True

        except Exception as e:
            print(f"Error validating repository {github_url}: {e}")
            return False

    def _normalize_github_url(self, url: str) -> str:
        """Normalize GitHub URL to standard format."""
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


# Example usage function for testing
async def test_detector():
    """Test the GitHub detector with sample papers."""
    detector = SmartGitHubDetector()

    test_cases = [
        {
            'title': 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
            'abstract': 'We introduce a new language representation model called BERT. Code available at https://github.com/google-research/bert',
            'expected': 'https://github.com/google-research/bert'
        },
        {
            'title': 'Attention Is All You Need',
            'abstract': 'We propose a new network architecture, the Transformer. Project page: https://transformer-model.github.io',
            'expected': None  # Would need to parse project page
        }
    ]

    async with detector:
        for test in test_cases:
            result = await detector.detect_github_url(
                test['title'],
                test['abstract']
            )
            print(f"Title: {test['title']}")
            print(f"Expected: {test['expected']}")
            print(f"Found: {result}")
            print("---")


if __name__ == "__main__":
    asyncio.run(test_detector())