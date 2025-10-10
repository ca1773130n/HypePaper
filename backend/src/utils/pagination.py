"""Pagination utilities for API responses."""
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination request parameters."""

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response wrapper."""

    items: List[T] = Field(description="Page items")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create paginated response from query results.

        Args:
            items: Page items
            total: Total number of items
            page: Current page number
            page_size: Items per page

        Returns:
            PaginatedResponse instance
        """
        total_pages = (total + page_size - 1) // page_size  # Ceiling division

        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


async def paginate(
    session: AsyncSession,
    query: Select,
    pagination: PaginationParams,
) -> tuple[List[Any], int]:
    """Execute paginated query.

    Args:
        session: Database session
        query: SQLAlchemy select query
        pagination: Pagination parameters

    Returns:
        Tuple of (items, total_count)
    """
    # Get total count (without pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated items
    paginated_query = query.offset(pagination.offset).limit(pagination.limit)
    result = await session.execute(paginated_query)
    items = result.scalars().all()

    return items, total


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters (for large datasets)."""

    cursor: Optional[str] = Field(
        None, description="Cursor for next page (opaque string)"
    )
    limit: int = Field(20, ge=1, le=100, description="Items per page")


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Cursor-based paginated response."""

    items: List[T] = Field(description="Page items")
    next_cursor: Optional[str] = Field(
        None, description="Cursor for next page (None if no more pages)"
    )
    has_more: bool = Field(description="Whether there are more items")

    @classmethod
    def create(
        cls,
        items: List[T],
        next_cursor: Optional[str],
    ) -> "CursorPaginatedResponse[T]":
        """Create cursor paginated response.

        Args:
            items: Page items
            next_cursor: Cursor for next page (None if no more pages)

        Returns:
            CursorPaginatedResponse instance
        """
        return cls(
            items=items,
            next_cursor=next_cursor,
            has_more=next_cursor is not None,
        )


def encode_cursor(value: Any) -> str:
    """Encode cursor value to opaque string.

    Args:
        value: Cursor value (timestamp, ID, etc.)

    Returns:
        Base64-encoded cursor string
    """
    import base64

    cursor_str = str(value)
    return base64.b64encode(cursor_str.encode()).decode()


def decode_cursor(cursor: str) -> str:
    """Decode cursor string to value.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Decoded cursor value
    """
    import base64

    return base64.b64decode(cursor.encode()).decode()
