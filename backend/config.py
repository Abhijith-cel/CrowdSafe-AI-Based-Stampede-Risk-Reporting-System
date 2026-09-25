"""Application Configuration for CrowdSafe Backend."""

import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base configuration settings."""

    # Environment
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1")
    SECRET_KEY = os.getenv("SECRET_KEY", "crowdsafe-dev-secret-key-replace-in-production")

    # Database (PostgreSQL default with fallback)
    DB_USER = os.getenv("POSTGRES_USER", "postgres")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "crowdsafe_db")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # JWT Authentication
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "crowdsafe-jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_EXPIRY_HOURS", "8")))

    # File Uploads
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "app" / "uploads"))
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB max upload limit
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "mp4", "avi", "mov", "mkv"}

    # Model Weights Path
    MODELS_DIR = os.getenv("MODELS_DIR", str(BASE_DIR / "models_pretrained"))
    YOLO_WEIGHTS_PATH = str(Path(MODELS_DIR) / "yolov8n.pt")
    CSRNET_WEIGHTS_PATH = str(Path(MODELS_DIR) / "CSRNet_ShanghaiTech_A.pth")

    # Stampede Safety Standards & Thresholds (persons per square meter)
    DENSITY_LOW_MAX = float(os.getenv("DENSITY_LOW_MAX", "2.0"))        # Free movement (LOS A-C)
    DENSITY_MODERATE_MAX = float(os.getenv("DENSITY_MODERATE_MAX", "3.5")) # Restrained (LOS D-E)
    DENSITY_HIGH_MAX = float(os.getenv("DENSITY_HIGH_MAX", "5.0"))      # High Risk (LOS F)
    # > 5.0 is CRITICAL (Immediate crush/asphyxia risk)

    # Surge & Trend Alert Thresholds
    SURGE_THRESHOLD_RATE = float(os.getenv("SURGE_THRESHOLD_RATE", "15.0")) # +15 persons/min
    ALERT_COOLDOWN_SECONDS = int(os.getenv("ALERT_COOLDOWN_SECONDS", "60")) # 60s between duplicate alerts

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")


class DevelopmentConfig(Config):
    """Development environment specific settings."""
    DEBUG = True


class ProductionConfig(Config):
    """Production environment specific settings."""
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
