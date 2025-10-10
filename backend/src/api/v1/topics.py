"""Topics API with user management support."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models import Topic, PaperTopicMatch
from ...api.dependencies import get_current_user, get_user_id
from ...jobs.celery_app import celery_app

router = APIRouter(prefix="/topics", tags=["Topics"])


class TopicCreate(BaseModel):
    """Create topic request."""
    name: str
    description: Optional[str] = None
    keywords: List[str]


class TopicUpdate(BaseModel):
    """Update topic request."""
    name: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None


class TopicResponse(BaseModel):
    """Topic response."""
    id: str
    name: str
    description: Optional[str]
    keywords: Optional[List[str]]
    is_system: bool
    user_id: Optional[str]
    created_at: str
    paper_count: int = 0

    class Config:
        from_attributes = True


@router.get("", response_model=List[TopicResponse])
async def list_topics(
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(get_current_user)
):
    """List all topics (system + user's custom topics)."""
    # Build query: system topics OR user's topics
    query = select(Topic)
    if user:
        query = query.where(
            or_(
                Topic.is_system == True,
                Topic.user_id == UUID(user["id"])
            )
        )
    else:
        query = query.where(Topic.is_system == True)

    result = await db.execute(query)
    topics = result.scalars().all()

    # Get paper counts
    response = []
    for topic in topics:
        count_result = await db.execute(
            select(PaperTopicMatch).where(PaperTopicMatch.topic_id == topic.id)
        )
        paper_count = len(count_result.scalars().all())

        response.append(TopicResponse(
            id=str(topic.id),
            name=topic.name,
            description=topic.description,
            keywords=topic.keywords or [],
            is_system=topic.is_system,
            user_id=str(topic.user_id) if topic.user_id else None,
            created_at=topic.created_at.isoformat(),
            paper_count=paper_count
        ))

    return response


@router.post("", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(
    request: TopicCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id)
):
    """Create a custom topic (authenticated users only)."""
    # Check for duplicate name
    existing = await db.execute(
        select(Topic).where(Topic.name == request.name.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic with this name already exists"
        )

    # Create topic
    topic = Topic(
        name=request.name.lower(),
        description=request.description,
        keywords=request.keywords,
        user_id=user_id,
        is_system=False
    )
    db.add(topic)
    await db.commit()
    await db.refresh(topic)

    # Match papers to this new topic immediately
    from ...services import TopicMatchingService
    matching_service = TopicMatchingService(db)

    # Get all papers
    papers_result = await db.execute(select(Paper))
    papers = papers_result.scalars().all()

    # Match each paper against this topic
    matched_count = 0
    for paper in papers:
        try:
            match = await matching_service.match_paper_to_topic(paper, topic)
            if match:
                matched_count += 1
        except Exception as e:
            print(f"Error matching paper {paper.id} to topic {topic.id}: {e}")
            continue

    print(f"Matched {matched_count} papers to new topic '{topic.name}'")

    return TopicResponse(
        id=str(topic.id),
        name=topic.name,
        description=topic.description,
        keywords=topic.keywords,
        is_system=False,
        user_id=str(user_id),
        created_at=topic.created_at.isoformat(),
        paper_count=matched_count
    )


@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: UUID,
    request: TopicUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id)
):
    """Update a custom topic (owner only)."""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    if topic.is_system or topic.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify this topic"
        )

    # Update fields
    if request.name:
        topic.name = request.name.lower()
    if request.description is not None:
        topic.description = request.description
    if request.keywords is not None:
        topic.keywords = request.keywords

    await db.commit()
    await db.refresh(topic)

    # Re-run matching if keywords changed
    if request.keywords:
        celery_app.send_task("match_topics.match_single_topic", args=[str(topic.id)])

    # Get paper count
    count_result = await db.execute(
        select(PaperTopicMatch).where(PaperTopicMatch.topic_id == topic.id)
    )
    paper_count = len(count_result.scalars().all())

    return TopicResponse(
        id=str(topic.id),
        name=topic.name,
        description=topic.description,
        keywords=topic.keywords,
        is_system=False,
        user_id=str(user_id),
        created_at=topic.created_at.isoformat(),
        paper_count=paper_count
    )


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id)
):
    """Delete a custom topic (owner only)."""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    if topic.is_system or topic.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete this topic"
        )

    await db.delete(topic)
    await db.commit()
    return None
