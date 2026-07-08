import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from urllib.parse import urlparse

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("\n" + "!" * 80)
    print("WARNING: DATABASE_URL environment variable is NOT set!")
    print("Falling back to SQLite local database (aicrm.db).")
    print("WARNING: All data will be WIPED on Render restarts due to ephemeral disk!")
    print("!" * 80 + "\n")
    DATABASE_URL = "sqlite:///./aicrm.db"

# Securely parse scheme and host for logs
try:
    parsed = urlparse(DATABASE_URL)
    scheme = parsed.scheme
    host = parsed.hostname or "local"
    print(f"Database connection parsed: {scheme}://{host}")
except Exception:
    print("Database connection parsed: unknown")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
