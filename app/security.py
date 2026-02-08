import time
from dataclasses import dataclass
from typing import Dict, Optional

from app.config import settings


@dataclass
class RateLimitState:
    tokens: float
    updated_at: float


class RateLimiter:
    def __init__(self, rate_per_min: int) -> None:
        self.rate_per_min = rate_per_min
        self._state: Dict[str, RateLimitState] = {}

    def allow(self, key: str) -> bool:
        if self.rate_per_min <= 0:
            return True
        now = time.time()
        state = self._state.get(key)
        capacity = float(self.rate_per_min)
        refill_rate = capacity / 60.0
        if not state:
            state = RateLimitState(tokens=capacity, updated_at=now)
            self._state[key] = state
        elapsed = now - state.updated_at
        state.tokens = min(capacity, state.tokens + elapsed * refill_rate)
        state.updated_at = now
        if state.tokens < 1.0:
            return False
        state.tokens -= 1.0
        return True


rate_limiter = RateLimiter(settings.rate_limit_per_min)


def is_allowed_user(user_id: Optional[str]) -> bool:
    if not settings.allowed_user_ids:
        return False
    if not user_id:
        return False
    return str(user_id) in settings.allowed_user_ids


def check_api_key(provided_key: Optional[str]) -> bool:
    if not settings.api_key:
        return False
    return provided_key == settings.api_key
