"""PaperService for CRUD operations on papers."""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Paper, PaperTopicMatch


class PaperService:
    """Service for paper-related operations.

    Handles querying, filtering, and sorting papers.
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session

    async def get_papers(
        self,
        topic_id: Optional[UUID] = None,
        sort_by: str = "recency",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Paper], int]:
        """Get papers with optional filtering and sorting.

        Args:
            topic_id: Filter by topic (optional)
            sort_by: Sort option ("hype_score", "recency", "stars")
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            Tuple of (papers list, total count)
        """
        # Build base query
        query = select(Paper)

        # Filter by topic if specified
        if topic_id:
            query = query.join(PaperTopicMatch).where(PaperTopicMatch.topic_id == topic_id)

        # Apply sorting
        if sort_by == "recency":
            query = query.order_by(Paper.published_date.desc())
        elif sort_by == "stars":
            # Sort by GitHub stars (scraped) in descending order
            # Use COALESCE to handle NULL values, putting them at the end
            from sqlalchemy import func
            query = query.order_by(
                func.coalesce(Paper.github_stars_scraped, 0).desc(),
                Paper.published_date.desc()  # Secondary sort for tie-breaking
            )
        elif sort_by == "hype_score":
            # For MVP, we'll sort by published_date as fallback
            # Will be replaced with calculated hype score
            query = query.order_by(Paper.published_date.desc())
        else:
            # Default to recency
            query = query.order_by(Paper.published_date.desc())

        # Get total count (before pagination)
        count_query = select(Paper.id)
        if topic_id:
            count_query = count_query.join(PaperTopicMatch).where(
                PaperTopicMatch.topic_id == topic_id
            )
        total_result = await self.session.execute(count_query)
        total = len(total_result.all())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(query)
        papers = list(result.scalars().all())

        return papers, total

    async def get_paper_by_id(self, paper_id: UUID) -> Optional[Paper]:
        """Get a single paper by ID.

        Args:
            paper_id: Paper UUID

        Returns:
            Paper if found, None otherwise
        """
        query = (
            select(Paper)
            .where(Paper.id == paper_id)
            .options(selectinload(Paper.topic_matches))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_paper(self, paper_data: dict) -> Paper:
        """Create a new paper.

        Args:
            paper_data: Dictionary with paper fields

        Returns:
            Created paper
        """
        paper = Paper(**paper_data)
        self.session.add(paper)
        await self.session.flush()
        return paper

    async def get_paper_by_arxiv_id(self, arxiv_id: str) -> Optional[Paper]:
        """Get paper by arXiv ID.

        Args:
            arxiv_id: arXiv identifier

        Returns:
            Paper if found, None otherwise
        """
        query = select(Paper).where(Paper.arxiv_id == arxiv_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_paper_by_doi(self, doi: str) -> Optional[Paper]:
        """Get paper by DOI.

        Args:
            doi: Digital Object Identifier

        Returns:
            Paper if found, None otherwise
        """
        query = select(Paper).where(Paper.doi == doi)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
