"""Topics API routes.

Endpoints for managing and querying research topics.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..services import TopicService

router = APIRouter(prefix="/api/v1/topics", tags=["topics"])


# Response models
class TopicResponse(BaseModel):
    """Topic response schema."""

    id: str
    name: str
    description: Optional[str] = None
    keywords: Optional[list[str]] = None
    paper_count: int
    created_at: str

    class Config:
        """Pydantic config."""
        from_attributes = True


class TopicsListResponse(BaseModel):
    """Topics list response schema."""

    topics: list[TopicResponse]
    total: int


class TopicDetailResponse(BaseModel):
    """Topic detail response schema."""

    id: str
    name: str
    description: Optional[str] = None
    keywords: Optional[list[str]] = None
    created_at: str

    class Config:
        """Pydantic config."""
        from_attributes = True


# Import database session dependency
from ..database import get_db


@router.get("", response_model=TopicsListResponse)
async def get_topics(
    db: AsyncSession = Depends(get_db),
) -> TopicsListResponse:
    """Get all topics with paper counts.

    Returns:
        TopicsListResponse with topics array and total count
    """
    topic_service = TopicService(db)
    topics = await topic_service.get_all_topics()

    return TopicsListResponse(
        topics=[TopicResponse(**topic) for topic in topics],
        total=len(topics),
    )


@router.get("/{topic_id}", response_model=TopicDetailResponse)
async def get_topic_by_id(
    topic_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TopicDetailResponse:
    """Get a single topic by ID.

    Args:
        topic_id: Topic UUID

    Returns:
        TopicDetailResponse

    Raises:
        HTTPException: 404 if topic not found
    """
    topic_service = TopicService(db)
    topic = await topic_service.get_topic_by_id(topic_id)

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    return TopicDetailResponse(
        id=str(topic.id),
        name=topic.name,
        description=topic.description,
        keywords=topic.keywords,
        created_at=topic.created_at.isoformat(),
    )
