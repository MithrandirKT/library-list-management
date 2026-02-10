"""
Quota-aware router for AI providers.
"""

import random
import time
from typing import Callable, Dict, Optional, Tuple


class ProviderState:
    def __init__(self) -> None:
        self.cooldown_until = 0.0
        self.dead = False

    def available(self) -> bool:
        if self.dead:
            return False
        return time.time() >= self.cooldown_until

    def cooldown(self, seconds: float) -> None:
        jitter = random.uniform(0, 0.25 * seconds)
        self.cooldown_until = time.time() + seconds + jitter

    def mark_dead(self) -> None:
        self.dead = True


class QuotaRouter:
    def __init__(self) -> None:
        self.states: Dict[str, ProviderState] = {}

    def _state(self, name: str) -> ProviderState:
        if name not in self.states:
            self.states[name] = ProviderState()
        return self.states[name]

    def call(self, name: str, fn: Callable[[], Tuple[Optional[dict], Optional[int]]]) -> Optional[dict]:
        """
        fn returns (result, status_code)
        """
        state = self._state(name)
        if not state.available():
            return None

        result, status_code = fn()
        if status_code is None:
            return result

        if status_code in (401, 403):
            state.mark_dead()
            return None
        if status_code in (429, 503):
            state.cooldown(10)
            return None

        return result
