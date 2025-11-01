"""User profile model for Google Auth users.

Represents user accounts from Supabase Google Auth.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .crawler_job import CrawlerJob
    from .topic import Topic


class UserProfile(Base):
    """User profile from Google Auth.

    This table stores user information from Supabase Google Authentication.
    The primary key (id) comes directly from Supabase auth.users.id.

    Fields:
    - id: UUID from Supabase auth.users.id (primary key)
    - email: User's email address from Google Auth
    - display_name: User's display name (from Google profile or custom)
    - avatar_url: Profile picture URL
    - preferences: JSONB field for user preferences and settings
    - created_at: When the profile was created
    - updated_at: Last profile update timestamp
    - last_login_at: Last login timestamp

    Relationships:
    - crawler_jobs: User's crawler jobs (active and inactive)
    - custom_topics: User-created custom topics

    Usage:
    - User ID comes from Supabase auth.users.id (Google Auth UUID)
    - Crawler jobs can be filtered by user_id and status
    - Custom topics are linked via topics.user_id foreign key
    """

    __tablename__ = "user_profiles"

    # Primary key (from Supabase auth.users.id)
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        comment="User UUID from Google Auth (Supabase auth.users.id)"
    )

    # User information
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address from Google Auth"
    )

    display_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="User display name"
    )

    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="User avatar/profile picture URL"
    )

    # Preferences and settings
    preferences: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default='{}',
        comment="User preferences and settings (JSONB)"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
        comment="Profile creation timestamp"
    )

    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
        comment="Last profile update timestamp"
    )

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Last login timestamp"
    )

    # ============================================================
    # RELATIONSHIPS
    # ============================================================

    # User's crawler jobs
    crawler_jobs: Mapped[list["CrawlerJob"]] = relationship(
        "CrawlerJob",
        back_populates="user",
        cascade="all, delete-orphan",
        doc="User's crawler jobs (both active and inactive)"
    )

    # User's custom topics
    custom_topics: Mapped[list["Topic"]] = relationship(
        "Topic",
        back_populates="creator",
        foreign_keys="Topic.user_id",
        cascade="all, delete-orphan",
        doc="Custom topics created by this user"
    )

    # ============================================================
    # COMPUTED PROPERTIES
    # ============================================================

    @property
    def active_crawler_jobs(self) -> list["CrawlerJob"]:
        """Get only active crawler jobs."""
        return [job for job in self.crawler_jobs if job.status == "processing"]

    @property
    def inactive_crawler_jobs(self) -> list["CrawlerJob"]:
        """Get inactive crawler jobs (completed or failed)."""
        return [job for job in self.crawler_jobs if job.status in ("completed", "failed")]

    @property
    def crawler_job_count(self) -> dict[str, int]:
        """Count crawler jobs by status."""
        return {
            "active": len(self.active_crawler_jobs),
            "inactive": len(self.inactive_crawler_jobs),
            "total": len(self.crawler_jobs)
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserProfile({self.email})>"
