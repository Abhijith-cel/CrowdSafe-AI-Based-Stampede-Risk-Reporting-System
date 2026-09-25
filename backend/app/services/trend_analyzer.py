"""Trend Analyzer Service for CrowdSafe.

Performs time-series analysis on crowd density and headcount data,
detecting sudden surges, computing velocity/acceleration of crowd accumulation,
and forecasting near-future stampede risks over configurable sliding time windows.
"""

from __future__ import annotations

import collections
import logging
import time
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CrowdDataPoint:
    """A single point in time crowd measurement."""

    timestamp: float
    count: int
    density: float


@dataclass
class TrendMetrics:
    """Statistical summary and surge analysis for a monitored zone."""

    zone_id: str
    current_count: int
    current_density: float
    moving_avg_count: float
    moving_avg_density: float
    rate_of_change_per_min: float  # Velocity (persons per minute)
    acceleration: float            # Change in velocity
    is_surging: bool
    forecast_count_5m: int
    forecast_density_5m: float
    sample_size: int
    timestamp: float = field(default_factory=time.time)


class TrendAnalyzer:
    """Tracks time-series measurements per zone and computes trends and surge risks."""

    def __init__(
        self,
        max_history_length: int = 1000,
        surge_threshold_rate: float = 15.0,  # +15 persons/min flags surge
    ) -> None:
        """Initialize TrendAnalyzer.

        Args:
            max_history_length: Maximum observations retained per zone queue.
            surge_threshold_rate: Person/minute increase required to declare a surge.
        """
        self.max_history_length = max_history_length
        self.surge_threshold_rate = surge_threshold_rate
        self._history: Dict[str, Deque[CrowdDataPoint]] = collections.defaultdict(
            lambda: collections.deque(maxlen=self.max_history_length)
        )

    def record_observation(
        self,
        zone_id: str,
        count: int,
        density: float,
        timestamp: Optional[float] = None,
    ) -> None:
        """Record a new crowd measurement for a specific zone or camera feed."""
        t = timestamp if timestamp is not None else time.time()
        self._history[zone_id].append(
            CrowdDataPoint(timestamp=t, count=count, density=density)
        )

    def get_history(self, zone_id: str, window_seconds: Optional[float] = None) -> List[CrowdDataPoint]:
        """Retrieve historical points within an optional recent time window."""
        points = list(self._history.get(zone_id, []))
        if not points or window_seconds is None:
            return points

        cutoff = time.time() - window_seconds
        return [p for p in points if p.timestamp >= cutoff]

    def analyze_zone(
        self,
        zone_id: str,
        window_seconds: float = 300.0,  # 5 minutes default
    ) -> TrendMetrics:
        """Calculate trend metrics, rate of change, and future projection.

        Args:
            zone_id: Identifier of the zone.
            window_seconds: Duration of lookback window in seconds.

        Returns:
            TrendMetrics containing moving averages, surge indicator, and 5-min forecast.
        """
        points = self.get_history(zone_id, window_seconds=window_seconds)

        if not points:
            return TrendMetrics(
                zone_id=zone_id,
                current_count=0,
                current_density=0.0,
                moving_avg_count=0.0,
                moving_avg_density=0.0,
                rate_of_change_per_min=0.0,
                acceleration=0.0,
                is_surging=False,
                forecast_count_5m=0,
                forecast_density_5m=0.0,
                sample_size=0,
            )

        latest = points[-1]
        counts = [p.count for p in points]
        densities = [p.density for p in points]

        avg_count = sum(counts) / len(counts)
        avg_density = sum(densities) / len(densities)

        # Rate of change calculation
        rate_of_change = 0.0
        acceleration = 0.0

        if len(points) >= 2:
            time_delta_sec = points[-1].timestamp - points[0].timestamp
            if time_delta_sec > 1.0:
                count_delta = points[-1].count - points[0].count
                # Rate per minute: (delta / delta_seconds) * 60
                rate_of_change = (count_delta / time_delta_sec) * 60.0

            # If enough points, calculate acceleration (comparing first half to second half)
            mid = len(points) // 2
            t_first = points[mid].timestamp - points[0].timestamp
            t_second = points[-1].timestamp - points[mid].timestamp
            if t_first > 0 and t_second > 0:
                v1 = ((points[mid].count - points[0].count) / t_first) * 60.0
                v2 = ((points[-1].count - points[mid].count) / t_second) * 60.0
                acceleration = v2 - v1

        is_surging = rate_of_change >= self.surge_threshold_rate

        # Simple linear projection for next 5 minutes
        forecast_count = max(0, int(round(latest.count + (rate_of_change * 5.0))))
        density_scale = (forecast_count / latest.count) if latest.count > 0 else 1.0
        forecast_density = round(latest.density * density_scale, 2)

        return TrendMetrics(
            zone_id=zone_id,
            current_count=latest.count,
            current_density=latest.density,
            moving_avg_count=round(avg_count, 1),
            moving_avg_density=round(avg_density, 2),
            rate_of_change_per_min=round(rate_of_change, 2),
            acceleration=round(acceleration, 2),
            is_surging=is_surging,
            forecast_count_5m=forecast_count,
            forecast_density_5m=forecast_density,
            sample_size=len(points),
            timestamp=latest.timestamp,
        )

    def clear(self, zone_id: Optional[str] = None) -> None:
        """Reset historical measurements for a specific zone or all zones."""
        if zone_id:
            self._history.pop(zone_id, None)
        else:
            self._history.clear()
