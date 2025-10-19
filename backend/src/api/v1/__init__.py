"""API v1 routers.

SOTAPapers integration endpoints for HypePaper.
"""
from fastapi import APIRouter

from .authors import router as authors_router
from .citations import router as citations_router
from .github import router as github_router
from .health import router as health_router
from .jobs import router as jobs_router
from .papers import router as papers_router

# Create main v1 router
v1_router = APIRouter()

# Include all sub-routers
v1_router.include_router(papers_router)
v1_router.include_router(authors_router)
v1_router.include_router(citations_router)
v1_router.include_router(github_router)
v1_router.include_router(jobs_router)
v1_router.include_router(health_router)

__all__ = [
    "v1_router",
    "papers_router",
    "authors_router",
    "citations_router",
    "github_router",
    "jobs_router",
    "health_router",
]
