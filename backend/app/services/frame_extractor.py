"""Frame Extractor Service for CrowdSafe.

Responsible for ingesting video files or RTSP/CCTV live streams,
sampling frames at configured intervals or target frame rates,
and yielding normalized frames for downstream crowd density and risk models.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator, Optional, Tuple, Union

logger = logging.getLogger(__name__)

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
    OPENCV_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    OPENCV_AVAILABLE = False


@dataclass
class VideoMetadata:
    """Metadata describing a video source."""

    total_frames: int
    fps: float
    duration_seconds: float
    width: int
    height: int


class FrameExtractor:
    """Extracts frames from video files, recorded feeds, or live RTSP streams."""

    def __init__(self, default_target_fps: float = 2.0, resize_dims: Optional[Tuple[int, int]] = None) -> None:
        """Initialize frame extractor configuration.

        Args:
            default_target_fps: Default sampling rate in frames per second.
            resize_dims: Optional tuple of (width, height) to resize frames.
        """
        self.default_target_fps = default_target_fps
        self.resize_dims = resize_dims

    def check_dependencies(self) -> None:
        """Verify that required video processing dependencies are available."""
        if not OPENCV_AVAILABLE:
            raise ImportError(
                "OpenCV ('cv2') and 'numpy' are required for FrameExtractor. "
                "Install them via 'pip install opencv-python numpy'."
            )

    def get_video_metadata(self, source_path: Union[str, Path]) -> VideoMetadata:
        """Read video stream metadata without loading all frames into memory."""
        self.check_dependencies()
        cap = cv2.VideoCapture(str(source_path))
        if not cap.isOpened():
            raise ValueError(f"Unable to open video source: {source_path}")

        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = (total_frames / fps) if fps > 0 else 0.0

            return VideoMetadata(
                total_frames=total_frames,
                fps=fps,
                duration_seconds=duration,
                width=width,
                height=height,
            )
        finally:
            cap.release()

    def extract_from_file(
        self,
        video_path: Union[str, Path],
        target_fps: Optional[float] = None,
        max_frames: Optional[int] = None,
    ) -> Generator[Tuple[int, float, Any], None, None]:
        """Extract frames sequentially from a video file at a target sampling rate.

        Args:
            video_path: Path to the video file.
            target_fps: Sample rate in FPS (defaults to self.default_target_fps).
            max_frames: Maximum total frames to extract.

        Yields:
            Tuple of (frame_index, timestamp_seconds, frame_ndarray).
        """
        self.check_dependencies()
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Unable to open video file: {video_path}")

        fps = target_fps or self.default_target_fps
        native_fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
        frame_interval = max(1, int(round(native_fps / fps))) if fps > 0 else 1

        extracted_count = 0
        current_frame_idx = 0

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if current_frame_idx % frame_interval == 0:
                    timestamp = current_frame_idx / native_fps

                    if self.resize_dims:
                        frame = cv2.resize(frame, self.resize_dims)

                    yield current_frame_idx, timestamp, frame
                    extracted_count += 1

                    if max_frames and extracted_count >= max_frames:
                        break

                current_frame_idx += 1
        finally:
            cap.release()

    def extract_frame_at_timestamp(
        self,
        video_path: Union[str, Path],
        timestamp_sec: float,
    ) -> Optional[Any]:
        """Seek and extract a single frame at an exact timestamp."""
        self.check_dependencies()
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return None

        try:
            msec = timestamp_sec * 1000.0
            cap.set(cv2.CAP_PROP_POS_MSEC, msec)
            ret, frame = cap.read()
            if not ret:
                return None
            if self.resize_dims:
                frame = cv2.resize(frame, self.resize_dims)
            return frame
        finally:
            cap.release()

    def extract_from_stream(
        self,
        stream_url: str,
        sample_interval_sec: float = 1.0,
        max_duration_sec: Optional[float] = None,
    ) -> Generator[Tuple[int, float, Any], None, None]:
        """Extract sampled frames from an RTSP, HTTP, or device live video stream."""
        self.check_dependencies()
        cap = cv2.VideoCapture(stream_url)
        if not cap.isOpened():
            raise ConnectionError(f"Failed to connect to stream: {stream_url}")

        import time

        start_time = time.time()
        last_sample_time = 0.0
        frame_idx = 0

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Stream frame read failed or connection lost.")
                    break

                now = time.time()
                elapsed = now - start_time
                if max_duration_sec and elapsed > max_duration_sec:
                    break

                if (now - last_sample_time) >= sample_interval_sec:
                    last_sample_time = now
                    if self.resize_dims:
                        frame = cv2.resize(frame, self.resize_dims)
                    yield frame_idx, elapsed, frame

                frame_idx += 1
        finally:
            cap.release()
