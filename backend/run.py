"""
Dev entry point. Run from inside backend/ with the venv activated:

    (venv) PS ...\backend> python run.py

Starts on http://localhost:5000 — matches the VITE_API_BASE default already
baked into frontend/src/reportsApi.js.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)