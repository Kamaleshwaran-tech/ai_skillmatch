"""Database engine and session management.

Supports both SQLite (for local development) and PostgreSQL (for production).
The connection parameters automatically adjust according to the provided DATABASE_URL.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Database engine configuration with dialect awareness
connect_args = {}
engine_kwargs = {"pool_pre_ping": True}

if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite requires check_same_thread: False for multithreaded FastAPI requests
    connect_args["check_same_thread"] = False
else:
    # PostgreSQL / MySQL connection pool settings
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
    })

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
