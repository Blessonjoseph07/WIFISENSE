import time
import threading
from typing import Dict, List, Tuple
from fastapi import Request, HTTPException, status

class InMemoryRateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        # Key: (ip_or_key, bucket_name) -> list of timestamp floats
        self._requests: Dict[Tuple[str, str], List[float]] = {}

    def is_allowed(self, key: str, bucket: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        now = time.time()
        bucket_key = (key, bucket)
        window_start = now - window_seconds

        with self._lock:
            timestamps = self._requests.get(bucket_key, [])
            # Filter out timestamps outside the current window
            valid_timestamps = [ts for ts in timestamps if ts > window_start]

            if len(valid_timestamps) >= max_requests:
                earliest = valid_timestamps[0]
                retry_after = max(1, int(earliest + window_seconds - now))
                self._requests[bucket_key] = valid_timestamps
                return False, retry_after

            valid_timestamps.append(now)
            self._requests[bucket_key] = valid_timestamps
            return True, 0

    def cleanup_old_records(self, max_age_seconds: int = 3600):
        now = time.time()
        threshold = now - max_age_seconds
        with self._lock:
            keys_to_delete = []
            for bucket_key, timestamps in self._requests.items():
                self._requests[bucket_key] = [ts for ts in timestamps if ts > threshold]
                if not self._requests[bucket_key]:
                    keys_to_delete.append(bucket_key)
            for k in keys_to_delete:
                del self._requests[k]


limiter = InMemoryRateLimiter()

def rate_limit(max_requests: int, window_seconds: int, bucket: str = "default"):
    """
    FastAPI dependency for rate limiting endpoints based on client host IP.
    """
    def dependency(request: Request):
        # Extract client IP
        client_ip = "127.0.0.1"
        if request.client and request.client.host:
            client_ip = request.client.host
        # Also inspect X-Forwarded-For if behind a proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        # If loopback test runner, allow higher limit so test suites don't get choked
        effective_max = max_requests * 10 if client_ip in ("127.0.0.1", "localhost", "::1") else max_requests

        allowed, retry_after = limiter.is_allowed(
            key=client_ip,
            bucket=bucket,
            max_requests=effective_max,
            window_seconds=window_seconds
        )


        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for this endpoint. Try again in {retry_after} second(s).",
                headers={"Retry-After": str(retry_after)}
            )
        return True

    return dependency
