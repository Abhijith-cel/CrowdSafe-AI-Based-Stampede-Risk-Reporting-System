# backend/seed_test_data.py  -- run once: python seed_test_data.py
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import Alert, Authority, Report, User

VIDEO = "https://www.w3schools.com/html/mov_bbb.mp4"
def img(n): return f"https://picsum.photos/seed/crowdsafe{n}/640/400"

AUTHORITIES = [  # test data, approximate Bengaluru coordinates
    ("Central Division Control Room", 12.9767, 77.5713),
    ("East Division Control Room",    12.9788, 77.5996),
    ("South Division Control Room",   12.9507, 77.5848),
]

# (lat, long, risk, media_type, media_path, minutes_ago, context, person_count, location_name, authority_index)
REPORTS = [
    (12.9767, 77.5713, "Critical", "video", VIDEO,   4, "platform",    312, "Nelamangala Bus Platform",    0),
    (12.9788, 77.5996, "High",     "image", img(2), 11, "stairway",    168, "MG Road Metro Stairway",      1),
    (12.9788, 77.5996, "Moderate", "image", img(3), 26, "open_ground",  84, "Cubbon Park Main Gate",       1),
    (12.9634, 77.5755, "High",     "video", VIDEO,  42, "narrow_lane", 142, "Chickpet Narrow Lane",       0),
    (12.9507, 77.5848, "Low",      "image", img(5), 75, "open_ground",  37, "Lalbagh West Gate",          2),
    (12.9698, 77.5063, "Moderate", "image", img(6),130, "narrow_lane",  76, "Rajajinagar Temple Road",    0),
    (12.9791, 77.5913, "Critical", "image", img(7),  8, "stairway",    289, "Kanteerava Stadium Exit",    1),
]

db = SessionLocal()
try:
    if db.query(Authority).count():
        print("Authorities already exist, skipping seed.")
    else:
        user = User(name="Test Citizen", email="citizen@test.local",
                    password_hash="not-a-real-hash", role="citizen")
        auths = [Authority(name=n, station_lat=la, station_long=lo, jurisdiction_radius_km=5.0,
                           contact_email=f"auth{i+1}@test.local")
                 for i, (n, la, lo) in enumerate(AUTHORITIES)]
        db.add_all([user, *auths])
        db.flush()

        for la, lo, risk, mtype, path, mins, ctx, count, name, ai in REPORTS:
            r = Report(user_id=user.id, media_path=path, media_type=mtype, lat=la, long=lo,
                       context_tag=ctx, person_count=count, risk_level=risk, location_name=name,
                       status="PROCESSED", submitted_at=datetime.now() - timedelta(minutes=mins))
            db.add(r)
            db.flush()
            db.add(Alert(report_id=r.id, authority_id=auths[ai].id, status="UNACKNOWLEDGED"))

        # mirror the mock: report 4 was already acknowledged
        db.flush()
        db.query(Alert).filter(Alert.report_id == 4).update(
            {"status": "ACKNOWLEDGED", "acknowledged_at": datetime.utcnow()})
        db.commit()
        print("Seeded 1 user, 3 authorities, 7 reports with alerts.")
finally:
    db.close()
