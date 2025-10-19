"""Author service for author lookup and statistics.

Provides search and statistics for paper authors with citation tracking.
"""
from typing import Optional, Sequence
from datetime import date

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.author import Author, PaperAuthor
from src.models.paper import Paper


class AuthorService:
    """Service for managing author data and statistics."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def get_author_by_id(
        self,
        author_id: int,
        include_papers: bool = False
    ) -> Optional[Author]:
        """Get author by ID with optional paper relationships.

        Args:
            author_id: Author ID
            include_papers: Whether to eagerly load papers relationship

        Returns:
            Optional[Author]: Author if found, None otherwise
        """
        query = select(Author).where(Author.id == author_id)

        if include_papers:
            query = query.options(
                selectinload(Author.papers),
                selectinload(Author.latest_paper)
            )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def search_authors(
        self,
        query: str,
        limit: int = 20
    ) -> Sequence[Author]:
        """Search authors by name with full-text search.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            Sequence[Author]: List of matching authors
        """
        # Use PostgreSQL full-text search on name
        stmt = (
            select(Author)
            .where(
                func.to_tsvector("english", Author.name)
                .op("@@")(func.plainto_tsquery("english", query))
            )
            .order_by(desc(Author.paper_count))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_or_create_author(
        self,
        name: str,
        affiliation: Optional[str] = None,
        email: Optional[str] = None,
        website_url: Optional[str] = None
    ) -> Author:
        """Find existing author or create new one.

        For disambiguation: matches by name + primary affiliation if provided.

        Args:
            name: Author full name (normalized)
            affiliation: Primary affiliation (optional)
            email: Author email (optional)
            website_url: Author website (optional)

        Returns:
            Author: Existing or newly created author
        """
        # Try to find by name + affiliation match
        if affiliation:
            result = await self.session.execute(
                select(Author).where(
                    and_(
                        Author.name == name,
                        Author.affiliations.contains([affiliation])
                    )
                )
            )
            author = result.scalar_one_or_none()
            if author:
                return author

        # Try to find by name + email match
        if email:
            result = await self.session.execute(
                select(Author).where(
                    and_(
                        Author.name == name,
                        Author.email == email
                    )
                )
            )
            author = result.scalar_one_or_none()
            if author:
                return author

        # Try to find by name only (first match)
        result = await self.session.execute(
            select(Author).where(Author.name == name).limit(1)
        )
        author = result.scalar_one_or_none()

        if author:
            # Update affiliations if new affiliation provided
            if affiliation and affiliation not in (author.affiliations or []):
                existing_affiliations = author.affiliations or []
                author.affiliations = [affiliation] + existing_affiliations

            # Update email if not set
            if email and not author.email:
                author.email = email

            # Update website_url if not set
            if website_url and not author.website_url:
                author.website_url = website_url

            await self.session.commit()
            await self.session.refresh(author)
            return author
        else:
            # Create new author
            new_author = Author(
                name=name,
                affiliations=[affiliation] if affiliation else None,
                email=email,
                website_url=website_url,
                paper_count=0,
                total_citation_count=0
            )
            self.session.add(new_author)
            await self.session.commit()
            await self.session.refresh(new_author)
            return new_author

    async def update_author_statistics(
        self,
        author_id: int
    ) -> Author:
        """Recalculate author statistics from associated papers.

        Updates:
        - paper_count: Total papers by this author
        - total_citation_count: Sum of citations from all papers
        - latest_paper_id: Most recent paper by published_date

        Args:
            author_id: Author ID to update

        Returns:
            Author: Updated author record
        """
        author = await self.get_author_by_id(author_id, include_papers=True)
        if not author:
            raise ValueError(f"Author not found: {author_id}")

        # Update paper_count
        author.paper_count = len(author.papers)

        # Update total_citation_count
        author.total_citation_count = sum(
            paper.citation_count for paper in author.papers
        )

        # Update latest_paper_id
        if author.papers:
            latest_paper = max(author.papers, key=lambda p: p.published_date)
            author.latest_paper_id = latest_paper.id
        else:
            author.latest_paper_id = None

        await self.session.commit()
        await self.session.refresh(author)
        return author

    async def get_prolific_authors(
        self,
        min_papers: int = 5,
        limit: int = 100
    ) -> Sequence[Author]:
        """Get authors with most papers published.

        Args:
            min_papers: Minimum paper count threshold
            limit: Maximum number of results

        Returns:
            Sequence[Author]: List of prolific authors
        """
        stmt = (
            select(Author)
            .where(Author.paper_count >= min_papers)
            .order_by(desc(Author.paper_count))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_highly_cited_authors(
        self,
        min_citations: int = 100,
        limit: int = 100
    ) -> Sequence[Author]:
        """Get authors with highest total citation counts.

        Args:
            min_citations: Minimum total citation threshold
            limit: Maximum number of results

        Returns:
            Sequence[Author]: List of highly cited authors
        """
        stmt = (
            select(Author)
            .where(Author.total_citation_count >= min_citations)
            .order_by(desc(Author.total_citation_count))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_authors_by_affiliation(
        self,
        affiliation: str,
        limit: int = 100
    ) -> Sequence[Author]:
        """Get authors by affiliation (JSONB containment query).

        Args:
            affiliation: Institution name to search
            limit: Maximum number of results

        Returns:
            Sequence[Author]: List of authors from this institution
        """
        stmt = (
            select(Author)
            .where(Author.affiliations.contains([affiliation]))
            .order_by(desc(Author.paper_count))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()
