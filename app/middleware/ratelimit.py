import time
from typing import Dict, Deque, Tuple
from collections import deque
from fastapi import Request, HTTPException, status, Depends


class InMemoryRateLimiter:
    """
    Simple process-local sliding window rate limiter.
    Not suitable for multi-process deployments. Replace with Redis-backed limiter for production scale.
    """

    def __init__(self, requests: int, window_seconds: int) -> None:
        self.requests = requests
        self.window = window_seconds
        self.storage: Dict[str, Deque[float]] = {}

    def _get_bucket(self, key: str) -> Deque[float]:
        if key not in self.storage:
            self.storage[key] = deque()
        return self.storage[key]

    def __call__(self, request: Request):  
        now = time.time()
        # Key by IP + path to isolate per-endpoint per-client
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"

        bucket = self._get_bucket(key)
       
        while bucket and now - bucket[0] > self.window:
            bucket.popleft()

        if len(bucket) >= self.requests:
            # Too many requests
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Slow down.",
            )

        bucket.append(now)


def limiter_dependency(requests: int, window_seconds: int):
    limiter = InMemoryRateLimiter(requests, window_seconds)

    async def _dep(request: Request):
        return limiter(request)

    return _dep
