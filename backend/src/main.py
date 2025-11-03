"""FastAPI main application.

Entry point for the HypePaper backend API.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .api import papers, votes, authors
from .api.v1 import citations, github, health, jobs, auth, admin, topics, papers_enhanced, profile, async_jobs
from .api.v1 import papers as papers_v1
from .middleware.error_handler import ErrorHandlerMiddleware, RequestLoggingMiddleware
from .middleware.security import SecurityHeadersMiddleware
from .middleware.rate_limiter import RateLimiterMiddleware
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

# Health check endpoint (MUST be defined BEFORE middleware to bypass rate limiting)
# This ensures Railway health checks always succeed even during high load
@app.get("/health")
async def railway_health_check():
    """Railway health check endpoint - bypasses all middleware for reliability."""
    return {"status": "healthy", "service": "hypepaper-api"}

# Add middleware (order matters - first added = outermost)
app.add_middleware(RateLimiterMiddleware, requests_per_minute=60, requests_per_hour=1000)
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
        "https://hypepaper.app",
        "https://www.hypepaper.app",
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
app.include_router(profile.router, prefix="/api")  # profile router has /profile, we add /api
app.include_router(async_jobs.router, prefix="/api")  # async_jobs router has /async-jobs, we add /api

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
        "health": "/health",
        "health_detailed": "/api/v1/health",
        "metrics": "/api/v1/health/metrics",
    }


@app.get("/oauth/redirect-proxy")
async def oauth_redirect_proxy(request: Request):
    """
    OAuth redirect proxy for Railway preview deployments.

    This endpoint provides a stable redirect URI for Google OAuth that works
    with Railway's dynamic preview deployment URLs.

    The frontend URL is determined based on:
    - Production: Uses configured production frontend URL
    - Preview: Uses RAILWAY_STATIC_URL for PR preview deployments
    - Development: Falls back to localhost

    Google OAuth Configuration:
    Add this single redirect URI to your Google OAuth client:
    - https://api.hypepaper.app/oauth/redirect-proxy
    - https://your-railway-backend.up.railway.app/oauth/redirect-proxy

    This eliminates the need to add each preview deployment URL to Google OAuth.
    """
    from fastapi.responses import RedirectResponse
    import urllib.parse

    # Get OAuth parameters from hash fragment or query string
    # Note: Hash fragments (#) are not sent to server, so we rely on query params
    # The frontend should convert hash to query when using this proxy
    request_url = str(request.url)

    # Determine frontend URL based on environment
    railway_env = os.getenv("RAILWAY_ENVIRONMENT_NAME", "")
    railway_static_url = os.getenv("RAILWAY_STATIC_URL", "")

    if railway_env.startswith("pr-"):
        # Railway preview deployment
        # Frontend preview URL pattern: https://<service>-<pr>-<hash>.railway.app
        if railway_static_url:
            frontend_url = f"https://{railway_static_url}"
        else:
            # Fallback: try to construct from backend URL
            backend_url = request.url.hostname
            if backend_url and "railway.app" in backend_url:
                # Replace "backend" with "frontend" in hostname
                frontend_hostname = backend_url.replace("backend", "frontend")
                frontend_url = f"https://{frontend_hostname}"
            else:
                frontend_url = "http://localhost:5173"
    elif os.getenv("ENVIRONMENT") == "production":
        # Production environment
        frontend_url = os.getenv("FRONTEND_URL", "https://hypepaper.pages.dev")
    else:
        # Local development
        frontend_url = "http://localhost:5173"

    # Build callback URL
    callback_url = f"{frontend_url}/auth/callback"

    # Preserve all query parameters and forward to frontend
    query_string = request.url.query
    if query_string:
        callback_url += f"?{query_string}"

    return RedirectResponse(url=callback_url, status_code=302)
