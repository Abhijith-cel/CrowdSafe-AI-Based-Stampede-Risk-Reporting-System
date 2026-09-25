"""Analytics and historical trend routes for CrowdSafe."""

from flask import Blueprint, jsonify, request
from ..database import db
from ..models import CrowdTelemetry, Report, Zone
from ..services import HeatmapGenerator

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")
heatmap_generator = HeatmapGenerator()


@analytics_bp.route("/summary", methods=["GET"])
def get_analytics_summary():
    """Retrieve aggregate statistics, peak densities, and total counts."""
    reports = Report.query.all()
    total_incidents = len(reports)
    critical_incidents = sum(1 for r in reports if r.risk_level == "CRITICAL")
    high_incidents = sum(1 for r in reports if r.risk_level == "HIGH")
    avg_density = (sum(r.density for r in reports) / total_incidents) if total_incidents > 0 else 0.0
    max_density = max((r.density for r in reports), default=0.0)

    # Risk level distribution breakdown
    distribution = {
        "LOW": sum(1 for r in reports if r.risk_level == "LOW"),
        "MODERATE": sum(1 for r in reports if r.risk_level == "MODERATE"),
        "HIGH": high_incidents,
        "CRITICAL": critical_incidents,
    }

    return jsonify({
        "total_incidents": total_incidents,
        "critical_incidents": critical_incidents,
        "high_incidents": high_incidents,
        "avg_density": round(avg_density, 2),
        "peak_density": round(max_density, 2),
        "risk_distribution": distribution,
    }), 200


@analytics_bp.route("/trends/<int:zone_id>", methods=["GET"])
def get_zone_trends(zone_id: int):
    """Retrieve time-series crowd telemetry for Chart.js graphing."""
    zone = Zone.query.get(zone_id)
    if not zone:
        return jsonify({"error": f"Zone {zone_id} not found"}), 404

    limit = min(int(request.args.get("limit", 50)), 200)
    telemetries = (
        CrowdTelemetry.query.filter_by(zone_id=zone_id)
        .order_by(CrowdTelemetry.timestamp.desc())
        .limit(limit)
        .all()
    )

    # Reverse to chronological order for line charts
    chronological = list(reversed(telemetries))

    return jsonify({
        "zone": zone.to_dict(),
        "timestamps": [t.timestamp.strftime("%H:%M:%S") for t in chronological],
        "headcounts": [t.headcount for t in chronological],
        "densities": [t.density for t in chronological],
        "surge_rates": [t.surge_rate for t in chronological],
    }), 200


@analytics_bp.route("/heatmap/<int:zone_id>", methods=["GET"])
def get_zone_heatmap_grid(zone_id: int):
    """Return a spatial discrete density grid matrix for the zone."""
    zone = Zone.query.get(zone_id)
    if not zone:
        return jsonify({"error": f"Zone {zone_id} not found"}), 404

    # Generate sample 5x5 spatial grid based on latest reports
    latest_report = (
        Report.query.filter_by(zone_id=zone_id)
        .order_by(Report.created_at.desc())
        .first()
    )
    count = latest_report.estimated_count if latest_report else 10

    # Synthetic distribution for grid demo
    import random
    rows, cols = 5, 5
    grid = [[0 for _ in range(cols)] for _ in range(rows)]
    for _ in range(count):
        r = min(rows - 1, max(0, int(random.gauss(rows / 2, 0.8))))
        c = min(cols - 1, max(0, int(random.gauss(cols / 2, 0.8))))
        grid[r][c] += 1

    return jsonify({
        "zone_id": zone_id,
        "zone_name": zone.name,
        "grid_rows": rows,
        "grid_cols": cols,
        "density_grid": grid,
        "total_count": count,
    }), 200
