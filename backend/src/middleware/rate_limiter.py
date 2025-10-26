"""Rate limiting middleware for API endpoints."""
import time
from collections import defaultdict
from typing import Callable, Dict, Tuple

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter middleware.

    Limits requests per IP address to prevent abuse.
    For production, consider using Redis-based rate limiting.
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        """Initialize rate limiter.

        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per IP per minute
            requests_per_hour: Maximum requests per IP per hour
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # Store: {ip: [(timestamp, count_minute, count_hour)]}
        self.ip_requests: Dict[str, list] = defaultdict(list)

        # Cleanup old entries every 100 requests
        self.request_count = 0
        self.cleanup_interval = 100

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request.

        Handles X-Forwarded-For header from reverse proxies.
        """
        # Check X-Forwarded-For header (for Railway, Cloudflare, etc.)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP (client IP)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fallback to direct client
        if request.client:
            return request.client.host

        return "unknown"

    def _cleanup_old_entries(self) -> None:
        """Remove expired entries to prevent memory leak."""
        now = time.time()
        hour_ago = now - 3600

        for ip in list(self.ip_requests.keys()):
            # Remove entries older than 1 hour
            self.ip_requests[ip] = [
                (ts, count_min, count_hour)
                for ts, count_min, count_hour in self.ip_requests[ip]
                if ts > hour_ago
            ]

            # Remove IP if no recent requests
            if not self.ip_requests[ip]:
                del self.ip_requests[ip]

    def _check_rate_limit(self, ip: str) -> Tuple[bool, Dict[str, int]]:
        """Check if IP has exceeded rate limits.

        Returns:
            (is_allowed, rate_info) tuple
        """
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600

        # Count requests in last minute and hour
        requests_minute = sum(
            1 for ts, _, _ in self.ip_requests[ip]
            if ts > minute_ago
        )

        requests_hour = sum(
            1 for ts, _, _ in self.ip_requests[ip]
            if ts > hour_ago
        )

        # Add current request
        self.ip_requests[ip].append((now, requests_minute + 1, requests_hour + 1))

        # Check limits
        is_allowed = (
            requests_minute < self.requests_per_minute
            and requests_hour < self.requests_per_hour
        )

        rate_info = {
            "requests_minute": requests_minute + 1,
            "limit_minute": self.requests_per_minute,
            "requests_hour": requests_hour + 1,
            "limit_hour": self.requests_per_hour,
        }

        return is_allowed, rate_info

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/v1/health", "/api/v1/health/"]:
            return await call_next(request)

        # Periodic cleanup
        self.request_count += 1
        if self.request_count % self.cleanup_interval == 0:
            self._cleanup_old_entries()

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Check rate limit
        is_allowed, rate_info = self._check_rate_limit(client_ip)

        if not is_allowed:
            # Return 429 Too Many Requests
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests from {client_ip}. "
                    f"Limit: {self.requests_per_minute}/minute, {self.requests_per_hour}/hour",
                    "retry_after": 60,  # seconds
                    "rate_info": rate_info,
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit-Minute": str(self.requests_per_minute),
                    "X-RateLimit-Limit-Hour": str(self.requests_per_hour),
                    "X-RateLimit-Remaining-Minute": str(
                        max(0, self.requests_per_minute - rate_info["requests_minute"])
                    ),
                    "X-RateLimit-Remaining-Hour": str(
                        max(0, self.requests_per_hour - rate_info["requests_hour"])
                    ),
                },
            )

        # Add rate limit headers to response
        response = await call_next(request)

        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            max(0, self.requests_per_minute - rate_info["requests_minute"])
        )
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            max(0, self.requests_per_hour - rate_info["requests_hour"])
        )

        return response
