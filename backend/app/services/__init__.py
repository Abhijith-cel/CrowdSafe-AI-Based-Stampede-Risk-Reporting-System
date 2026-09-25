"""CrowdSafe Services Package.

This package contains modular core services for video frame extraction,
crowd density analysis, stampede risk classification, spatial heatmaps,
geo-matching, alerting, rate limiting, and background task processing.
"""

from .frame_extractor import FrameExtractor
from .crowd_counter import CrowdCounter, CrowdCountResult
from .risk_classifier import RiskClassifier, RiskLevel, RiskAssessment
from .trend_analyzer import TrendAnalyzer, TrendMetrics, CrowdDataPoint
from .heatmap_generator import HeatmapGenerator
from .geo_matcher import GeoMatcher, GeoZone, Point
from .notifier import Notifier, AlertChannel, AlertMessage
from .rate_limiter import RateLimiter
from .task_queue import TaskQueue, Task, TaskPriority, TaskStatus

__all__ = [
    "FrameExtractor",
    "CrowdCounter",
    "CrowdCountResult",
    "RiskClassifier",
    "RiskLevel",
    "RiskAssessment",
    "TrendAnalyzer",
    "TrendMetrics",
    "CrowdDataPoint",
    "HeatmapGenerator",
    "GeoMatcher",
    "GeoZone",
    "Point",
    "Notifier",
    "AlertChannel",
    "AlertMessage",
    "RateLimiter",
    "TaskQueue",
    "Task",
    "TaskPriority",
    "TaskStatus",
]
