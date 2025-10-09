"""Shared dependencies for API routes."""
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import AsyncSessionLocal

security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency for FastAPI.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """Get current authenticated user (placeholder for future auth).

    Args:
        credentials: Bearer token credentials

    Returns:
        User info dict or None if not authenticated

    Note:
        This is a placeholder. Authentication will be implemented in a future PR.
        For now, it returns None (no authentication required).
    """
    # TODO: Implement JWT token verification
    # For now, return None (no auth required)
    return None


async def get_current_active_user(
    current_user: Optional[dict] = Depends(get_current_user)
) -> Optional[dict]:
    """Get current active user (requires authentication).

    Args:
        current_user: Current user from get_current_user

    Returns:
        User info dict

    Raises:
        HTTPException: 401 if not authenticated

    Note:
        This is a placeholder. For now it allows unauthenticated access.
    """
    # TODO: Uncomment when authentication is implemented
    # if current_user is None:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Not authenticated",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    return current_user
