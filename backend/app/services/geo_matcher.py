"""Geo Matcher Service for CrowdSafe.

Maps cameras and incidents to geographic coordinates, venue sectors,
corridor choke points, and evacuation routes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Point:
    """Represents a coordinate point (latitude/longitude or local metric Cartesian X/Y)."""

    x: float  # Longitude or X (meters)
    y: float  # Latitude or Y (meters)


@dataclass
class GeoZone:
    """Represents a monitored physical sector or venue zone."""

    zone_id: str
    name: str
    zone_type: str  # 'open_plaza', 'corridor', 'gate', 'stairwell', 'entry_exit'
    area_sqm: float
    safe_capacity: int
    polygon_boundary: List[Point] = field(default_factory=list)
    nearest_exits: List[str] = field(default_factory=list)
    is_bottleneck: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)


class GeoMatcher:
    """Manages spatial relationships, camera mapping, and bottleneck identification."""

    def __init__(self) -> None:
        """Initialize the GeoMatcher registry."""
        self._zones: Dict[str, GeoZone] = {}
        self._camera_to_zone: Dict[str, str] = {}
        self._exit_locations: Dict[str, Point] = {}

    def register_zone(self, zone: GeoZone) -> None:
        """Register a new venue zone or monitored sector."""
        self._zones[zone.zone_id] = zone

    def register_camera(self, camera_id: str, zone_id: str) -> None:
        """Bind a physical or virtual camera feed to a zone."""
        if zone_id not in self._zones:
            raise KeyError(f"Zone '{zone_id}' must be registered before mapping cameras.")
        self._camera_to_zone[camera_id] = zone_id

    def register_exit(self, exit_id: str, location: Point) -> None:
        """Register an emergency exit or dispersal gate location."""
        self._exit_locations[exit_id] = location

    def get_zone_by_camera(self, camera_id: str) -> Optional[GeoZone]:
        """Look up the zone monitored by a given camera."""
        zone_id = self._camera_to_zone.get(camera_id)
        if zone_id:
            return self._zones.get(zone_id)
        return None

    def get_zone(self, zone_id: str) -> Optional[GeoZone]:
        """Fetch zone details by zone_id."""
        return self._zones.get(zone_id)

    def list_zones(self) -> List[GeoZone]:
        """Return all registered zones."""
        return list(self._zones.values())

    def point_in_zone(self, point: Point, zone_id: str) -> bool:
        """Ray-casting algorithm to verify if a coordinate point lies within a zone polygon."""
        zone = self._zones.get(zone_id)
        if not zone or len(zone.polygon_boundary) < 3:
            return False

        poly = zone.polygon_boundary
        n = len(poly)
        inside = False

        p1x, p1y = poly[0].x, poly[0].y
        for i in range(n + 1):
            p2x, p2y = poly[i % n].x, poly[i % n].y
            if point.y > min(p1y, p2y):
                if point.y <= max(p1y, p2y):
                    if point.x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (point.y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or point.x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def find_nearest_exit(self, origin: Point) -> Tuple[Optional[str], float]:
        """Calculate Euclidean / Haversine distance to closest emergency exit.

        Returns:
            Tuple of (exit_id, distance_in_units).
        """
        if not self._exit_locations:
            return None, float("inf")

        closest_exit = None
        min_dist = float("inf")

        for exit_id, exit_pt in self._exit_locations.items():
            dist = math.hypot(exit_pt.x - origin.x, exit_pt.y - origin.y)
            if dist < min_dist:
                min_dist = dist
                closest_exit = exit_id

        return closest_exit, round(min_dist, 2)
