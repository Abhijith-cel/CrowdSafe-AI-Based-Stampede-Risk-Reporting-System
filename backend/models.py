# backend/app/models.py
"""
Table definitions. Each class here = one table in PostgreSQL.
Matches the schema.sql we wrote earlier, but as Python classes so
routes can work with objects instead of writing raw SQL everywhere.
"""

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="citizen")  # citizen | authority | admin
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


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    video_path = Column(String(255), nullable=False)
    lat = Column(Numeric(9, 6), nullable=False)
    long = Column(Numeric(9, 6), nullable=False)
    context_tag = Column(String(30))  # open_ground | narrow_lane | stairway | platform
    person_count = Column(Integer)
    density_score = Column(Numeric(6, 2))
    risk_level = Column(String(20))  # Low | Moderate | High | Critical
    status = Column(String(20), default="PENDING")  # PENDING | PROCESSING | REVIEWED
    submitted_at = Column(TIMESTAMP, server_default=func.now())
    processed_at = Column(TIMESTAMP)

    user = relationship("User", back_populates="reports")
    alerts = relationship("Alert", back_populates="report")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"))
    authority_id = Column(Integer, ForeignKey("authorities.id", ondelete="SET NULL"))
    status = Column(String(20), default="UNACKNOWLEDGED")  # UNACKNOWLEDGED | ACKNOWLEDGED | ESCALATED
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    acknowledged_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())

    report = relationship("Report", back_populates="alerts")
    authority = relationship("Authority", back_populates="alerts")
