import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_requests: int = 100, window: int = 3600):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)

    def is_rate_limited(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window

        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]

        # Check rate limit
        if len(self.requests[key]) >= self.max_requests:
            return True

        self.requests[key].append(now)
        return False


rate_limiter = RateLimiter()