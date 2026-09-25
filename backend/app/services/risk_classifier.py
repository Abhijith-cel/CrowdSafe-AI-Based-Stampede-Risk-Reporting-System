"""Risk Classifier Service for CrowdSafe.

Evaluates stampede and crowd crush danger levels based on crowd science
principles (Fruin Level of Service, Still's crowd density standards),
incorporating flow velocity, surge acceleration, and bottleneck factors.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Stampede risk severity classifications."""

    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RiskThresholds:
    """Configurable density boundaries (persons per square meter)."""

    low_max: float = 2.0        # Free movement (LOS A-C)
    moderate_max: float = 3.5   # Restricted movement (LOS D-E)
    high_max: float = 5.0       # Severe restriction, shockwaves possible (LOS F)
    # > high_max is CRITICAL: Immediate crush/asphyxia risk


@dataclass
class RiskAssessment:
    """Comprehensive stampede risk evaluation report."""

    level: RiskLevel
    risk_score: float  # Normalized 0.0 to 100.0
    density: float
    headcount: int
    surge_rate: float
    recommendation: str
    is_bottleneck: bool = False
    factors: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class RiskClassifier:
    """Classifies crowd safety risk and generates real-time recommendations."""

    def __init__(self, thresholds: Optional[RiskThresholds] = None) -> None:
        """Initialize risk classifier with safety thresholds."""
        self.thresholds = thresholds or RiskThresholds()

    def classify(
        self,
        density: float,
        headcount: int,
        surge_rate: float = 0.0,
        is_bottleneck: bool = False,
        capacity_limit: Optional[int] = None,
    ) -> RiskAssessment:
        """Compute the risk level and numerical score for a given observation.

        Args:
            density: Persons per square meter.
            headcount: Absolute person count.
            surge_rate: Rate of crowd increase (persons/min). Positive means surging.
            is_bottleneck: True if the zone is a narrow corridor, stairwell, or gate.
            capacity_limit: Maximum safe physical headcount for the zone.

        Returns:
            RiskAssessment with severity level, score, and tactical recommendations.
        """
        density = max(0.0, density)
        headcount = max(0, headcount)

        # Baseline score derived from density relative to critical threshold (5.0 p/m2)
        base_score = min(100.0, (density / self.thresholds.high_max) * 75.0)

        # Capacity overflow penalty
        capacity_ratio = 0.0
        if capacity_limit and capacity_limit > 0:
            capacity_ratio = headcount / capacity_limit
            if capacity_ratio > 1.0:
                base_score += min(20.0, (capacity_ratio - 1.0) * 40.0)

        # Bottleneck multiplier
        if is_bottleneck:
            base_score *= 1.2

        # Sudden surge penalty (crowd rushing in quickly)
        if surge_rate > 10.0:
            surge_penalty = min(20.0, (surge_rate - 10.0) * 0.5)
            base_score += surge_penalty

        risk_score = round(min(100.0, max(0.0, base_score)), 2)

        # Determine Risk Level
        if density >= self.thresholds.high_max or risk_score >= 80.0:
            level = RiskLevel.CRITICAL
            recommendation = (
                "CRITICAL ALERT: Stampede danger imminent. Halt inbound crowd flow immediately. "
                "Open emergency bypass gates and deploy rapid-response marshals."
            )
        elif density >= self.thresholds.moderate_max or risk_score >= 60.0:
            level = RiskLevel.HIGH
            recommendation = (
                "HIGH WARNING: Crowd density reaching dangerous levels. Restrict entry points, "
                "meter inflows, and issue public address dispersal announcements."
            )
        elif density >= self.thresholds.low_max or risk_score >= 35.0:
            level = RiskLevel.MODERATE
            recommendation = (
                "MODERATE ATTENTION: Density elevated. Monitor crowd flow velocity, prepare detour "
                "signage, and position stewards near potential pinch points."
            )
        else:
            level = RiskLevel.LOW
            recommendation = "LOW RISK: Crowd flow within safe operating parameters. Routine monitoring."

        factors = {
            "density_persons_per_sqm": density,
            "headcount": headcount,
            "surge_rate_per_min": surge_rate,
            "is_bottleneck": is_bottleneck,
            "capacity_utilization": f"{round(capacity_ratio * 100, 1)}%" if capacity_limit else "N/A",
        }

        return RiskAssessment(
            level=level,
            risk_score=risk_score,
            density=round(density, 2),
            headcount=headcount,
            surge_rate=round(surge_rate, 2),
            recommendation=recommendation,
            is_bottleneck=is_bottleneck,
            factors=factors,
        )
