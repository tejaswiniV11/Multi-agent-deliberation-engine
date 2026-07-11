"""Custom middleware layer.

Adds three things every request gets, independent of the route handler:
  * a unique X-Request-ID (generated if the client didn't send one),
  * a server-timing header measuring handler duration,
  * a structured access-log line.

This is deliberately hand-rolled rather than pulled from a library so the
middleware stack is transparent for the code-quality review.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("quorum.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
        request.state.request_id = request_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:  # noqa: BLE001 - log then re-raise for the error handler
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "rid=%s %s %s -> 500 in %.1fms",
                request_id,
                request.method,
                request.url.path,
                elapsed_ms,
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["Server-Timing"] = f"app;dur={elapsed_ms:.1f}"
        logger.info(
            "rid=%s %s %s -> %s in %.1fms",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
