from pathlib import Path

from flask import Flask, send_from_directory
from flask_cors import CORS

from app.routes.authority_routes import authority_bp

# backend/app/uploads/ — where citizen-uploaded photos/videos will live once
# report_routes.py exists. Serving them here so media_url in API responses
# is a real, loadable link for the dashboard's photo/video panel.
UPLOADS_DIR = Path(__file__).resolve().parent / "uploads"


def create_app():
    app = Flask(__name__)

    # Dev-only CORS: the React dashboard runs on Vite's dev server
    # (localhost:5173 by default) while Flask runs on localhost:5000 — two
    # different origins, so the browser blocks the fetch() without this.
    # Tighten the origin list before any real deployment.
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://localhost:5174"]}})

    app.register_blueprint(authority_bp)

    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        return send_from_directory(UPLOADS_DIR, filename)

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app