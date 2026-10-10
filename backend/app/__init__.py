import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from app.routes.authority_routes import authority_bp
from app.routes.report_routes import report_bp

UPLOADS_DIR = Path(__file__).resolve().parent / "uploads"

# Comma-separated list in the CORS_ORIGINS env var overrides this (needed once the
# frontend is opened from a phone via an HTTPS tunnel URL).
DEFAULT_ORIGINS = ["http://localhost:5173", "http://localhost:5174"]


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024  # 15 MB per upload

    origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()] or DEFAULT_ORIGINS
    CORS(app, resources={r"/api/*": {"origins": origins}})

    app.register_blueprint(authority_bp)
    app.register_blueprint(report_bp)

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify({"error": "Photo is too large (max 15 MB)"}), 413

    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        return send_from_directory(UPLOADS_DIR, filename)

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app