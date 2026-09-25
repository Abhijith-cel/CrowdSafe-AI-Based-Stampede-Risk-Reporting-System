"""Rate Limiter Service for CrowdSafe.

Implements sliding-window and cooldown throttling to prevent alert fatigue,
notification storming, and resource exhaustion during continuous crowd surges.
"""

from __future__ import annotations

import collections
import logging
import threading
import time
from typing import Deque, Dict, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Thread-safe sliding-window rate limiter and alert cooldown manager."""

    def __init__(self) -> None:
        """Initialize in-memory storage for event timestamps."""
        self._history: Dict[str, Deque[float]] = collections.defaultdict(collections.deque)
        self._last_alert_time: Dict[str, float] = {}
        self._lock = threading.Lock()

    def is_allowed(
        self,
        key: str,
        max_events: int = 1,
        window_seconds: float = 60.0,
    ) -> bool:
        """Check if an action is permitted within a sliding time window.

        Args:
            key: Rate limit identifier (e.g., 'zone:gate_1:high_alert').
            max_events: Maximum allowed actions within window_seconds.
            window_seconds: Duration of rate limit window.

        Returns:
            True if event is allowed, False if limit has been reached.
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            q = self._history[key]
            # Evict timestamps older than cutoff
            while q and q[0] <= cutoff:
                q.popleft()

            if len(q) < max_events:
                q.append(now)
                return True

            return False

    def should_suppress_alert(
        self,
        zone_id: str,
        risk_level: str,
        cooldown_seconds: float = 60.0,
    ) -> bool:
        """Determine if an alert should be suppressed due to active cooldown.

        Higher severity alerts (e.g. escalation to CRITICAL) can override cooldown.

        Args:
            zone_id: Identifier of monitored zone.
            risk_level: Severity string ('LOW', 'MODERATE', 'HIGH', 'CRITICAL').
            cooldown_seconds: Minimum seconds required between consecutive alerts of same severity.

        Returns:
            True if alert should be suppressed (cooldown active), False if allowed.
        """
        key = f"{zone_id}:{risk_level}"
        now = time.time()

        with self._lock:
            last_sent = self._last_alert_time.get(key, 0.0)
            if (now - last_sent) < cooldown_seconds:
                return True  # Suppress

            self._last_alert_time[key] = now
            return False  # Dispatch allowed

    def get_remaining_cooldown(self, key: str, cooldown_seconds: float = 60.0) -> float:
        """Get remaining cooldown in seconds before the next event is permitted."""
        with self._lock:
            last = self._last_alert_time.get(key, 0.0)
            elapsed = time.time() - last
            remaining = cooldown_seconds - elapsed
            return max(0.0, round(remaining, 2))

    def reset(self, key: Optional[str] = None) -> None:
        """Reset rate limiter state for a specific key or all keys."""
        with self._lock:
            if key:
                self._history.pop(key, None)
                self._last_alert_time.pop(key, None)
            else:
                self._history.clear()
                self._last_alert_time.clear()
