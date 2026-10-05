"""Seed sample data. Run from the backend/ folder:  python seed_data.py

Coordinates and names are samples - change them to areas you want to demo.
"""
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from app.database import SessionLocal
from app.models import User, Authority, Zone, Report, Alert


def get_or_create_user(db, name, email, role, password):
    user = db.query(User).filter_by(email=email).first()
    if not user:
        user = User(
            name=name,
            email=email,
            role=role,
            password_hash=generate_password_hash(password),
        )
        db.add(user)
        db.flush()
    return user


def main():
    db = SessionLocal()
    try:
        citizen = get_or_create_user(db, "Test Citizen", "citizen@example.com", "citizen", "citizen123")
        officer = get_or_create_user(db, "Test Officer", "officer@example.com", "authority", "officer123")

        authority = db.query(Authority).first()
        if not authority:
            authority = Authority(
                name="Central Control Room",
                station_lat=28.6139,
                station_long=77.2090,
                jurisdiction_radius_km=10,
                contact_email="control@example.com",
            )
            db.add(authority)
            db.flush()

        if db.query(Zone).count() == 0:
            db.add_all([
                Zone(name="Temple main gate", center_lat=28.6129, center_long=77.2295,
                     radius_m=120, area_sq_m=400, capacity=800, context_tag="narrow_lane"),
                Zone(name="Railway platform 1", center_lat=28.6428, center_long=77.2194,
                     radius_m=100, area_sq_m=600, capacity=1500, context_tag="platform"),
                Zone(name="Market ground", center_lat=28.6562, center_long=77.2410,
                     radius_m=200, area_sq_m=2500, capacity=6000, context_tag="open_ground"),
            ])
            db.flush()

        if db.query(Report).count() == 0:
            zones = db.query(Zone).order_by(Zone.id).all()
            now = datetime.utcnow()
            # (zone index, people, density, risk, tag, minutes ago, status)
            samples = [
                (0, 1650, 4.1, "Critical", "narrow_lane", 5, "PENDING"),
                (1, 950, 1.6, "Moderate", "platform", 20, "PENDING"),
                (2, 3200, 1.3, "Low", "open_ground", 45, "PENDING"),
                (0, 1100, 2.8, "High", "narrow_lane", 70, "PENDING"),
                (1, 300, 0.5, "Low", "platform", 120, "RESOLVED"),
            ]
            for zi, people, density, risk, tag, mins, status in samples:
                z = zones[zi]
                report = Report(
                    user_id=citizen.id,
                    zone_id=z.id,
                    media_path=f"uploads/sample_{zi}_{mins}.jpg",
                    media_type="image",
                    lat=z.center_lat,
                    long=z.center_long,
                    gps_accuracy=12.5,
                    address_text=f"Near {z.name}",
                    location_name=z.name,
                    context_tag=tag,
                    person_count=people,
                    density_score=density,
                    risk_level=risk,
                    confidence=0.80,
                    verified=False,
                    status=status,
                    submitted_at=now - timedelta(minutes=mins),
                    processed_at=now - timedelta(minutes=mins - 1),
                )
                db.add(report)
                db.flush()
                if risk in ("High", "Critical"):
                    db.add(Alert(report_id=report.id, authority_id=authority.id))

        db.commit()
        print("Seed complete.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()