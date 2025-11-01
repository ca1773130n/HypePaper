"""User profile service for managing user accounts and settings."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.user_profile import UserProfile
from ..models.crawler_job import CrawlerJob
from ..models.topic import Topic


class UserProfileService:
    """Service for user profile operations."""

    @staticmethod
    async def get_or_create_profile(
        db: AsyncSession,
        user_id: UUID,
        email: str,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> UserProfile:
        """Get existing profile or create new one from Google Auth.

        Args:
            db: Database session
            user_id: User UUID from Supabase auth.users.id
            email: User email from Google Auth
            display_name: Display name from Google profile
            avatar_url: Avatar URL from Google profile

        Returns:
            UserProfile: User profile instance
        """
        # Try to get existing profile
        result = await db.execute(
            select(UserProfile).where(UserProfile.id == user_id)
        )
        profile = result.scalar_one_or_none()

        if profile:
            # Update last login
            profile.last_login_at = datetime.utcnow()

            # Update profile info if changed
            if email and profile.email != email:
                profile.email = email
            if display_name and profile.display_name != display_name:
                profile.display_name = display_name
            if avatar_url and profile.avatar_url != avatar_url:
                profile.avatar_url = avatar_url

            profile.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(profile)
        else:
            # Create new profile
            profile = UserProfile(
                id=user_id,
                email=email,
                display_name=display_name,
                avatar_url=avatar_url,
                last_login_at=datetime.utcnow(),
            )
            db.add(profile)
            await db.commit()
            await db.refresh(profile)

        return profile

    @staticmethod
    async def get_profile(
        db: AsyncSession,
        user_id: UUID,
        include_jobs: bool = False,
        include_topics: bool = False,
    ) -> Optional[UserProfile]:
        """Get user profile by ID.

        Args:
            db: Database session
            user_id: User UUID
            include_jobs: Whether to load crawler jobs
            include_topics: Whether to load custom topics

        Returns:
            UserProfile or None if not found
        """
        stmt = select(UserProfile).where(UserProfile.id == user_id)

        # Eager load relationships if requested
        if include_jobs:
            stmt = stmt.options(selectinload(UserProfile.crawler_jobs))
        if include_topics:
            stmt = stmt.options(selectinload(UserProfile.custom_topics))

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_profile_by_email(
        db: AsyncSession,
        email: str,
    ) -> Optional[UserProfile]:
        """Get user profile by email.

        Args:
            db: Database session
            email: User email address

        Returns:
            UserProfile or None if not found
        """
        result = await db.execute(
            select(UserProfile).where(UserProfile.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        user_id: UUID,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        preferences: Optional[dict] = None,
    ) -> Optional[UserProfile]:
        """Update user profile.

        Args:
            db: Database session
            user_id: User UUID
            display_name: New display name
            avatar_url: New avatar URL
            preferences: User preferences dict

        Returns:
            Updated UserProfile or None if not found
        """
        profile = await UserProfileService.get_profile(db, user_id)
        if not profile:
            return None

        # Update fields if provided
        if display_name is not None:
            profile.display_name = display_name
        if avatar_url is not None:
            profile.avatar_url = avatar_url
        if preferences is not None:
            profile.preferences = preferences

        profile.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(profile)

        return profile

    @staticmethod
    async def update_preferences(
        db: AsyncSession,
        user_id: UUID,
        preferences: dict,
        merge: bool = True,
    ) -> Optional[UserProfile]:
        """Update user preferences.

        Args:
            db: Database session
            user_id: User UUID
            preferences: Preferences dict
            merge: If True, merge with existing preferences; if False, replace

        Returns:
            Updated UserProfile or None if not found
        """
        profile = await UserProfileService.get_profile(db, user_id)
        if not profile:
            return None

        if merge:
            # Merge with existing preferences
            current_prefs = profile.preferences or {}
            profile.preferences = {**current_prefs, **preferences}
        else:
            # Replace preferences entirely
            profile.preferences = preferences

        profile.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(profile)

        return profile

    @staticmethod
    async def delete_profile(
        db: AsyncSession,
        user_id: UUID,
    ) -> bool:
        """Delete user profile.

        This will cascade delete all related data:
        - Crawler jobs
        - Custom topics

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            True if deleted, False if not found
        """
        profile = await UserProfileService.get_profile(db, user_id)
        if not profile:
            return False

        await db.delete(profile)
        await db.commit()
        return True

    @staticmethod
    async def get_user_crawler_jobs(
        db: AsyncSession,
        user_id: UUID,
        status: Optional[str] = None,
    ) -> list[CrawlerJob]:
        """Get user's crawler jobs.

        Args:
            db: Database session
            user_id: User UUID
            status: Filter by status (processing, completed, failed)

        Returns:
            List of crawler jobs
        """
        stmt = select(CrawlerJob).where(CrawlerJob.user_id == user_id)

        if status:
            stmt = stmt.where(CrawlerJob.status == status)

        stmt = stmt.order_by(CrawlerJob.created_at.desc())

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_user_custom_topics(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[Topic]:
        """Get user's custom topics.

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            List of custom topics
        """
        result = await db.execute(
            select(Topic)
            .where(Topic.user_id == user_id)
            .order_by(Topic.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_user_stats(
        db: AsyncSession,
        user_id: UUID,
    ) -> dict:
        """Get user statistics.

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            Dict with user stats
        """
        profile = await UserProfileService.get_profile(
            db, user_id, include_jobs=True, include_topics=True
        )
        if not profile:
            return {}

        # Count jobs by status
        active_jobs = len(profile.active_crawler_jobs)
        inactive_jobs = len(profile.inactive_crawler_jobs)
        total_jobs = len(profile.crawler_jobs)

        # Count custom topics
        custom_topics = len(profile.custom_topics)

        return {
            "total_crawler_jobs": total_jobs,
            "active_crawler_jobs": active_jobs,
            "inactive_crawler_jobs": inactive_jobs,
            "custom_topics": custom_topics,
            "member_since": profile.created_at.isoformat(),
            "last_login": profile.last_login_at.isoformat() if profile.last_login_at else None,
        }
