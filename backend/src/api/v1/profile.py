"""User profile API endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from ...services.user_profile_service import UserProfileService
from ...database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/profile", tags=["User Profile"])


# Request/Response Models


class UserProfileResponse(BaseModel):
    """User profile response model."""

    id: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: dict = {}
    created_at: str
    updated_at: str
    last_login_at: Optional[str] = None

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    """Update profile request model."""

    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UpdatePreferencesRequest(BaseModel):
    """Update preferences request model."""

    preferences: dict
    merge: bool = True


class CrawlerJobResponse(BaseModel):
    """Crawler job response model."""

    id: str
    job_id: str
    status: str
    source_type: str
    keywords: Optional[str] = None
    papers_crawled: int
    references_crawled: int
    started_at: str
    completed_at: Optional[str] = None

    class Config:
        from_attributes = True


class TopicResponse(BaseModel):
    """Topic response model."""

    id: str
    name: str
    description: Optional[str] = None
    keywords: Optional[list[str]] = None
    is_system: bool
    created_at: str

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """User statistics response model."""

    total_crawler_jobs: int
    active_crawler_jobs: int
    inactive_crawler_jobs: int
    custom_topics: int
    member_since: str
    last_login: Optional[str] = None


# API Endpoints


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's profile.

    Requires authentication. Returns the authenticated user's profile.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user_id = UUID(current_user["id"])
    profile = await UserProfileService.get_profile(db, user_id)

    if not profile:
        # Auto-create profile from auth data
        profile = await UserProfileService.get_or_create_profile(
            db=db,
            user_id=user_id,
            email=current_user.get("email", ""),
            display_name=current_user.get("user_metadata", {}).get("name"),
            avatar_url=current_user.get("user_metadata", {}).get("avatar_url"),
        )

    return UserProfileResponse(
        id=str(profile.id),
        email=profile.email,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        preferences=profile.preferences,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
        last_login_at=profile.last_login_at.isoformat() if profile.last_login_at else None,
    )


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile.

    Requires authentication. Updates display name and/or avatar URL.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user_id = UUID(current_user["id"])
    profile = await UserProfileService.update_profile(
        db=db,
        user_id=user_id,
        display_name=request.display_name,
        avatar_url=request.avatar_url,
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return UserProfileResponse(
        id=str(profile.id),
        email=profile.email,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        preferences=profile.preferences,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
        last_login_at=profile.last_login_at.isoformat() if profile.last_login_at else None,
    )


@router.put("/me/preferences", response_model=UserProfileResponse)
async def update_my_preferences(
    request: UpdatePreferencesRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's preferences.

    Requires authentication. Merges or replaces preferences based on 'merge' flag.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user_id = UUID(current_user["id"])
    profile = await UserProfileService.update_preferences(
        db=db,
        user_id=user_id,
        preferences=request.preferences,
        merge=request.merge,
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return UserProfileResponse(
        id=str(profile.id),
        email=profile.email,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        preferences=profile.preferences,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
        last_login_at=profile.last_login_at.isoformat() if profile.last_login_at else None,
    )


@router.get("/me/crawler-jobs", response_model=list[CrawlerJobResponse])
async def get_my_crawler_jobs(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's crawler jobs.

    Requires authentication. Optionally filter by status.

    Args:
        status: Filter by status (processing, completed, failed)
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user_id = UUID(current_user["id"])
    jobs = await UserProfileService.get_user_crawler_jobs(db, user_id, status)

    return [
        CrawlerJobResponse(
            id=str(job.id),
            job_id=job.job_id,
            status=job.status,
            source_type=job.source_type,
            keywords=job.keywords,
            papers_crawled=job.papers_crawled,
            references_crawled=job.references_crawled,
            started_at=job.started_at.isoformat(),
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )
        for job in jobs
    ]


@router.get("/me/topics", response_model=list[TopicResponse])
async def get_my_topics(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's custom topics.

    Requires authentication. Returns only topics created by the user.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user_id = UUID(current_user["id"])
    topics = await UserProfileService.get_user_custom_topics(db, user_id)

    return [
        TopicResponse(
            id=str(topic.id),
            name=topic.name,
            description=topic.description,
            keywords=topic.keywords,
            is_system=topic.is_system,
            created_at=topic.created_at.isoformat(),
        )
        for topic in topics
    ]


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_my_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's statistics.

    Requires authentication. Returns activity stats and usage metrics.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user_id = UUID(current_user["id"])
    stats = await UserProfileService.get_user_stats(db, user_id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return UserStatsResponse(**stats)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete current user's profile.

    Requires authentication. This will CASCADE delete all related data:
    - Crawler jobs
    - Custom topics

    This action cannot be undone.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user_id = UUID(current_user["id"])
    deleted = await UserProfileService.delete_profile(db, user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return None
