"""Vote API endpoints.

Provides endpoints for casting, removing, and querying votes on papers.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.services.vote_service import VoteService
from src.models.paper import Paper


router = APIRouter(prefix="/api/papers", tags=["votes"])


# Request/Response models
class VoteRequest(BaseModel):
    """Request body for casting a vote."""
    vote_type: str = Field(..., pattern="^(upvote|downvote)$", description="Vote type: upvote or downvote")


class VoteResponse(BaseModel):
    """Response after casting or updating a vote."""
    vote_type: str
    vote_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VoteStatusResponse(BaseModel):
    """Response for checking user's vote status on a paper."""
    has_voted: bool
    vote_type: Optional[str] = None


# Dependency: Get authenticated user ID from Supabase JWT
# TODO: Implement proper Supabase JWT authentication
async def get_current_user_id() -> UUID:
    """Extract user ID from Supabase JWT token.

    TODO: Implement proper JWT validation with Supabase.
    For now, returns a test UUID.
    """
    # Placeholder - will be replaced with actual JWT validation
    return UUID("00000000-0000-0000-0000-000000000001")


@router.post(
    "/{paper_id}/vote",
    response_model=VoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Cast or update vote on paper"
)
async def cast_vote(
    paper_id: UUID,
    vote_request: VoteRequest,
    session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """Cast or update a vote on a paper.

    - If user has no existing vote, creates a new vote
    - If user has existing vote, updates the vote_type
    - Paper.vote_count is automatically updated by database trigger

    Args:
        paper_id: Paper UUID
        vote_request: Vote request containing vote_type
        session: Database session
        user_id: Authenticated user ID from JWT

    Returns:
        VoteResponse with vote details and updated vote_count

    Raises:
        404: Paper not found
        400: Invalid vote_type
    """
    vote_service = VoteService(session)

    try:
        vote = await vote_service.cast_vote(
            user_id=user_id,
            paper_id=paper_id,
            vote_type=vote_request.vote_type
        )

        # Fetch updated paper vote_count
        paper = await session.get(Paper, paper_id)

        return VoteResponse(
            vote_type=vote.vote_type,
            vote_count=paper.vote_count,
            created_at=vote.created_at,
            updated_at=vote.updated_at
        )

    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paper not found: {paper_id}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


@router.delete(
    "/{paper_id}/vote",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove vote from paper"
)
async def remove_vote(
    paper_id: UUID,
    session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """Remove user's vote from a paper.

    - If user has no vote, returns 204 (idempotent)
    - Paper.vote_count is automatically updated by database trigger

    Args:
        paper_id: Paper UUID
        session: Database session
        user_id: Authenticated user ID from JWT

    Returns:
        204 No Content
    """
    vote_service = VoteService(session)
    await vote_service.remove_vote(user_id=user_id, paper_id=paper_id)
    return None


@router.get(
    "/{paper_id}/vote",
    response_model=VoteStatusResponse,
    summary="Get user's vote status on paper"
)
async def get_vote_status(
    paper_id: UUID,
    session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """Get authenticated user's vote status on a paper.

    Used by frontend to show current vote state in UI.

    Args:
        paper_id: Paper UUID
        session: Database session
        user_id: Authenticated user ID from JWT

    Returns:
        VoteStatusResponse indicating if user voted and vote type
    """
    vote_service = VoteService(session)
    vote = await vote_service.get_user_vote(user_id=user_id, paper_id=paper_id)

    if vote:
        return VoteStatusResponse(
            has_voted=True,
            vote_type=vote.vote_type
        )
    else:
        return VoteStatusResponse(
            has_voted=False,
            vote_type=None
        )
