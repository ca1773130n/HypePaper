"""Citation counter service using scholarly library.

Extracts citation counts from Google Scholar.
"""
import asyncio
from typing import Optional


class CitationCounter:
    """Count citations for research papers using Google Scholar."""

    def __init__(self):
        """Initialize citation counter."""
        self._scholarly = None

    async def _init_scholarly(self):
        """Lazy init scholarly (blocking operation)."""
        if self._scholarly is None:
            try:
                from scholarly import scholarly
                self._scholarly = scholarly
            except ImportError:
                print("scholarly library not installed, citation counting disabled")
                self._scholarly = False

    async def get_citation_count(self, title: str) -> Optional[int]:
        """
        Get citation count for a paper by its title.

        Args:
            title: Paper title

        Returns:
            Number of citations or None if not found
        """
        await self._init_scholarly()

        if not self._scholarly:
            return None

        try:
            # Run blocking scholarly operation in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._search_title_sync(title)
            )
            return result
        except Exception as e:
            print(f"Error getting citation count: {e}")
            return None

    def _search_title_sync(self, title: str) -> Optional[int]:
        """Synchronous search for title."""
        try:
            query = self._scholarly.search_pubs(title)
            for result in query:
                # Check if title matches (allowing some tolerance)
                result_title = result.get('bib', {}).get('title', '')
                if self._titles_match(result_title, title):
                    return result.get('num_citations', 0)
            return None
        except Exception as e:
            print(f"Error in scholarly search: {e}")
            return None

    def _titles_match(self, title1: str, title2: str, tolerance: int = 5) -> bool:
        """
        Check if two titles match with some character tolerance.

        Args:
            title1: First title
            title2: Second title
            tolerance: Number of characters that can differ

        Returns:
            True if titles match within tolerance
        """
        # Normalize titles
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()

        # Remove common punctuation
        for char in '.,;:!?()-[]{}"\'/':
            t1 = t1.replace(char, '')
            t2 = t2.replace(char, '')

        # Calculate Levenshtein-like difference
        if abs(len(t1) - len(t2)) > tolerance:
            return False

        # Simple character-by-character comparison
        diff = sum(1 for a, b in zip(t1, t2) if a != b)
        diff += abs(len(t1) - len(t2))

        return diff <= tolerance
