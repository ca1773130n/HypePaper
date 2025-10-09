"""API package for HypePaper.

Contains all API routers and endpoints.
"""
from .v1 import (
    v1_router,
    papers_router,
    citations_router,
    github_router,
    jobs_router,
)

__all__ = [
    "v1_router",
    "papers_router",
    "citations_router",
    "github_router",
    "jobs_router",
]
