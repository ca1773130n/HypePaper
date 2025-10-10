"""TopicService for CRUD operations on topics."""
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import PaperTopicMatch, Topic


class TopicService:
    """Service for topic-related operations.

    Handles querying topics and calculating paper counts.
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session

    async def get_all_topics(self) -> list[dict]:
        """Get all topics with paper counts.

        Returns:
            List of topic dictionaries with paper_count
        """
        # Query topics with paper counts
        query = (
            select(
                Topic,
                func.count(PaperTopicMatch.id).label("paper_count"),
            )
            .outerjoin(PaperTopicMatch, Topic.id == PaperTopicMatch.topic_id)
            .group_by(Topic.id)
            .order_by(Topic.name)
        )

        result = await self.session.execute(query)
        rows = result.all()

        # Convert to dictionaries
        topics = []
        for topic, paper_count in rows:
            topics.append(
                {
                    "id": str(topic.id),
                    "name": topic.name,
                    "description": topic.description,
                    "paper_count": paper_count,
                    "created_at": topic.created_at.isoformat(),
                }
            )

        return topics

    async def get_topic_by_id(self, topic_id: UUID) -> Optional[Topic]:
        """Get a single topic by ID.

        Args:
            topic_id: Topic UUID

        Returns:
            Topic if found, None otherwise
        """
        query = select(Topic).where(Topic.id == topic_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_topic_by_name(self, name: str) -> Optional[Topic]:
        """Get topic by name.

        Args:
            name: Topic name (case-insensitive)

        Returns:
            Topic if found, None otherwise
        """
        query = select(Topic).where(Topic.name == name.lower())
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_topic(self, topic_data: dict) -> Topic:
        """Create a new topic.

        Args:
            topic_data: Dictionary with topic fields

        Returns:
            Created topic
        """
        # Ensure name is lowercase
        topic_data["name"] = topic_data["name"].lower()

        topic = Topic(**topic_data)
        self.session.add(topic)
        await self.session.flush()
        return topic

    async def get_paper_count(self, topic_id: UUID) -> int:
        """Get count of papers for a topic.

        Args:
            topic_id: Topic UUID

        Returns:
            Number of papers matched to this topic
        """
        query = select(func.count(PaperTopicMatch.id)).where(
            PaperTopicMatch.topic_id == topic_id
        )
        result = await self.session.execute(query)
        count = result.scalar_one()
        return count
