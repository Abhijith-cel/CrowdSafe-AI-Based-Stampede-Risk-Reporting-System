"""Notifier Service for CrowdSafe.

Handles real-time automated dispatch of stampede warnings and safety
recommendations across multiple channels (WebSockets, Webhooks, SMS, Email, and Control Room console).
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)


class AlertChannel(str, Enum):
    """Supported delivery channels for safety alerts."""

    CONSOLE = "CONSOLE"
    WEBSOCKET = "WEBSOCKET"
    WEBHOOK = "WEBHOOK"
    SMS = "SMS"
    EMAIL = "EMAIL"


@dataclass
class AlertMessage:
    """Standardized safety alert payload for stampede risk dispatch."""

    alert_id: str
    risk_level: str  # LOW, MODERATE, HIGH, CRITICAL
    zone_id: str
    zone_name: str
    risk_score: float
    current_density: float
    headcount: int
    recommendation: str
    channels: List[AlertChannel]
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert message to serializable dictionary."""
        data = asdict(self)
        data["channels"] = [c.value if isinstance(c, AlertChannel) else str(c) for c in self.channels]
        return data

    def to_json(self) -> str:
        """Serialize alert message to JSON string."""
        return json.dumps(self.to_dict())


class Notifier:
    """Dispatches safety notifications to registered subscribers and channels."""

    def __init__(self) -> None:
        """Initialize Notifier with channel listeners."""
        self._handlers: Dict[AlertChannel, List[Callable[[AlertMessage], Any]]] = {
            channel: [] for channel in AlertChannel
        }
        # Setup default console logger
        self.register_handler(AlertChannel.CONSOLE, self._default_console_handler)

    def register_handler(
        self,
        channel: AlertChannel,
        handler: Callable[[AlertMessage], Any],
    ) -> None:
        """Register a callback handler for a specific notification channel."""
        self._handlers[channel].append(handler)

    def _default_console_handler(self, alert: AlertMessage) -> None:
        """Default logging output for all generated alerts."""
        log_msg = (
            f"[{alert.risk_level}] Zone: {alert.zone_name} ({alert.zone_id}) | "
            f"Score: {alert.risk_score} | Density: {alert.current_density} p/m² | "
            f"Recommendation: {alert.recommendation}"
        )
        if alert.risk_level == "CRITICAL":
            logger.critical(log_msg)
        elif alert.risk_level == "HIGH":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

    async def dispatch(self, alert: AlertMessage) -> Dict[str, bool]:
        """Dispatch alert to all channels specified in the AlertMessage.

        Returns:
            Dict mapping channel name to delivery status.
        """
        results: Dict[str, bool] = {}

        for channel in alert.channels:
            handlers = self._handlers.get(channel, [])
            results[channel.value] = True

            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(alert)
                    else:
                        handler(alert)
                except Exception as e:
                    logger.error("Failed dispatching alert on channel %s: %s", channel.value, e)
                    results[channel.value] = False

        return results

    def dispatch_sync(self, alert: AlertMessage) -> Dict[str, bool]:
        """Synchronous dispatch helper for non-async execution contexts."""
        results: Dict[str, bool] = {}

        for channel in alert.channels:
            handlers = self._handlers.get(channel, [])
            results[channel.value] = True

            for handler in handlers:
                try:
                    res = handler(alert)
                    if asyncio.iscoroutine(res):
                        asyncio.run(res)
                except Exception as e:
                    logger.error("Failed sync dispatch on channel %s: %s", channel.value, e)
                    results[channel.value] = False

        return results
