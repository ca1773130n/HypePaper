"""
Citation matching service with fuzzy string matching.

Provides citation parsing and fuzzy matching using Levenshtein distance
to link references to papers in the database.
"""

import asyncio
import json
import os
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from typing import Optional, Dict, Any, List

from rapidfuzz import fuzz


class CitationMatcher:
    """
    Service for parsing citations and matching to papers using fuzzy matching.

    Features:
    - Unicode normalization for robust matching
    - AnyStyle CLI integration for citation parsing
    - Levenshtein distance matching with configurable threshold (default 85%)
    - Year-based matching boost
    """

    def __init__(self, similarity_threshold: int = 85):
        """
        Initialize citation matcher.

        Args:
            similarity_threshold: Minimum similarity score (0-100) for match
        """
        self.threshold = similarity_threshold

    def normalize_title(self, title: str) -> str:
        """
        Normalize title for fuzzy matching.

        Performs:
        - Unicode normalization (NFKD)
        - ASCII conversion
        - Lowercase conversion
        - Whitespace stripping

        Args:
            title: Raw title string

        Returns:
            Normalized title
        """
        # Unicode normalization
        normalized = unicodedata.normalize('NFKD', title)

        # Convert to ASCII (remove accents, special chars)
        ascii_str = ''.join(c for c in normalized if ord(c) < 128)

        # Lowercase and strip
        return ascii_str.lower().strip()

    async def parse_citation(self, citation_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse citation text using AnyStyle CLI.

        AnyStyle is a Ruby gem that parses bibliographic references
        into structured data.

        Args:
            citation_text: Raw citation string

        Returns:
            Dictionary with 'title', 'year', 'authors', etc. or None if parsing fails
        """
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._parse_citation_sync,
            citation_text
        )

    def _parse_citation_sync(self, citation_text: str) -> Optional[Dict[str, Any]]:
        """
        Synchronous citation parsing using AnyStyle CLI.

        Args:
            citation_text: Raw citation string

        Returns:
            Parsed citation dict or None
        """
        # Create temporary file for citation
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(citation_text)
            temp_path = f.name

        try:
            # Call AnyStyle CLI
            result = subprocess.run(
                ['anystyle', 'parse', temp_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout:
                # Parse JSON output
                parsed_list = json.loads(result.stdout)

                if len(parsed_list) > 0:
                    parsed = parsed_list[0]

                    # Extract key fields
                    citation_data = {}

                    # Title (may be array of words)
                    if 'title' in parsed:
                        title_parts = parsed['title']
                        if isinstance(title_parts, list):
                            citation_data['title'] = ' '.join(title_parts)
                        else:
                            citation_data['title'] = str(title_parts)

                    # Year (may be in 'date' field)
                    if 'date' in parsed:
                        date_parts = parsed['date']
                        if isinstance(date_parts, list) and len(date_parts) > 0:
                            try:
                                citation_data['year'] = int(date_parts[0])
                            except (ValueError, TypeError):
                                pass
                        elif isinstance(date_parts, str):
                            try:
                                citation_data['year'] = int(date_parts)
                            except ValueError:
                                pass

                    # Authors
                    if 'author' in parsed:
                        authors = parsed['author']
                        if isinstance(authors, list):
                            citation_data['authors'] = [
                                a.get('family', '') + ', ' + a.get('given', '')
                                if isinstance(a, dict) else str(a)
                                for a in authors
                            ]

                    # Venue/journal
                    if 'container-title' in parsed:
                        citation_data['venue'] = parsed['container-title']

                    return citation_data

        except subprocess.TimeoutExpired:
            print(f"AnyStyle parsing timed out for: {citation_text[:50]}...")
        except json.JSONDecodeError:
            print(f"Failed to parse AnyStyle JSON output")
        except FileNotFoundError:
            print("AnyStyle CLI not found. Install with: gem install anystyle-cli")
        except Exception as e:
            print(f"Citation parsing error: {e}")
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass

        return None

    async def match_citation(
        self,
        citation_text: str,
        papers: List[Any]
    ) -> Optional[Any]:
        """
        Match citation text to a paper in the database using fuzzy matching.

        Args:
            citation_text: Raw citation string
            papers: List of Paper objects to match against

        Returns:
            Best matching Paper object or None
        """
        # Parse citation to extract title and year
        parsed = await self.parse_citation(citation_text)

        if not parsed or 'title' not in parsed:
            return None

        target_title = self.normalize_title(parsed['title'])
        target_year = parsed.get('year')

        best_match = None
        best_score = 0

        # Compare with all papers
        for paper in papers:
            paper_title = self.normalize_title(paper.title)

            # Calculate Levenshtein ratio (0-100)
            title_score = fuzz.ratio(target_title, paper_title)

            # Boost score if years match
            if target_year and hasattr(paper, 'year') and paper.year == target_year:
                title_score = min(100, title_score + 10)

            # Update best match
            if title_score >= self.threshold and title_score > best_score:
                best_score = title_score
                best_match = paper

        return best_match

    async def match_citation_bulk(
        self,
        citations: List[str],
        papers: List[Any]
    ) -> Dict[str, Optional[Any]]:
        """
        Match multiple citations to papers concurrently.

        Args:
            citations: List of citation strings
            papers: List of Paper objects

        Returns:
            Dictionary mapping citation text to matched Paper (or None)
        """
        # Create tasks for parallel processing
        tasks = [
            self.match_citation(citation, papers)
            for citation in citations
        ]

        # Execute in parallel
        results = await asyncio.gather(*tasks)

        # Build result dictionary
        return {
            citation: result
            for citation, result in zip(citations, results)
        }

    def calculate_match_quality(
        self,
        citation_text: str,
        paper_title: str,
        paper_year: Optional[int] = None
    ) -> int:
        """
        Calculate match quality score between citation and paper.

        Args:
            citation_text: Raw citation string
            paper_title: Paper title
            paper_year: Paper publication year (optional)

        Returns:
            Match quality score (0-100)
        """
        # Normalize both titles
        normalized_citation = self.normalize_title(citation_text)
        normalized_paper = self.normalize_title(paper_title)

        # Base score from title similarity
        score = fuzz.ratio(normalized_citation, normalized_paper)

        # Boost if year appears in citation and matches
        if paper_year:
            year_str = str(paper_year)
            if year_str in citation_text:
                score = min(100, score + 10)

        return score
