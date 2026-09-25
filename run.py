"""CrowdSafe Application Entry Point.

Starts the Flask backend server with background tasks and routes.
"""

import os
import sys

# Ensure backend root is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1")
    print(f"[*] Starting CrowdSafe Server on port {port} (debug={debug})...")
    app.run(host="0.0.0.0", port=port, debug=debug)
