"""
Rate limiting middleware using Redis.
"""
import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.redis_client import rate_limit_cache

logger = logging.getLogger(__name__)

EXEMPT_PATHS = {"/health", "/api/docs", "/api/redoc", "/api/openapi.json"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        minute_key = f"minute:{client_ip}"
        hour_key = f"hour:{client_ip}"

        minute_count = await rate_limit_cache.incr(minute_key, ttl=60)
        hour_count = await rate_limit_cache.incr(hour_key, ttl=3600)

        if minute_count > settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": "60"},
            )

        if hour_count > settings.RATE_LIMIT_PER_HOUR:
            return JSONResponse(
                status_code=429,
                content={"detail": "Hourly rate limit exceeded."},
                headers={"Retry-After": "3600"},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit-Minute"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            max(0, settings.RATE_LIMIT_PER_MINUTE - minute_count)
        )
        return response
