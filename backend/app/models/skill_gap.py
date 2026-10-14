"""SQLAlchemy models for Skill Gap Analysis persistence."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class SkillGapAnalysis(Base):
    """Persisted skill gap analysis records."""

    __tablename__ = "skill_gap_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id: Mapped[int] = mapped_column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_role: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_listings_analyzed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data_source: Mapped[str] = mapped_column(String(100), default="Adzuna Sample Fixtures", nullable=False)
    is_sample_data: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    results_json: Mapped[str] = mapped_column(Text, nullable=False)  # Full JSON payload
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    resume: Mapped["Resume"] = relationship("Resume")
