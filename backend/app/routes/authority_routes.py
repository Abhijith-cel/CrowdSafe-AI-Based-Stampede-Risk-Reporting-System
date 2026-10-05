"""
Authority dashboard API.

Serves the React dashboard (frontend/src/reportsApi.js) exactly the report
shape it already expects:
  { id, lat, long, risk_level, media_type, media_url, timestamp,
    context_tag, status, person_count, location_name }

Note on sessions: database.py's get_db() is a generator meant for a
framework that calls next()/close() around a request for you (FastAPI-style
Depends). Flask has no equivalent built in, so routes here open a
SessionLocal() directly inside a small context manager instead — same
engine/session factory, just consumed the way plain Flask expects.
"""

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request

from app.database import SessionLocal
from app.models import Alert, Report

authority_bp = Blueprint("authority", __name__, url_prefix="/api/authority")


@contextmanager
def db_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def serialize_report(report: Report, host_url: str) -> dict:
    # "new" vs "acknowledged" comes from Alert, not Report.status —
    # Report.status ("PENDING" by default) tracks AI-pipeline progress, a
    # separate concern from whether an authority has acknowledged it.
    alert = report.alerts[0] if report.alerts else None
    acknowledged = bool(alert and alert.acknowledged_at)

    # Assumes media_path's filename matches a real file under
    # backend/app/uploads/. Manually-seeded test rows need a matching real
    # file there (or this will 404 in the browser) — this isn't enforced
    # here since report_routes.py (the real upload writer) doesn't exist yet.
    filename = Path(report.media_path).name if report.media_path else None
    media_url = f"{host_url}uploads/{filename}" if filename else None

    return {
        "id": report.id,
        "lat": float(report.lat) if report.lat is not None else None,
        "long": float(report.long) if report.long is not None else None,
        # Defaults to "Low" if null so the frontend's color lookup never
        # breaks — but that means un-set test rows will silently show as
        # Low risk. Set risk_level explicitly on every seeded row for now,
        # since risk_classifier.py doesn't exist yet to fill this in.
        "risk_level": report.risk_level or "Low",
        "media_type": report.media_type,
        "media_url": media_url,
        "timestamp": report.submitted_at.isoformat() if report.submitted_at else None,
        "context_tag": report.context_tag,
        "status": "acknowledged" if acknowledged else "new",
        "person_count": report.person_count,
        "location_name": report.location_name or f"{report.lat}, {report.long}",
    }


@authority_bp.route("/reports", methods=["GET"])
def list_reports():
    with db_session() as db:
        reports = db.query(Report).order_by(Report.submitted_at.desc()).all()
        data = [serialize_report(r, request.host_url) for r in reports]
    return jsonify(data)


@authority_bp.route("/reports/<int:report_id>/acknowledge", methods=["POST"])
def acknowledge_report(report_id):
    with db_session() as db:
        report = db.query(Report).filter(Report.id == report_id).first()
        if report is None:
            return jsonify({"error": "Report not found"}), 404

        alert = db.query(Alert).filter(Alert.report_id == report_id).first()
        now = datetime.utcnow()
        if alert is None:
            # No Alert row yet — expected until geo_matcher.py exists and
            # creates one automatically on upload. Create it here so
            # acknowledging still works against manually-seeded reports.
            alert = Alert(report_id=report_id, status="ACKNOWLEDGED", acknowledged_at=now)
            db.add(alert)
        else:
            alert.status = "ACKNOWLEDGED"
            alert.acknowledged_at = now
        # acknowledged_by (a user id) is intentionally left unset: this
        # build has no login, so there's no authenticated user to credit.

        db.flush()
        updated = serialize_report(report, request.host_url)
    return jsonify(updated)