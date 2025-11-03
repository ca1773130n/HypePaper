"""FastAPI main application.

Entry point for the HypePaper backend API.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
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
async def oauth_redirect_proxy(request: Request, frontend_callback: str = None):
    """
    OAuth redirect proxy for Railway preview deployments.

    This endpoint provides a stable redirect URI for Supabase OAuth that works
    with Railway's dynamic preview deployment URLs.

    IMPORTANT: This returns an HTML page with JavaScript that preserves the OAuth
    hash parameters (#access_token, etc.) when redirecting. Hash fragments are
    client-side only and don't reach the server, so we need JavaScript to handle them.

    The frontend URL is determined by:
    1. frontend_callback query parameter (passed by frontend)
    2. Or auto-detected based on Railway environment variables
    3. Or fallback to configured production/development URLs

    Supabase Configuration:
    Add this redirect URI to Supabase → Authentication → URL Configuration:
    - https://api.hypepaper.app/oauth/redirect-proxy
    - https://your-railway-backend.up.railway.app/oauth/redirect-proxy
    - https://*.up.railway.app/oauth/redirect-proxy (if Supabase supports wildcards)

    This eliminates the need to add each preview deployment URL.
    """
    from fastapi.responses import HTMLResponse
    import urllib.parse

    # Determine frontend callback URL
    if frontend_callback:
        # Decode the frontend callback URL passed as parameter
        callback_url = urllib.parse.unquote(frontend_callback)
    else:
        # Auto-detect based on environment
        railway_env = os.getenv("RAILWAY_ENVIRONMENT_NAME", "")
        railway_static_url = os.getenv("RAILWAY_STATIC_URL", "")

        if railway_env.startswith("pr-"):
            # Railway preview deployment
            if railway_static_url:
                frontend_url = f"https://{railway_static_url}"
            else:
                # Try to construct from backend URL
                backend_hostname = request.url.hostname
                if backend_hostname and "railway.app" in backend_hostname:
                    # Replace "backend" with "frontend" in hostname
                    frontend_hostname = backend_hostname.replace("backend", "frontend")
                    frontend_url = f"https://{frontend_hostname}"
                else:
                    frontend_url = "http://localhost:5173"
        elif os.getenv("ENVIRONMENT") == "production":
            # Production
            frontend_url = os.getenv("FRONTEND_URL", "https://hypepaper.pages.dev")
        else:
            # Development
            frontend_url = "http://localhost:5173"

        callback_url = f"{frontend_url}/auth/callback"

    # Return HTML page with JavaScript redirect that preserves hash parameters
    # This is necessary because hash fragments (#access_token, etc.) are client-side only
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Redirecting...</title>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: system-ui, -apple-system, sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white;
                padding: 3rem;
                border-radius: 1rem;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 400px;
            }}
            .spinner {{
                width: 50px;
                height: 50px;
                margin: 0 auto 1.5rem;
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            h2 {{
                color: #333;
                margin: 0 0 0.5rem;
                font-size: 1.5rem;
            }}
            p {{
                color: #666;
                margin: 0;
                font-size: 0.95rem;
            }}
            .debug {{
                margin-top: 1.5rem;
                padding: 1rem;
                background: #f5f5f5;
                border-radius: 0.5rem;
                font-size: 0.85rem;
                color: #666;
                word-break: break-all;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="spinner"></div>
            <h2>Completing sign in...</h2>
            <p>Please wait while we redirect you.</p>
            <div class="debug" id="debug" style="display:none;"></div>
        </div>
        <script>
            // Get hash parameters (OAuth tokens from Supabase)
            const hash = window.location.hash;

            // Get query parameters (optional additional data)
            const search = window.location.search;

            // Build final callback URL with hash and query preserved
            const callbackUrl = "{callback_url}";
            let finalUrl = callbackUrl;

            // Preserve query parameters if any
            if (search) {{
                finalUrl += search;
            }}

            // Preserve hash parameters (most important - contains OAuth tokens)
            if (hash) {{
                finalUrl += hash;
            }}

            // Debug output (uncomment for troubleshooting)
            // document.getElementById('debug').style.display = 'block';
            // document.getElementById('debug').innerHTML =
            //     'Redirecting to:<br>' + finalUrl;

            // Log for debugging
            console.log('OAuth Redirect Proxy');
            console.log('Original URL:', window.location.href);
            console.log('Callback URL:', callbackUrl);
            console.log('Final URL:', finalUrl);
            console.log('Hash params:', hash);
            console.log('Query params:', search);

            // Redirect immediately (hash fragments are preserved)
            window.location.replace(finalUrl);
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content, status_code=200)
