"""arXiv API client for fetching research papers.

Fetches papers by category using the official arXiv API.
Rate limit: 3 requests per second as per arXiv guidelines.
"""
import time
from datetime import date, datetime, timedelta
from typing import Optional
from xml.etree import ElementTree as ET

import httpx


class ArxivClient:
    """Client for interacting with arXiv API."""

    BASE_URL = "http://export.arxiv.org/api/query"
    RATE_LIMIT_DELAY = 0.34  # ~3 requests per second

    def __init__(self):
        """Initialize arXiv client."""
        self.client = httpx.AsyncClient(timeout=30.0)
        self.last_request_time = 0.0

    async def _rate_limit(self):
        """Enforce rate limiting (3 req/s)."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            await self.client.aclose()
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
            self.client = httpx.AsyncClient(timeout=30.0)
        self.last_request_time = time.time()

    async def search_papers(
        self,
        category: str,
        max_results: int = 100,
        start_date: Optional[date] = None,
    ) -> list[dict]:
        """Search papers by category.

        Args:
            category: arXiv category (e.g., "cs.CV", "cs.LG")
            max_results: Maximum number of results (default 100)
            start_date: Filter papers submitted after this date (optional)

        Returns:
            List of paper dictionaries with metadata
        """
        await self._rate_limit()

        # Build query
        query = f"cat:{category}"
        if start_date:
            query += f" AND submittedDate:[{start_date.strftime('%Y%m%d')}* TO *]"

        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        try:
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return self._parse_response(response.text)
        except httpx.HTTPError as e:
            print(f"arXiv API error: {e}")
            return []

    def _parse_response(self, xml_text: str) -> list[dict]:
        """Parse arXiv API XML response.

        Args:
            xml_text: XML response from arXiv API

        Returns:
            List of paper dictionaries
        """
        papers = []
        root = ET.fromstring(xml_text)

        # arXiv uses Atom namespace
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall("atom:entry", ns):
            try:
                # Extract arXiv ID from entry ID
                entry_id = entry.find("atom:id", ns).text
                arxiv_id = entry_id.split("/")[-1]

                # Extract metadata
                title = entry.find("atom:title", ns).text.strip()
                abstract = entry.find("atom:summary", ns).text.strip()

                # Authors
                authors = []
                for author in entry.findall("atom:author", ns):
                    name = author.find("atom:name", ns).text
                    authors.append(name)

                # Published date
                published_str = entry.find("atom:published", ns).text
                published_date = datetime.fromisoformat(
                    published_str.replace("Z", "+00:00")
                ).date()

                # Links
                arxiv_url = entry.find("atom:id", ns).text
                pdf_url = arxiv_url.replace("/abs/", "/pdf/") + ".pdf"

                # Category
                category_elem = entry.find("atom:category", ns)
                category = category_elem.get("term") if category_elem is not None else None

                # DOI (if available)
                doi = None
                for link in entry.findall("atom:link", ns):
                    if link.get("title") == "doi":
                        doi = link.get("href").split("/")[-1]

                papers.append(
                    {
                        "arxiv_id": arxiv_id,
                        "doi": doi,
                        "title": title,
                        "authors": authors,
                        "abstract": abstract,
                        "published_date": published_date,
                        "arxiv_url": arxiv_url,
                        "pdf_url": pdf_url,
                        "category": category,
                    }
                )
            except (AttributeError, ValueError) as e:
                print(f"Error parsing arXiv entry: {e}")
                continue

        return papers

    async def get_recent_papers(
        self, categories: list[str], days: int = 7, max_per_category: int = 50
    ) -> list[dict]:
        """Get recent papers from multiple categories.

        Args:
            categories: List of arXiv categories (e.g., ["cs.CV", "cs.LG"])
            days: Number of days to look back (default 7)
            max_per_category: Max results per category (default 50)

        Returns:
            Combined list of papers from all categories
        """
        start_date = date.today() - timedelta(days=days)
        all_papers = []

        for category in categories:
            papers = await self.search_papers(
                category=category,
                max_results=max_per_category,
                start_date=start_date,
            )
            all_papers.extend(papers)

        # Deduplicate by arXiv ID
        seen_ids = set()
        unique_papers = []
        for paper in all_papers:
            if paper["arxiv_id"] not in seen_ids:
                seen_ids.add(paper["arxiv_id"])
                unique_papers.append(paper)

        return unique_papers

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
