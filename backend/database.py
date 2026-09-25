# backend/app/database.py
"""
Sets up the SQLAlchemy engine and session — every other file that
needs to talk to PostgreSQL imports from here.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load variables from backend/.env into the environment
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "crowd_monitor")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# The engine is the actual connection pool to PostgreSQL
engine = create_engine(DATABASE_URL, echo=True)
# echo=True prints every SQL statement to the terminal — useful while
# learning/debugging. Set to False later once things are stable.

# SessionLocal is what routes will use to talk to the DB per-request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is what models.py will inherit from to define tables
Base = declarative_base()


def get_db():
    """
    Call this from route files to get a DB session, and it closes
    itself automatically afterward. Example usage in a route:

        db = next(get_db())
        db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
