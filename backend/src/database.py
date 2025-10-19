"""Database configuration and session management."""
import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from .models import Base

# Load environment variables from .env file
load_dotenv()

# Database URL (will be configured via environment variable)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://hypepaper:hypepaper_dev@localhost:5432/hypepaper")

# Create async engine with connection pooling optimizations
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    future=True,
    pool_size=3,  # Reduced for session pooler
    max_overflow=2,  # Reduced for session pooler
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Timeout for getting connection from pool
    # Disable prepared statements for Supabase transaction pooler
    connect_args={"statement_cache_size": 0},
    # Use NullPool only for testing environments
    poolclass=NullPool if os.getenv("TESTING") == "1" else None,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


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


async def init_db() -> None:
    """Initialize database tables.

    Creates all tables defined in models.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
