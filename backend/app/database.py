"""
SQLAlchemy database engine, session factory, and table initialisation.
Uses SQLite for zero-config local storage.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import get_settings

settings = get_settings()

# Ensure the data directory exists
os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)

DATABASE_URL = f"sqlite:///{settings.DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist."""
    from . import models  # noqa: F401 — import so Base sees the models
    Base.metadata.create_all(bind=engine)
