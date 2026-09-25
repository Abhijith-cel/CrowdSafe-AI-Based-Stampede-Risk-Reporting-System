"""Heatmap Generator Service for CrowdSafe.

Converts person detection points or head coordinates into spatial crowd
density heatmaps, generating visual overlays on camera frames and matrix grids
for web dashboards.
"""

from __future__ import annotations

import base64
import logging
from typing import Any, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    CV2_AVAILABLE = False


class HeatmapGenerator:
    """Generates 2D spatial crowd density heatmaps from detection coordinates."""

    def __init__(
        self,
        kernel_size: int = 45,
        colormap: str = "JET",
        alpha_blend: float = 0.5,
    ) -> None:
        """Initialize the heatmap generator.

        Args:
            kernel_size: Gaussian blur kernel size (must be an odd integer).
            colormap: OpenCV colormap name ('JET', 'TURBO', 'HOT', 'INFERNO').
            alpha_blend: Opacity of heatmap overlay on original frame (0.0 to 1.0).
        """
        self.kernel_size = kernel_size if (kernel_size % 2 != 0) else kernel_size + 1
        self.colormap_name = colormap
        self.alpha_blend = alpha_blend

    def _get_cv2_colormap(self) -> int:
        """Map colormap string to OpenCV colormap constant."""
        if not CV2_AVAILABLE:
            return 2  # cv2.COLORMAP_JET fallback
        maps = {
            "JET": cv2.COLORMAP_JET,
            "TURBO": getattr(cv2, "COLORMAP_TURBO", cv2.COLORMAP_JET),
            "HOT": cv2.COLORMAP_HOT,
            "INFERNO": getattr(cv2, "COLORMAP_INFERNO", cv2.COLORMAP_JET),
        }
        return maps.get(self.colormap_name.upper(), cv2.COLORMAP_JET)

    def generate_density_matrix(
        self,
        points: List[Tuple[float, float]],
        width: int,
        height: int,
    ) -> Any:
        """Generate a smoothed 2D numpy matrix representing crowd density.

        Args:
            points: List of (x, y) coordinates for detected people/heads.
            width: Width of image/grid.
            height: Height of image/grid.

        Returns:
            2D numpy array normalized between 0.0 and 1.0.
        """
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV and NumPy are required for heatmap generation.")

        density_map = np.zeros((height, width), dtype=np.float32)

        for x, y in points:
            ix, iy = int(round(x)), int(round(y))
            if 0 <= ix < width and 0 <= iy < height:
                density_map[iy, ix] += 1.0

        # Apply Gaussian filter to smooth points into continuous density
        if len(points) > 0 and self.kernel_size > 1:
            density_map = cv2.GaussianBlur(
                density_map, (self.kernel_size, self.kernel_size), 0
            )

        max_val = np.max(density_map)
        if max_val > 0:
            density_map = density_map / max_val

        return density_map

    def generate_overlay(
        self,
        frame: Any,
        points: List[Tuple[float, float]],
    ) -> Any:
        """Overlay colored crowd density heatmap on top of the original video frame.

        Args:
            frame: Input image array (BGR format).
            points: List of (x, y) coordinates of detected people.

        Returns:
            Blended image array with heatmap overlay.
        """
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV and NumPy are required for heatmap overlay.")

        if frame is None or len(points) == 0:
            return frame

        h, w = frame.shape[:2]
        density_matrix = self.generate_density_matrix(points, w, h)

        # Convert normalized float matrix to 8-bit image
        density_8u = np.uint8(255 * density_matrix)

        # Colorize using chosen colormap
        colored_map = cv2.applyColorMap(density_8u, self._get_cv2_colormap())

        # Blend with original frame
        blended = cv2.addWeighted(
            colored_map,
            self.alpha_blend,
            frame,
            1.0 - self.alpha_blend,
            0,
        )
        return blended

    def to_base64_image(self, frame: Any, format_ext: str = ".jpg") -> str:
        """Encode image array to base64 string for API transmission or web rendering."""
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV and NumPy are required for base64 image export.")

        success, buffer = cv2.imencode(format_ext, frame)
        if not success:
            raise RuntimeError("Failed to encode frame to image buffer.")

        encoded = base64.b64encode(buffer).decode("utf-8")
        mime = "image/jpeg" if format_ext.lower() in [".jpg", ".jpeg"] else "image/png"
        return f"data:{mime};base64,{encoded}"

    def generate_grid_summary(
        self,
        points: List[Tuple[float, float]],
        frame_width: int,
        frame_height: int,
        grid_rows: int = 5,
        grid_cols: int = 5,
    ) -> List[List[int]]:
        """Divide space into a discrete NxM grid and count occupants per cell.

        Useful for lightweight JSON API payloads and low-bandwidth clients.
        """
        grid = [[0 for _ in range(grid_cols)] for _ in range(grid_rows)]
        col_width = frame_width / max(1, grid_cols)
        row_height = frame_height / max(1, grid_rows)

        for x, y in points:
            c = min(grid_cols - 1, max(0, int(x // col_width)))
            r = min(grid_rows - 1, max(0, int(y // row_height)))
            grid[r][c] += 1

        return grid
