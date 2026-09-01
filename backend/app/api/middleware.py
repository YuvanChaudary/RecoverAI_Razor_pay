"""
FastAPI Request Correlation ID Middleware
Intercepts requests, extracts or generates X-Request-ID, and propagates correlation context.
"""

import uuid
from contextvars import ContextVar
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ContextVar for storing correlation ID per request context
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> Optional[str]:
    """
    Retrieves current active correlation ID from context contextvar.
    """
    return correlation_id_ctx.get()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware ensuring every HTTP request has a traceable X-Request-ID header.
    """

    HEADER_NAME = "X-Request-ID"

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract existing X-Request-ID header or generate new UUID
        request_id = request.headers.get(self.HEADER_NAME)
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex[:16]}"

        # Set contextvar for access by downstream loggers & services
        token = correlation_id_ctx.set(request_id)

        try:
            response: Response = await call_next(request)
            response.headers[self.HEADER_NAME] = request_id
            return response
        finally:
            correlation_id_ctx.reset(token)
