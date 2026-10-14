"""SQLAlchemy Base and common model definitions.

Designed to work transparently with SQLite during local development
and PostgreSQL in production environments.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, Integer


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""
    pass


class TimestampedModel:
    """Mixin for models requiring created_at and updated_at timestamps."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
