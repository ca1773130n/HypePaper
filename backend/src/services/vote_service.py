"""Vote service for managing user votes on papers.

Provides CRUD operations for upvoting/downvoting papers with vote_count
automatically maintained by database trigger.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.vote import Vote
from src.models.paper import Paper


class VoteService:
    """Service for managing user votes on papers."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def cast_vote(
        self,
        user_id: UUID,
        paper_id: UUID,
        vote_type: str
    ) -> Vote:
        """Cast or update a vote on a paper.

        Args:
            user_id: User ID from auth.users
            paper_id: Paper ID
            vote_type: Either "upvote" or "downvote"

        Returns:
            Vote: The created or updated vote record

        Raises:
            ValueError: If vote_type is invalid or paper doesn't exist
        """
        # Validate vote_type
        if vote_type not in ("upvote", "downvote"):
            raise ValueError(f"Invalid vote_type: {vote_type}. Must be 'upvote' or 'downvote'")

        # Verify paper exists
        paper_result = await self.session.execute(
            select(Paper).where(Paper.id == paper_id)
        )
        paper = paper_result.scalar_one_or_none()
        if not paper:
            raise ValueError(f"Paper not found: {paper_id}")

        # Check for existing vote
        existing_vote_result = await self.session.execute(
            select(Vote).where(
                and_(
                    Vote.user_id == user_id,
                    Vote.paper_id == paper_id
                )
            )
        )
        existing_vote = existing_vote_result.scalar_one_or_none()

        if existing_vote:
            # Update existing vote
            existing_vote.vote_type = vote_type
            await self.session.commit()
            await self.session.refresh(existing_vote)
            return existing_vote
        else:
            # Create new vote
            new_vote = Vote(
                user_id=user_id,
                paper_id=paper_id,
                vote_type=vote_type
            )
            self.session.add(new_vote)
            await self.session.commit()
            await self.session.refresh(new_vote)
            return new_vote

    async def remove_vote(
        self,
        user_id: UUID,
        paper_id: UUID
    ) -> bool:
        """Remove a user's vote from a paper.

        Args:
            user_id: User ID from auth.users
            paper_id: Paper ID

        Returns:
            bool: True if vote was removed, False if no vote existed
        """
        # Find existing vote
        existing_vote_result = await self.session.execute(
            select(Vote).where(
                and_(
                    Vote.user_id == user_id,
                    Vote.paper_id == paper_id
                )
            )
        )
        existing_vote = existing_vote_result.scalar_one_or_none()

        if existing_vote:
            await self.session.delete(existing_vote)
            await self.session.commit()
            return True
        else:
            return False

    async def get_user_vote(
        self,
        user_id: UUID,
        paper_id: UUID
    ) -> Optional[Vote]:
        """Get a user's vote on a specific paper.

        Args:
            user_id: User ID from auth.users
            paper_id: Paper ID

        Returns:
            Optional[Vote]: The vote record if exists, None otherwise
        """
        result = await self.session.execute(
            select(Vote).where(
                and_(
                    Vote.user_id == user_id,
                    Vote.paper_id == paper_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_paper_votes(
        self,
        paper_id: UUID
    ) -> tuple[int, int, int]:
        """Get vote statistics for a paper.

        Args:
            paper_id: Paper ID

        Returns:
            tuple[int, int, int]: (upvotes, downvotes, net_votes)
        """
        # Query all votes for this paper
        result = await self.session.execute(
            select(Vote).where(Vote.paper_id == paper_id)
        )
        votes = result.scalars().all()

        upvotes = sum(1 for v in votes if v.vote_type == "upvote")
        downvotes = sum(1 for v in votes if v.vote_type == "downvote")
        net_votes = upvotes - downvotes

        return (upvotes, downvotes, net_votes)

    async def get_user_votes_for_papers(
        self,
        user_id: UUID,
        paper_ids: list[UUID]
    ) -> dict[UUID, str]:
        """Get user's votes for multiple papers (for UI state).

        Args:
            user_id: User ID from auth.users
            paper_ids: List of paper IDs to check

        Returns:
            dict[UUID, str]: Mapping of paper_id → vote_type for papers the user voted on
        """
        if not paper_ids:
            return {}

        result = await self.session.execute(
            select(Vote).where(
                and_(
                    Vote.user_id == user_id,
                    Vote.paper_id.in_(paper_ids)
                )
            )
        )
        votes = result.scalars().all()

        return {vote.paper_id: vote.vote_type for vote in votes}
