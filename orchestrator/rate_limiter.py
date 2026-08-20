"""
Simple Redis-backed rate limiter middleware for FastAPI.

Uses a sliding-window counter stored in Redis.  Each unique client
(IP + optional API key) gets a separate counter, scoped per endpoint
so that different routes can have independent, differently-configured
limits (e.g. stricter on /login, looser on /health).  When the limit
is exceeded the middleware returns 429 Too Many Requests.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from orchestrator.cache_manager import CacheManager

logger = logging.getLogger(__name__)

_DEFAULT_LIMIT = 60  # requests per window
_DEFAULT_WINDOW_SECONDS = 60  # 1 minute window
 
@dataclass(frozen=True)
class RouteLimit:
    """A rate limit configuration for one endpoint."""

    limit: int
    window_seconds: int


# Per-endpoint overrides. Keys are exact request paths.
# Anything not listed here falls back to (_DEFAULT_LIMIT, _DEFAULT_WINDOW_SECONDS).
DEFAULT_ROUTE_LIMITS: dict[str, RouteLimit] = {
    "/login": RouteLimit(limit=5, window_seconds=60),
}


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Per-client, per-endpoint sliding-window rate limiter backed by Redis.

    The key is derived from the client IP, the ``X-API-Token`` header
    (if present), and the request path — so each endpoint tracks its
    own independent window. Paths under ``/docs`` are exempt from
    limiting entirely.
    """

    EXEMPT_PATHS: frozenset[str] = frozenset({
    "/health",
    "/docs",
    "/openapi.json",})

    def __init__(
        self,
        app,
        limit: int = _DEFAULT_LIMIT,
        window_seconds: int = _DEFAULT_WINDOW_SECONDS,
        route_limits: dict[str, RouteLimit] | None = None,
    ) -> None:
        super().__init__(app)
        # Fallback used for any path not present in route_limits.
        self.default_limit = RouteLimit(limit=limit, window_seconds=window_seconds)
        self.route_limits: dict[str, RouteLimit] = (
            route_limits if route_limits is not None else dict(DEFAULT_ROUTE_LIMITS)
        )

    def _limit_for_path(self, path: str) -> RouteLimit:
        """Return the configured RouteLimit for a given path, or the default."""
        return self.route_limits.get(path, self.default_limit)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if (
            path in self.EXEMPT_PATHS
            or path.startswith("/docs")
            or path == "/metrics/web-vitals"
        ):
            return await call_next(request)

        route_limit = self._limit_for_path(path)
        client_key = self._client_key(request)
        redis_client = CacheManager()

        if redis_client is None:
            return await call_next(request)

        try:
            now = time.time()
            window_start = now - route_limit.window_seconds
            # Path is part of the key so each endpoint has its own
            # independent counter/window.
            redis_key = f"ratelimit:{path}:{client_key}"

            pipe = redis_client.raw.pipeline(transaction=False)
            # Remove entries outside the window
            pipe.zremrangebyscore(redis_key, 0, window_start)
            # Add current request
            pipe.zadd(redis_key, {str(now): now})
            # Count requests in window
            pipe.zcard(redis_key)
            # Set TTL so old keys are cleaned up automatically
            pipe.expire(redis_key, route_limit.window_seconds * 2)
            results = pipe.execute()

            request_count = results[2]

            if request_count > route_limit.limit:
                retry_after = int(route_limit.window_seconds - (now - window_start))
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": max(retry_after, 1),
                    },
                    headers={"Retry-After": str(max(retry_after, 1))},
                )
        except Exception as exc:
            logger.debug("Rate limiter error (allowing request): %s", exc)

        return await call_next(request)

    @staticmethod
    def _client_key(request: Request) -> str:
        """Build a composite key: IP + optional API token."""
        forwarded = request.headers.get("x-forwarded-for")
        ip = (
            forwarded.split(",")[0].strip()
            if forwarded
            else request.client.host if request.client else "unknown"
        )
        token = request.headers.get("x-api-token", "")
        return f"{ip}:{token}"