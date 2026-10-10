"""Citizen report ingestion: photo + GPS (+ optional address) -> AI count -> risk -> saved Report.

Uses the same SessionLocal/Report model as authority_routes.py, so what a citizen
submits shows up on the authority dashboard with no translation layer.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from flask import Blueprint, jsonify, request

from app.models import Alert, Report
from app.routes.authority_routes import db_session, serialize_report
from app.services.crowd_counter import CounterUnavailableError, CrowdCounter
from app.services.risk_classifier import RiskClassifier

logger = logging.getLogger(__name__)
report_bp = Blueprint("reports", __name__, url_prefix="/api/reports")

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"

counter = CrowdCounter()
classifier = RiskClassifier()

# ASSUMPTIONS, NOT MEASUREMENTS. A phone photo carries no ground-area information,
# so density (people per m2) needs an assumed visible area per location type.
# These numbers are placeholders to calibrate against real photos of real places
# (your open item: "per-context-tag density baselines"). The assumed area is
# returned in every response so the authority can see what the risk is based on.
CONTEXT_PROFILES = {
    #               assumed visible m2, treated as a bottleneck (raises risk score)
    "open_ground": {"area": 120.0, "bottleneck": False},
    "narrow_lane": {"area": 25.0, "bottleneck": True},
    "stairway": {"area": 15.0, "bottleneck": True},
    "platform": {"area": 60.0, "bottleneck": True},
}


def _bad(msg, code=400):
    return jsonify({"error": msg}), code


@report_bp.route("", methods=["POST"])
def submit_report():
    # ---- validate input (never trust the client) ----
    context_tag = request.form.get("context_tag", "")
    if context_tag not in CONTEXT_PROFILES:
        return _bad(f"context_tag must be one of: {', '.join(CONTEXT_PROFILES)}")

    try:
        lat = float(request.form["lat"])
        lng = float(request.form["long"])
    except (KeyError, ValueError):
        return _bad("lat and long are required numbers")
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return _bad("lat/long out of range")

    address = (request.form.get("address") or "").strip()[:150] or None

    file = request.files.get("file")
    if file is None or not file.filename:
        return _bad("A photo is required")

    # Decode the bytes as an image. This rejects non-images regardless of the
    # filename/extension the client claims.
    data = np.frombuffer(file.read(), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        return _bad("File is not a readable image (use JPG, PNG or WebP)")

    # ---- AI: fail loudly rather than invent a number ----
    try:
        result = counter.count(image)
    except CounterUnavailableError as exc:
        logger.error("Crowd counter unavailable: %s", exc)
        return _bad("The AI model is unavailable right now, so this report was NOT saved. Please try again.", 503)

    profile = CONTEXT_PROFILES[context_tag]
    density = round(result.count / profile["area"], 2)
    assessment = classifier.classify(
        density=density,
        headcount=result.count,
        is_bottleneck=profile["bottleneck"],
    )
    risk_label = assessment.level.value.title()  # "CRITICAL" -> "Critical" (dashboard labels)

    # ---- save the image: always re-encoded JPEG under a random name (no user filename
    # on disk, EXIF stripped); the DB stores the filename only ----
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.jpg"
    if not cv2.imwrite(str(UPLOADS_DIR / filename), image, [cv2.IMWRITE_JPEG_QUALITY, 90]):
        return _bad("Could not store the image", 500)

    with db_session() as db:
        report = Report(
            media_path=filename,
            media_type="image",
            lat=lat,
            long=lng,
            context_tag=context_tag,
            person_count=result.count,
            density_score=density,
            risk_level=risk_label,
            location_name=address,
            status="PROCESSED",
            processed_at=datetime.utcnow(),
        )
        db.add(report)
        db.flush()  # assigns report.id
        if risk_label in ("High", "Critical"):
            db.add(Alert(report_id=report.id, status="UNACKNOWLEDGED"))
        db.flush()
        db.refresh(report)
        payload = serialize_report(report, request.host_url)

    return jsonify({
        "report": payload,
        "assessment": {
            "risk_level": risk_label,
            "risk_score": assessment.risk_score,
            "recommendation": assessment.recommendation,
            "people_detected": result.count,
            "density_per_sqm": density,
            "assumed_area_sqm": profile["area"],
            "model": result.backend,
            "note": "Estimate from one photo using an assumed visible area; not a measurement.",
        },
    }), 201