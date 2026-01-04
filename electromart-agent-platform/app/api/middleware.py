"""
API Middleware for Error Handling, Logging, and Request Tracing
Professional middleware stack for production-ready API
"""
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
import time
import uuid
from typing import Callable

from app.schemas.schemas import ErrorResponse, ErrorDetail
from app.utils import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to every request for tracing

    Features:
    - Generates UUID for each request
    - Adds X-Request-ID to response headers
    - Logs request ID with all log messages
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store in request state for access in route handlers
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all incoming requests with timing information

    Logs:
    - Request method and path
    - Request ID
    - Client IP
    - Response status code
    - Response time
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Extract request info
        request_id = getattr(request.state, "request_id", "unknown")
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # Log incoming request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "client_ip": client_ip
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate response time
            response_time = (time.time() - start_time) * 1000

            # Log completed request
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "response_time_ms": round(response_time, 2)
                }
            )

            # Add timing header
            response.headers["X-Response-Time"] = f"{response_time:.2f}ms"

            return response

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "response_time_ms": round(response_time, 2),
                    "error": str(e)
                },
                exc_info=True
            )

            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Centralized error handling for consistent error responses

    Handles:
    - HTTPException (FastAPI/Starlette)
    - RequestValidationError (Pydantic validation)
    - Generic exceptions (unexpected errors)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            return await self.handle_exception(request, exc)

    async def handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle different exception types with appropriate responses"""
        request_id = getattr(request.state, "request_id", "unknown")

        # HTTP Exceptions (400, 404, 500, etc.)
        if isinstance(exc, StarletteHTTPException):
            error_response = ErrorResponse(
                error=f"HTTP_{exc.status_code}",
                message=exc.detail,
                request_id=request_id
            )

            logger.warning(
                f"HTTP exception: {exc.status_code} - {exc.detail}",
                extra={
                    "request_id": request_id,
                    "status_code": exc.status_code,
                    "path": request.url.path
                }
            )

            return JSONResponse(
                status_code=exc.status_code,
                content=error_response.model_dump()
            )

        # Validation Errors (422)
        if isinstance(exc, RequestValidationError):
            error_details = [
                ErrorDetail(
                    loc=list(err.get("loc", [])),
                    msg=err.get("msg", ""),
                    type=err.get("type", "")
                )
                for err in exc.errors()
            ]

            error_response = ErrorResponse(
                error="VALIDATION_ERROR",
                message="Request validation failed",
                details=error_details,
                request_id=request_id
            )

            logger.warning(
                f"Validation error: {len(error_details)} errors",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "errors": error_details
                }
            )

            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=error_response.model_dump(exclude_none=True)
            )

        # Generic Exceptions (500)
        error_response = ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
            request_id=request_id
        )

        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "exception_type": type(exc).__name__
            },
            exc_info=True
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware with security headers

    Adds security headers:
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Strict-Transport-Security (HTTPS only)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Add HSTS header for HTTPS (only in production)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware (in-memory)

    Note: For production, use Redis-based rate limiting
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = {}  # {ip: [(timestamp, count), ...]}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Clean old entries
        self._clean_old_entries(current_time)

        # Check rate limit
        if self._is_rate_limited(client_ip, current_time):
            request_id = getattr(request.state, "request_id", "unknown")

            logger.warning(
                f"Rate limit exceeded",
                extra={
                    "request_id": request_id,
                    "client_ip": client_ip,
                    "path": request.url.path
                }
            )

            error_response = ErrorResponse(
                error="RATE_LIMIT_EXCEEDED",
                message=f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds} seconds.",
                request_id=request_id
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_response.model_dump(),
                headers={"Retry-After": str(self.window_seconds)}
            )

        # Increment request count
        self._increment_request_count(client_ip, current_time)

        return await call_next(request)

    def _clean_old_entries(self, current_time: float):
        """Remove entries older than the time window"""
        cutoff_time = current_time - self.window_seconds

        for ip in list(self.request_counts.keys()):
            self.request_counts[ip] = [
                (timestamp, count)
                for timestamp, count in self.request_counts[ip]
                if timestamp > cutoff_time
            ]

            # Remove IP if no entries left
            if not self.request_counts[ip]:
                del self.request_counts[ip]

    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client has exceeded rate limit"""
        if client_ip not in self.request_counts:
            return False

        cutoff_time = current_time - self.window_seconds
        recent_requests = sum(
            count for timestamp, count in self.request_counts[client_ip]
            if timestamp > cutoff_time
        )

        return recent_requests >= self.max_requests

    def _increment_request_count(self, client_ip: str, current_time: float):
        """Increment request count for client"""
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []

        self.request_counts[client_ip].append((current_time, 1))


# Exception handlers for FastAPI app
def configure_exception_handlers(app):
    """
    Configure custom exception handlers for the FastAPI app

    Usage in main.py:
        from backend.api.middleware import configure_exception_handlers
        configure_exception_handlers(app)
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", "unknown")

        error_response = ErrorResponse(
            error=f"HTTP_{exc.status_code}",
            message=exc.detail,
            request_id=request_id
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", "unknown")

        error_details = [
            ErrorDetail(
                loc=list(err.get("loc", [])),
                msg=err.get("msg", ""),
                type=err.get("type", "")
            )
            for err in exc.errors()
        ]

        error_response = ErrorResponse(
            error="VALIDATION_ERROR",
            message="Request validation failed",
            details=error_details,
            request_id=request_id
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump(exclude_none=True)
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")

        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
            extra={
                "request_id": request_id,
                "path": request.url.path
            },
            exc_info=True
        )

        error_response = ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
            request_id=request_id
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )
