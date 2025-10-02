"""FastAPI main application.

Entry point for the HypePaper backend API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import papers, topics

# Create FastAPI app
app = FastAPI(
    title="HypePaper API",
    description="API for tracking trending research papers",
    version="1.0.0",
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(topics.router)
app.include_router(papers.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "HypePaper API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
