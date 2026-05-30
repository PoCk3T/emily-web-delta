"""Rate limiting using Redis sliding window."""

from collections import defaultdict
from functools import wraps
from time import time
from typing import Callable

from fastapi import HTTPException, Request, status


class RateLimiter:
    """Simple in-memory rate limiter (use Redis in production)."""

    def __init__(self):
        self._windows: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if a request is allowed under the rate limit."""
        now = time()
        # Clean old entries
        self._windows[key] = [
            t for t in self._windows[key] if now - t < window
        ]
        if len(self._windows[key]) >= limit:
            return False
        self._windows[key].append(now)
        return True


rate_limiter = RateLimiter()


def require_rate_limit(
    key_func: Callable[[Request], str],
    limit: int = 100,
    window: int = 60,
) -> Callable:
    """Decorator to apply rate limiting."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            key = key_func(request)
            if not rate_limiter.is_allowed(key, limit, window):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Try again later.",
                )
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
