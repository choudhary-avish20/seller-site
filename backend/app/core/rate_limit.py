import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

# In-memory fixed-window limiter, keyed by client IP. Good enough for a single-process
# deployment; a multi-worker/multi-instance deployment would need a shared store (e.g.
# Redis, already a dependency here but otherwise unused) since each process has its own state.
_buckets: dict[str, list[float]] = defaultdict(list)


def rate_limit(key_prefix: str, max_requests: int, window_seconds: int):
    """FastAPI dependency factory: raises 429 once an IP exceeds max_requests within window_seconds."""

    async def _dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"{key_prefix}:{client_ip}"
        now = time.time()
        window_start = now - window_seconds

        bucket = _buckets[key]
        while bucket and bucket[0] < window_start:
            bucket.pop(0)

        if len(bucket) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Please try again later.",
            )
        bucket.append(now)

    return _dependency
