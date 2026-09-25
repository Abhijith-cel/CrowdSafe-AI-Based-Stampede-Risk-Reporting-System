# backend/test_connection.py
"""
Run this ONCE PostgreSQL is installed and running, to:
1. confirm your .env credentials are correct
2. create all four tables in the crowd_monitor database

Run from inside backend/ with your venv active:
    python test_connection.py
"""

from app.database import engine, Base
from app import models  # noqa: F401  (import so Base knows about the tables)

try:
    # This actually opens a connection to PostgreSQL
    connection = engine.connect()
    print("Connected to PostgreSQL successfully.")
    connection.close()

    # This creates the tables (users, authorities, reports, alerts)
    # if they don't already exist
    Base.metadata.create_all(bind=engine)
    print("Tables created (or already existed). Check pgAdmin to confirm.")

except Exception as e:
    print("Connection failed. Common causes:")
    print("- PostgreSQL service isn't running yet (check Services app)")
    print("- Wrong password in .env")
    print("- Database 'crowd_monitor' doesn't exist yet (create it in pgAdmin first)")
    print(f"\nActual error: {e}")
