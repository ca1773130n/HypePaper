"""FastAPI dependencies for authentication and database."""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..utils.supabase_client import get_supabase_client

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Get current user from Supabase JWT token.

    Args:
        credentials: HTTP Authorization header with Bearer token

    Returns:
        User dict with 'id', 'email', etc. or None if no credentials

    Raises:
        HTTPException: If token is invalid
    """
    if credentials is None:
        return None

    try:
        supabase = get_supabase_client()
        user = supabase.auth.get_user(credentials.credentials)

        if not user or not user.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        return {
            "id": user.user.id,
            "email": user.user.email,
            "user_metadata": user.user.user_metadata,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
        )


async def get_current_user_required(
    user: Optional[dict] = Depends(get_current_user),
) -> dict:
    """Require authenticated user (raise 401 if not authenticated).

    Args:
        user: Current user from get_current_user

    Returns:
        User dict

    Raises:
        HTTPException: If user is not authenticated
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


def get_user_id(user: dict = Depends(get_current_user_required)) -> UUID:
    """Extract user ID from authenticated user.

    Args:
        user: Authenticated user dict

    Returns:
        User ID as UUID
    """
    return UUID(user["id"])
