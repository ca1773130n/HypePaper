"""Topic model for research areas.

Represents research domains that users can watch.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Topic(Base):
    """Research topic/area entity.

    Fields:
    - id: Internal UUID identifier
    - name: Topic name (3-100 chars, lowercase, unique)
    - description: Optional detailed description
    - keywords: Related keywords for matching
    - is_system: Whether this is a system topic (vs user-created)
    - user_id: User ID if custom topic (null for system topics)
    - created_at: Topic creation timestamp

    Constraints:
    - Name must be 3-100 characters, lowercase, alphanumeric + spaces/hyphens
    - Name must be unique
    - Each keyword: 2-50 characters

    Note: System topics are predefined and available to all users.
    Users can also create custom topics.
    """

    __tablename__ = "topics"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Core fields
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keywords: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), nullable=False
    )

    # Relationships
    paper_matches: Mapped[list["PaperTopicMatch"]] = relationship(
        "PaperTopicMatch", back_populates="topic", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "LENGTH(name) >= 3 AND LENGTH(name) <= 100",
            name="topic_name_length_valid",
        ),
        CheckConstraint(
            "name = LOWER(name)",
            name="topic_name_lowercase",
        ),
        CheckConstraint(
            "name ~ '^[a-z0-9 -]+$'",
            name="topic_name_format_valid",
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Topic({self.name})>"
