"""Authority and security command dashboard routes."""

from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from ..database import db
from ..models import Alert, CrowdTelemetry, Report, User, Zone

authority_bp = Blueprint("authority", __name__, url_prefix="/api/authority")


@authority_bp.route("/dashboard", methods=["GET"])
def get_dashboard_summary():
    """Aggregate high-level situational awareness metrics for authorities."""
    total_zones = Zone.query.count()
    active_alerts = Alert.query.filter_by(is_active=True).count()
    critical_alerts = Alert.query.filter_by(is_active=True, risk_level="CRITICAL").count()
    high_alerts = Alert.query.filter_by(is_active=True, risk_level="HIGH").count()
    total_reports = Report.query.count()

    # Recent active alerts
    recent_alerts = (
        Alert.query.filter_by(is_active=True)
        .order_by(Alert.created_at.desc())
        .limit(10)
        .all()
    )

    # Zones with latest risk level
    zones = Zone.query.all()
    zone_summaries = []
    for z in zones:
        latest_report = (
            Report.query.filter_by(zone_id=z.id)
            .order_by(Report.created_at.desc())
            .first()
        )
        zone_summaries.append({
            "zone": z.to_dict(),
            "latest_risk_level": latest_report.risk_level if latest_report else "LOW",
            "latest_headcount": latest_report.estimated_count if latest_report else 0,
            "latest_density": latest_report.density if latest_report else 0.0,
            "capacity_percent": round(
                ((latest_report.estimated_count / z.capacity_limit) * 100) if (latest_report and z.capacity_limit > 0) else 0.0,
                1
            ),
        })

    return jsonify({
        "stats": {
            "total_zones": total_zones,
            "active_alerts": active_alerts,
            "critical_alerts": critical_alerts,
            "high_alerts": high_alerts,
            "total_reports": total_reports,
        },
        "recent_alerts": [a.to_dict() for a in recent_alerts],
        "zone_summaries": zone_summaries,
    }), 200


@authority_bp.route("/alerts", methods=["GET"])
def list_alerts():
    """List all active or historical emergency alerts."""
    is_active_filter = request.args.get("active", "true").lower() in ("true", "1")
    alerts = (
        Alert.query.filter_by(is_active=is_active_filter)
        .order_by(Alert.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify({"alerts": [a.to_dict() for a in alerts]}), 200


@authority_bp.route("/alerts/<int:alert_id>/acknowledge", methods=["POST"])
def acknowledge_alert(alert_id: int):
    """Mark an alert as acknowledged and resolved by responding authorities."""
    alert = Alert.query.get(alert_id)
    if not alert:
        return jsonify({"error": "Alert not found"}), 404

    data = request.get_json() or {}
    user_id = data.get("user_id")

    alert.is_active = False
    alert.acknowledged_by = int(user_id) if user_id and str(user_id).isdigit() else None
    alert.acknowledged_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "message": f"Alert {alert_id} acknowledged and marked as resolved",
        "alert": alert.to_dict(),
    }), 200


@authority_bp.route("/zones", methods=["GET"])
def list_zones():
    """List all registered venue zones."""
    zones = Zone.query.order_by(Zone.name.asc()).all()
    return jsonify({"zones": [z.to_dict() for z in zones]}), 200


@authority_bp.route("/zones", methods=["POST"])
def create_zone():
    """Register a new monitored zone or gate."""
    data = request.get_json() or {}
    zone_code = data.get("zone_code", "").strip()
    name = data.get("name", "").strip()
    zone_type = data.get("zone_type", "plaza").strip()
    latitude = float(data.get("latitude", 0.0))
    longitude = float(data.get("longitude", 0.0))
    area_sqm = float(data.get("area_sqm", 50.0))
    capacity_limit = int(data.get("capacity_limit", 200))
    is_bottleneck = bool(data.get("is_bottleneck", False))

    if not zone_code or not name:
        return jsonify({"error": "zone_code and name are required"}), 400

    if Zone.query.filter_by(zone_code=zone_code).first():
        return jsonify({"error": f"Zone code '{zone_code}' already exists"}), 409

    zone = Zone(
        zone_code=zone_code,
        name=name,
        zone_type=zone_type,
        latitude=latitude,
        longitude=longitude,
        area_sqm=area_sqm,
        capacity_limit=capacity_limit,
        is_bottleneck=is_bottleneck,
    )
    db.session.add(zone)
    db.session.commit()

    return jsonify({
        "message": "Zone created successfully",
        "zone": zone.to_dict(),
    }), 201


@authority_bp.route("/emergency-dispatch", methods=["POST"])
def trigger_emergency_dispatch():
    """Manual trigger to deploy marshals or open bypass gates."""
    data = request.get_json() or {}
    zone_id = data.get("zone_id")
    action_type = data.get("action_type", "DISPERSAL_DIRECTIVE")  # OPEN_GATES, DISPATCH_MARSHALS
    instruction = data.get("instruction", "Immediate crowd diversion required.")

    zone = Zone.query.get(int(zone_id)) if zone_id else None

    # Create emergency alert log
    alert = Alert(
        zone_id=zone.id if zone else 1,
        risk_level="CRITICAL",
        risk_score=95.0,
        message=f"[MANUAL EMERGENCY DISPATCH - {action_type}] Zone: {zone.name if zone else 'General'} | {instruction}",
    )
    db.session.add(alert)
    db.session.commit()

    return jsonify({
        "message": "Emergency dispatch command broadcasted to security teams",
        "alert": alert.to_dict(),
    }), 200
