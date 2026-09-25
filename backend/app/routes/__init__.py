"""API Routes Package for CrowdSafe."""

from .auth_routes import auth_bp
from .report_routes import report_bp
from .authority_routes import authority_bp
from .analytics_routes import analytics_bp

__all__ = [
    "auth_bp",
    "report_bp",
    "authority_bp",
    "analytics_bp",
]
