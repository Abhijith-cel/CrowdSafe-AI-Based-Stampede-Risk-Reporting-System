"""Crowd counter: estimates how many people are in one photo using a density-map model.

Why not YOLO: person detectors look for whole bodies, and in packed crowds people
overlap so much that they find only a fraction (on our test photo: 20-46 found vs
about 100 present). Density-map models (DM-Count here) estimate head counts directly
and are built for exactly this case.

Still an ESTIMATE from a single photo. Known weakness to check on real photos: density
models can report a few "people" in empty, textured scenes.

There is no fallback estimator: if the model can't load or run, count() raises
CounterUnavailableError so the caller can say the AI is down instead of inventing
a number.

Swap point: keep count(image) -> CountResult and change only this file to try a
different model (e.g. model_name="CSRNet", weights="SHA").
"""

from __future__ import annotations

import logging
import os
import tempfile
import threading
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


class CounterUnavailableError(RuntimeError):
    """The counting model could not be loaded or run."""


@dataclass
class CountResult:
    count: int
    backend: str  # e.g. "DM-Count/QNRF"


class CrowdCounter:
    # max_side: photos larger than this (in pixels, longest side) are shrunk first.
    # The library processes the full-size image, which is slow / memory-hungry for
    # 12 MP phone photos. Shrinking can lose tiny far-away heads in very dense crowds,
    # so raise it if far crowds look undercounted and your machine can take it.
    def __init__(self, model_name: str = "DM-Count", weights: str = "QNRF", max_side: int = 1600):
        self.model_name = model_name
        self.weights = weights
        self.max_side = max_side
        self._model = None
        self._load_lock = threading.Lock()
        self._infer_lock = threading.Lock()  # one inference at a time: CPU-bound, avoids thrashing

    def _load(self):
        if self._model is not None:
            return self._model
        with self._load_lock:
            if self._model is None:
                try:
                    from lwcc import LWCC  # imported lazily: pulls in PyTorch

                    # First run downloads the weights (~86 MB) to C:\.lwcc\weights
                    self._model = LWCC.load_model(model_name=self.model_name, model_weights=self.weights)
                except Exception as exc:
                    raise CounterUnavailableError(
                        f"Could not load {self.model_name}/{self.weights}: {exc}"
                    ) from exc
        return self._model

    def count(self, image: Any) -> CountResult:
        """image: BGR numpy array (as from cv2.imread / cv2.imdecode)."""
        import cv2
        from lwcc import LWCC

        model = self._load()

        h, w = image.shape[:2]
        scale = self.max_side / max(h, w)
        if scale < 1:
            image = cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)

        # The library only accepts a file path, so hand it a temporary JPEG.
        fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        try:
            if not cv2.imwrite(tmp_path, image):
                raise RuntimeError("could not write temporary image")
            with self._infer_lock:
                value = LWCC.get_count(tmp_path, model=model, resize_img=False)
        except Exception as exc:
            raise CounterUnavailableError(f"Model inference failed: {exc}") from exc
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

        return CountResult(count=max(0, round(float(value))), backend=f"{self.model_name}/{self.weights}")