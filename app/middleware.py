"""Middleware for request logging and timing."""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("pump_api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        t0 = time.perf_counter()

        # Attach request_id so routes can use it
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed = (time.perf_counter() - t0) * 1000
            logger.error(
                "[%s] %s %s → 500 (%.1f ms) — %s",
                request_id, request.method, request.url.path, elapsed, str(exc),
            )
            raise

        elapsed = (time.perf_counter() - t0) * 1000
        logger.info(
            "[%s] %s %s → %s (%.1f ms)",
            request_id, request.method, request.url.path, response.status_code, elapsed,
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{elapsed:.1f}"
        return response