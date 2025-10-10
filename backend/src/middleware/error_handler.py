"""Global error handling middleware."""
import logging
import traceback
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Handle errors globally.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        try:
            response = await call_next(request)
            return response
        except IntegrityError as e:
            logger.error(f"Database integrity error: {e}")
            logger.debug(traceback.format_exc())

            # Extract constraint violation details
            error_detail = str(e.orig) if hasattr(e, "orig") else str(e)

            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": "Integrity constraint violation",
                    "detail": error_detail,
                    "type": "IntegrityError",
                },
            )

        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            logger.debug(traceback.format_exc())

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Database operation failed",
                    "detail": str(e),
                    "type": "DatabaseError",
                },
            )

        except ValueError as e:
            logger.warning(f"Validation error: {e}")

            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Invalid input",
                    "detail": str(e),
                    "type": "ValueError",
                },
            )

        except PermissionError as e:
            logger.warning(f"Permission error: {e}")

            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Access denied",
                    "detail": str(e),
                    "type": "PermissionError",
                },
            )

        except FileNotFoundError as e:
            logger.warning(f"File not found: {e}")

            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": "Resource not found",
                    "detail": str(e),
                    "type": "FileNotFoundError",
                },
            )

        except TimeoutError as e:
            logger.error(f"Timeout error: {e}")

            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "error": "Request timeout",
                    "detail": str(e),
                    "type": "TimeoutError",
                },
            )

        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Unexpected error: {e}")
            logger.error(traceback.format_exc())

            # Don't expose internal error details in production
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "detail": "An unexpected error occurred. Please try again later.",
                    "type": type(e).__name__,
                },
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Log request and response details.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        response = await call_next(request)

        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"-> {response.status_code}"
        )

        return response
