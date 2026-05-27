"""Request/response middleware for monitoring."""

import logging
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses with timing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log request
        logger.info(
            "request_start",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            }
        )

        # Track timing
        start_time = time.time()
        
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                "request_error",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                },
                exc_info=True
            )
            raise

        # Log response
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "request_complete",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        )

        # Add request ID header
        response.headers["X-Request-ID"] = request_id
        return response
