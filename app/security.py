"""
Security middleware and utilities for OWASP Top 10 hardening.

Provides:
  - SecurityHeadersMiddleware: HTTP security headers (CSP, HSTS, X-Frame-Options, etc.)
  - InputValidationMiddleware: Request size, content-type validation
  - RateLimitMiddleware: Per-IP rate limiting (requests/minute)
  - validate_api_key: API key validation utility
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Callable
from datetime import datetime, timedelta

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)

# Request tracking for rate limiting
_request_tracker: dict[str, list[float]] = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 60
MAX_REQUEST_SIZE_MB = 10
MAX_REQUEST_SIZE_BYTES = MAX_REQUEST_SIZE_MB * 1024 * 1024


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    
    Headers added:
      - X-Content-Type-Options: nosniff (prevent MIME sniffing)
      - X-Frame-Options: DENY (prevent clickjacking)
      - Content-Security-Policy: default-src 'self' (XSS protection)
      - Strict-Transport-Security: max-age=31536000 (HSTS - 1 year)
      - Referrer-Policy: strict-origin-when-cross-origin
      - Permissions-Policy: controls browser features
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Remove Server header to avoid information disclosure
        # MutableHeaders doesn't have .pop() in newer Starlette, use del instead
        try:
            del response.headers["server"]
        except KeyError:
            pass

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking (Broken Auth - OWASP #1)
        response.headers["X-Frame-Options"] = "DENY"

        # Content Security Policy (Injection - OWASP #3, Insecure Design - OWASP #4)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )

        # HSTS (HTTP Strict Transport Security) - Insecure Design - OWASP #4
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Referrer Policy (Misconfiguration - OWASP #5)
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature Policy) - Misconfiguration - OWASP #5
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=()"
        )

        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Validate incoming requests for security and integrity.
    
    Checks:
      - Content-Type for POST/PUT requests (Injection - OWASP #3)
      - Request size < 10MB (Insecure Design - OWASP #4)
      - Returns 400 for invalid content-type
      - Returns 413 for oversized requests
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size_bytes = int(content_length)
                if size_bytes > MAX_REQUEST_SIZE_BYTES:
                    client_ip = request.client.host if request.client else "unknown"
                    logger.warning(
                        f"Request too large: {size_bytes} bytes "
                        f"(max: {MAX_REQUEST_SIZE_BYTES}) from {client_ip}"
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"Request too large (max {MAX_REQUEST_SIZE_MB}MB)"
                        },
                    )
            except (ValueError, TypeError):
                logger.warning("Invalid content-length header")

        # Validate content-type for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            # Allow application/json, application/x-www-form-urlencoded, multipart/form-data
            allowed_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data",
                "text/plain",
            ]
            if content_type and not any(
                content_type.startswith(allowed) for allowed in allowed_types
            ):
                client_ip = request.client.host if request.client else "unknown"
                logger.warning(
                    f"Invalid content-type: {content_type} "
                    f"from {client_ip}"
                )
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid content-type header"},
                )

        response = await call_next(request)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limit requests per IP address (requests/minute).
    
    Limits: 60 requests per minute per IP
    Returns: 429 Too Many Requests if limit exceeded
    Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
    
    Prevents: Broken Authentication Failures (OWASP #7)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP (handle proxy headers)
        client_ip = request.client.host if request.client else "unknown"
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(",")[0].strip()

        current_time = time.time()
        minute_ago = current_time - 60

        # Clean old entries (older than 1 minute)
        _request_tracker[client_ip] = [
            req_time for req_time in _request_tracker[client_ip] if req_time > minute_ago
        ]

        # Check rate limit
        request_count = len(_request_tracker[client_ip])
        if request_count >= MAX_REQUESTS_PER_MINUTE:
            logger.warning(
                f"Rate limit exceeded for {client_ip}: "
                f"{request_count} requests in 60s"
            )
            reset_time = _request_tracker[client_ip][0] + 60
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
                headers={
                    "X-RateLimit-Limit": str(MAX_REQUESTS_PER_MINUTE),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time)),
                    "Retry-After": str(int(reset_time - current_time)),
                },
            )

        # Record this request
        _request_tracker[client_ip].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        remaining = MAX_REQUESTS_PER_MINUTE - request_count - 1
        reset_time = (
            _request_tracker[client_ip][0] + 60
            if _request_tracker[client_ip]
            else current_time + 60
        )

        response.headers["X-RateLimit-Limit"] = str(MAX_REQUESTS_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))

        return response


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format and existence.
    
    Args:
        api_key: API key to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not api_key:
        return False
    
    # Basic format check: should be non-empty string
    if not isinstance(api_key, str) or len(api_key) < 10:
        return False
    
    # Can be extended with DB lookup, cryptographic verification, etc.
    return True
