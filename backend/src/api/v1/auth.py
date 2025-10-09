"""Authentication endpoints for Supabase integration."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...api.dependencies import get_current_user, get_current_user_required

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    user_metadata: dict


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: dict = Depends(get_current_user_required)
):
    """Get current authenticated user information."""
    return UserResponse(
        id=user["id"],
        email=user["email"],
        user_metadata=user.get("user_metadata", {})
    )


@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token clearing)."""
    return {"message": "Logged out successfully"}
