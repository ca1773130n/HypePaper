"""FastAPI main application.

Entry point for the HypePaper backend API.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import papers
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
    log_file = Path(os.getenv("LOG_FILE", "logs/hypepaper.log"))
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite/React dev servers
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
