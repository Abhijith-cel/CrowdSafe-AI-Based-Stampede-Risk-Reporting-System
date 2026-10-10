"""Crowd counter: counts people in one image with YOLOv8.

Deliberately has NO fallback estimator. If the model can't load, count()
raises CounterUnavailableError so the caller can tell the user the AI is
down, instead of silently returning a made-up number. (The earlier version
fell back to counting edge contours, which says nothing about people.)

Swap point: to move to CSRNet later, keep the same count(image) -> CountResult
contract and change only the internals of this file.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# backend/models_pretrained/ (this file is backend/app/services/crowd_counter.py)
MODELS_DIR = Path(__file__).resolve().parents[2] / "models_pretrained"


class CounterUnavailableError(RuntimeError):
    """The detection model could not be loaded or run."""


@dataclass
class CountResult:
    count: int
    avg_confidence: float
    backend: str  # e.g. "yolov8n"


class CrowdCounter:
    # imgsz 1280 (default is 640) helps find small, distant people in crowds.
    # conf/imgsz are starting points: tune them against real crowd photos.
    def __init__(self, weights: str = "yolov8n.pt", conf: float = 0.25, imgsz: int = 1280):
        self.weights = weights
        self.conf = conf
        self.imgsz = imgsz
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is not None:
                return self._model
            try:
                from ultralytics import YOLO  # imported lazily: heavy

                local = MODELS_DIR / self.weights
                # If the file isn't in models_pretrained/, ultralytics downloads it by name.
                self._model = YOLO(str(local) if local.exists() else self.weights)
            except Exception as exc:
                raise CounterUnavailableError(f"Could not load model '{self.weights}': {exc}") from exc
        return self._model

    def count(self, image: Any) -> CountResult:
        """image: BGR numpy array (as returned by cv2.imread / imdecode)."""
        model = self._load()
        try:
            results = model(image, conf=self.conf, imgsz=self.imgsz, classes=[0], verbose=False)
        except Exception as exc:
            raise CounterUnavailableError(f"Model inference failed: {exc}") from exc

        confs = [float(c) for r in results for c in r.boxes.conf.tolist()]
        n = len(confs)
        return CountResult(
            count=n,
            avg_confidence=round(sum(confs) / n, 3) if n else 0.0,
            backend=Path(self.weights).stem,
        )