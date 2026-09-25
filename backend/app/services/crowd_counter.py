"""Crowd Counter Service for CrowdSafe.

Performs person detection, head counting, and crowd density estimation
on video frames using pluggable model backends (YOLO, CSRNet, or heuristic fallback).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


@dataclass
class DetectionBox:
    """Bounding box for a detected person."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: float
    class_id: int = 0  # 0: person


@dataclass
class CrowdCountResult:
    """Output summary of crowd counting on a single frame."""

    total_count: int
    density_per_sq_meter: float
    confidence_avg: float
    timestamp: float = field(default_factory=time.time)
    boxes: List[DetectionBox] = field(default_factory=list)
    density_map: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CrowdCounter:
    """Detects and estimates crowd head count and spatial density."""

    def __init__(
        self,
        model_name: str = "default",
        confidence_threshold: float = 0.35,
        default_area_sqm: float = 50.0,
    ) -> None:
        """Initialize the crowd counter.

        Args:
            model_name: Backend model identifier (e.g., 'yolov8n', 'csrnet', 'default').
            confidence_threshold: Minimum detection confidence score.
            default_area_sqm: Estimated physical ground area visible in frame (square meters).
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.default_area_sqm = max(1.0, default_area_sqm)
        self._model = None
        self._initialized = False

    def load_model(self) -> None:
        """Load detection model weights into memory if configured."""
        try:
            # Example optional integration with Ultralytics YOLO if available
            from ultralytics import YOLO  # type: ignore
            self._model = YOLO(self.model_name if self.model_name != "default" else "yolov8n.pt")
            self._initialized = True
            logger.info("Loaded YOLO model for crowd counting.")
        except Exception as e:
            logger.info(
                "Deep learning framework not loaded (%s). Running in lightweight heuristic estimation mode.",
                e,
            )
            self._model = None
            self._initialized = True

    def count(
        self,
        frame: Any,
        area_sq_meters: Optional[float] = None,
        timestamp: Optional[float] = None,
    ) -> CrowdCountResult:
        """Count individuals and calculate density in the given frame.

        Args:
            frame: Image array (numpy ndarray, PIL image, or raw representation).
            area_sq_meters: Monitored ground area in square meters.
            timestamp: Time of frame capture (seconds).

        Returns:
            CrowdCountResult containing total count, density, and detection details.
        """
        if not self._initialized:
            self.load_model()

        area = area_sq_meters if area_sq_meters and area_sq_meters > 0 else self.default_area_sqm
        frame_time = timestamp if timestamp is not None else time.time()

        # If a real YOLO model is loaded
        if self._model is not None:
            return self._infer_yolo(frame, area, frame_time)

        # Baseline heuristic / image analysis fallback
        return self._infer_heuristic(frame, area, frame_time)

    def _infer_yolo(self, frame: Any, area: float, frame_time: float) -> CrowdCountResult:
        """Run inference using loaded YOLO detector."""
        results = self._model(frame, conf=self.confidence_threshold, verbose=False)
        boxes: List[DetectionBox] = []
        conf_sum = 0.0

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                # Class 0 in COCO is 'person'
                if cls_id == 0 and conf >= self.confidence_threshold:
                    xyxy = box.xyxy[0].tolist()
                    boxes.append(
                        DetectionBox(
                            x_min=xyxy[0],
                            y_min=xyxy[1],
                            x_max=xyxy[2],
                            y_max=xyxy[3],
                            confidence=conf,
                            class_id=cls_id,
                        )
                    )
                    conf_sum += conf

        total = len(boxes)
        avg_conf = (conf_sum / total) if total > 0 else 1.0
        density = round(total / area, 3)

        return CrowdCountResult(
            total_count=total,
            density_per_sq_meter=density,
            confidence_avg=round(avg_conf, 3),
            timestamp=frame_time,
            boxes=boxes,
            metadata={"backend": "yolo", "model": self.model_name},
        )

    def _infer_heuristic(self, frame: Any, area: float, frame_time: float) -> CrowdCountResult:
        """Baseline estimation based on image contours or basic edge density when DL engine is absent."""
        total = 0
        boxes: List[DetectionBox] = []

        try:
            import cv2
            import numpy as np

            if isinstance(frame, np.ndarray):
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
                # Apply Gaussian Blur and threshold
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                edges = cv2.Canny(blurred, 50, 150)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for cnt in contours:
                    area_cnt = cv2.contourArea(cnt)
                    if 100 < area_cnt < 5000:
                        x, y, w, h = cv2.boundingRect(cnt)
                        boxes.append(
                            DetectionBox(
                                x_min=float(x),
                                y_min=float(y),
                                x_max=float(x + w),
                                y_max=float(y + h),
                                confidence=0.5,
                            )
                        )
                total = len(boxes)
        except Exception:
            total = 0

        density = round(total / area, 3) if area > 0 else 0.0

        return CrowdCountResult(
            total_count=total,
            density_per_sq_meter=density,
            confidence_avg=0.5 if total > 0 else 1.0,
            timestamp=frame_time,
            boxes=boxes,
            metadata={"backend": "heuristic_edge_detection"},
        )

    def batch_count(
        self,
        frames: List[Any],
        area_sq_meters: Optional[float] = None,
    ) -> List[CrowdCountResult]:
        """Process multiple frames in sequence."""
        return [self.count(f, area_sq_meters=area_sq_meters) for f in frames]
