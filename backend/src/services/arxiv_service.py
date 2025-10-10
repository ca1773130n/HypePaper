"""
Async ArXiv API service with retry logic and rate limiting.

Provides methods for searching papers on ArXiv with automatic retries,
exponential backoff, and rate limiting to comply with API guidelines.
"""

import asyncio
import random
import xml.etree.ElementTree as ET
from typing import List, Optional
from datetime import datetime

import aiohttp
from aiohttp import ClientError


class AsyncArxivService:
    """
    Async service for searching and retrieving papers from the ArXiv API.

    Features:
    - Retry logic with exponential backoff (3 attempts, 1s initial delay)
    - Rate limiting (3 requests/second with semaphore)
    - XML response parsing
    """

    ARXIV_API_URL = "http://export.arxiv.org/api/query"

    def __init__(
        self,
        max_retry: int = 3,
        retry_delay_sec: int = 1,
        rate_limit_per_sec: int = 3
    ):
        """
        Initialize ArXiv service.

        Args:
            max_retry: Maximum number of retry attempts
            retry_delay_sec: Initial delay between retries in seconds
            rate_limit_per_sec: Maximum requests per second
        """
        self.max_retry = max_retry
        self.retry_delay_sec = retry_delay_sec
        self.semaphore = asyncio.Semaphore(rate_limit_per_sec)

    async def search_by_keywords(
        self,
        keywords: str,
        max_results: int = 10
    ) -> List[dict]:
        """
        Search ArXiv papers by keywords with retry logic.

        Args:
            keywords: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of paper dictionaries with metadata

        Raises:
            aiohttp.ClientError: If all retry attempts fail
        """
        delay_sec = self.retry_delay_sec

        for attempt in range(self.max_retry):
            try:
                async with self.semaphore:
                    async with aiohttp.ClientSession() as session:
                        params = {
                            'search_query': f'all:{keywords}',
                            'max_results': max_results,
                            'sortBy': 'submittedDate',
                            'sortOrder': 'descending'
                        }

                        async with session.get(
                            self.ARXIV_API_URL,
                            params=params,
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as response:
                            response.raise_for_status()
                            text = await response.text()
                            return self._parse_arxiv_xml(text)

            except ClientError as e:
                if attempt < self.max_retry - 1:
                    await asyncio.sleep(delay_sec)
                    # Exponential backoff with jitter
                    delay_sec *= random.uniform(1.5, 2.5)
                else:
                    raise
            except Exception as e:
                if attempt < self.max_retry - 1:
                    await asyncio.sleep(delay_sec)
                    delay_sec *= random.uniform(1.5, 2.5)
                else:
                    raise

        return []

    async def search_by_arxiv_id(self, arxiv_id: str) -> List[dict]:
        """
        Search ArXiv papers by ArXiv ID.

        Args:
            arxiv_id: ArXiv ID (e.g., 2410.12345v1)

        Returns:
            List of matching papers (usually 1)
        """
        search_query = f'id:{arxiv_id}'

        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                params = {
                    'search_query': search_query,
                    'max_results': 1
                }

                async with session.get(
                    self.ARXIV_API_URL,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    text = await response.text()
                    return self._parse_arxiv_xml(text)

    async def search_by_title(self, title: str) -> List[dict]:
        """
        Search ArXiv papers by exact title.

        Args:
            title: Paper title to search for

        Returns:
            List of matching papers
        """
        # Use title-specific search query
        search_query = f'ti:"{title}"'

        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                params = {
                    'search_query': search_query,
                    'max_results': 10
                }

                async with session.get(
                    self.ARXIV_API_URL,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    text = await response.text()
                    return self._parse_arxiv_xml(text)

    def _parse_arxiv_xml(self, xml_text: str) -> List[dict]:
        """
        Parse ArXiv API XML response into structured paper data.

        Args:
            xml_text: Raw XML response from ArXiv API

        Returns:
            List of paper dictionaries
        """
        papers = []

        # Define XML namespaces
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }

        try:
            root = ET.fromstring(xml_text)

            # Find all entry elements (papers)
            for entry in root.findall('atom:entry', namespaces):
                paper = {}

                # Extract basic metadata
                title_elem = entry.find('atom:title', namespaces)
                paper['title'] = title_elem.text.strip() if title_elem is not None else ''

                # Extract ArXiv ID
                id_elem = entry.find('atom:id', namespaces)
                if id_elem is not None:
                    arxiv_url = id_elem.text.strip()
                    paper['arxiv_id'] = arxiv_url.split('/')[-1]
                    paper['url'] = arxiv_url

                # Extract abstract
                summary_elem = entry.find('atom:summary', namespaces)
                paper['abstract'] = summary_elem.text.strip() if summary_elem is not None else ''

                # Extract authors
                authors = []
                for author_elem in entry.findall('atom:author', namespaces):
                    name_elem = author_elem.find('atom:name', namespaces)
                    if name_elem is not None:
                        authors.append(name_elem.text.strip())
                paper['authors'] = authors

                # Extract published date
                published_elem = entry.find('atom:published', namespaces)
                if published_elem is not None:
                    published_str = published_elem.text.strip()
                    try:
                        published_date = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                        paper['published_date'] = published_date.isoformat()
                        paper['year'] = published_date.year
                    except ValueError:
                        paper['published_date'] = published_str
                        paper['year'] = None

                # Extract updated date
                updated_elem = entry.find('atom:updated', namespaces)
                if updated_elem is not None:
                    paper['updated_date'] = updated_elem.text.strip()

                # Extract categories
                categories = []
                for category_elem in entry.findall('atom:category', namespaces):
                    term = category_elem.get('term')
                    if term:
                        categories.append(term)
                paper['categories'] = categories

                # Extract primary category
                primary_category_elem = entry.find('arxiv:primary_category', namespaces)
                if primary_category_elem is not None:
                    paper['primary_category'] = primary_category_elem.get('term')

                # Extract PDF link
                for link_elem in entry.findall('atom:link', namespaces):
                    if link_elem.get('title') == 'pdf':
                        paper['pdf_url'] = link_elem.get('href')

                # Extract DOI if available
                doi_elem = entry.find('arxiv:doi', namespaces)
                if doi_elem is not None:
                    paper['doi'] = doi_elem.text.strip()

                # Extract journal reference if available
                journal_elem = entry.find('arxiv:journal_ref', namespaces)
                if journal_elem is not None:
                    paper['journal_ref'] = journal_elem.text.strip()

                # Extract comment if available
                comment_elem = entry.find('arxiv:comment', namespaces)
                if comment_elem is not None:
                    paper['comment'] = comment_elem.text.strip()

                papers.append(paper)

        except ET.ParseError as e:
            # Log parsing error but don't fail
            print(f"Error parsing ArXiv XML: {e}")
            return []

        return papers
