"""Author extraction service.

Extracts author information from papers and creates Author records.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Paper, Author


class AuthorExtractorService:
    """Service to extract and create author records from papers."""

    async def extract_authors_from_paper(
        self,
        paper: Paper,
        db: AsyncSession
    ) -> list[Author]:
        """Extract authors from a paper and create Author records.

        Args:
            paper: Paper object with authors list
            db: Database session

        Returns:
            List of newly created Author objects
        """
        if not paper.authors:
            return []

        new_authors = []

        for author_name in paper.authors:
            # Check if author already exists
            result = await db.execute(
                select(Author).where(Author.name == author_name)
            )
            existing_author = result.scalar_one_or_none()

            if existing_author:
                # Link existing author to paper via paper_authors table
                if paper not in existing_author.papers:
                    existing_author.papers.append(paper)
                continue

            # Create new author
            author = Author(
                name=author_name,
                # These will be enriched later by other services
                primary_affiliation=None,
                paper_count=0,
                total_citation_count=0
            )

            db.add(author)
            author.papers.append(paper)
            new_authors.append(author)

        return new_authors
