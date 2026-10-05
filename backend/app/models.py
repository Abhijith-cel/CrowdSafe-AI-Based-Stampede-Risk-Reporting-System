from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, ForeignKey, TIMESTAMP, func
)
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="citizen")  # citizen | authority
    created_at = Column(TIMESTAMP, server_default=func.now())

    reports = relationship("Report", back_populates="user")


class Authority(Base):
    __tablename__ = "authorities"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    station_lat = Column(Numeric(9, 6), nullable=False)
    station_long = Column(Numeric(9, 6), nullable=False)
    jurisdiction_radius_km = Column(Numeric(5, 2), default=5.0)
    contact_email = Column(String(150))
    created_at = Column(TIMESTAMP, server_default=func.now())

    alerts = relationship("Alert", back_populates="authority")


class Zone(Base):
    """A monitored area (temple gate, station platform, market lane...)."""
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    center_lat = Column(Numeric(9, 6), nullable=False)
    center_long = Column(Numeric(9, 6), nullable=False)
    radius_m = Column(Integer, default=150)
    area_sq_m = Column(Numeric(10, 2))        # used to turn person_count into density
    capacity = Column(Integer)                # safe maximum number of people
    context_tag = Column(String(30))          # default tag for this zone
    created_at = Column(TIMESTAMP, server_default=func.now())

    reports = relationship("Report", back_populates="zone")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    zone_id = Column(Integer, ForeignKey("zones.id", ondelete="SET NULL"))
    media_path = Column(String(255), nullable=False)
    media_type = Column(String(10), nullable=False, default="image")  # image | video
    lat = Column(Numeric(9, 6), nullable=False)
    long = Column(Numeric(9, 6), nullable=False)
    gps_accuracy = Column(Numeric(7, 2))      # metres, from the browser Geolocation API
    address_text = Column(String(255))        # optional exact address typed by the user
    location_name = Column(String(150))       # optional; reverse-geocoded name
    context_tag = Column(String(30))          # open_ground | narrow_lane | stairway | platform
    person_count = Column(Integer)
    density_score = Column(Numeric(6, 2))
    risk_level = Column(String(20))           # Low | Moderate | High | Critical
    confidence = Column(Numeric(4, 2))        # 0.00 - 1.00, AI confidence
    verified = Column(Boolean, nullable=False, default=False, server_default="false")
    status = Column(String(20), default="PENDING")
    submitted_at = Column(TIMESTAMP, server_default=func.now())
    processed_at = Column(TIMESTAMP)

    user = relationship("User", back_populates="reports")
    zone = relationship("Zone", back_populates="reports")
    alerts = relationship("Alert", back_populates="report")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"))
    authority_id = Column(Integer, ForeignKey("authorities.id", ondelete="SET NULL"))
    status = Column(String(20), default="UNACKNOWLEDGED")
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    acknowledged_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())

    report = relationship("Report", back_populates="alerts")
    authority = relationship("Authority", back_populates="alerts")