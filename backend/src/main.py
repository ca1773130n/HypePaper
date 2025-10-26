"""FastAPI main application.

Entry point for the HypePaper backend API.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import papers, votes, authors
from .api.v1 import citations, github, health, jobs, auth, admin, topics, papers_enhanced
from .api.v1 import papers as papers_v1
from .middleware.error_handler import ErrorHandlerMiddleware, RequestLoggingMiddleware
from .middleware.security import SecurityHeadersMiddleware
from .services.cache_service import close_cache
from .utils.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    log_level = os.getenv("LOG_LEVEL", "INFO")
    # Only use file logging if LOG_FILE is explicitly set (not in production by default)
    log_file_str = os.getenv("LOG_FILE")
    log_file = Path(log_file_str) if log_file_str else None
    json_format = os.getenv("LOG_JSON", "false").lower() == "true"
    setup_logging(log_level, log_file, json_format)

    yield

    # Shutdown
    await close_cache()


# Create FastAPI app
app = FastAPI(
    title="HypePaper API",
    description="API for tracking trending research papers with GitHub stars and citations",
    version="2.0.0",
    lifespan=lifespan,
)

# Add middleware (order matters - first added = outermost)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS for frontend
# Get allowed origins from environment or use defaults
allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")

# Add production domains if in production environment
if os.getenv("ENVIRONMENT") == "production":
    allowed_origins.extend([
        "https://hypepaper.pages.dev",  # Cloudflare Pages
        "https://*.pages.dev",  # Cloudflare Pages preview deployments
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API routers (new SOTAPapers integration endpoints)
app.include_router(papers_v1.router, prefix="/api/v1")
app.include_router(papers_enhanced.router, prefix="/api/v1")
app.include_router(citations.router, prefix="/api/v1")
app.include_router(github.router, prefix="/api/v1")
app.include_router(jobs.router)  # jobs router already has /api/v1/jobs prefix
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(topics.router, prefix="/api/v1")

# Include legacy routers (for backward compatibility)
app.include_router(papers.router)

# Feature 003: Voting & Enrichment endpoints
app.include_router(votes.router)
app.include_router(authors.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "HypePaper API - Research Paper Tracking with GitHub Stars & Citations",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "metrics": "/api/v1/health/metrics",
    }


@app.get("/health")
async def health_legacy():
    """Legacy health check endpoint."""
    return {"status": "ok"}
