"""SQLAlchemy ORM models for SkillSync AI.

Includes:
- User (users)
- Resume (resumes)
- ExtractedSkill (extracted_skills)
- JobListing (job_listings)
- JobSkill (job_skills)
- SkillGapAnalysis (skill_gap_analyses)
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class User(Base):
    """User account model for authentication and ownership."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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

    # Relationships
    resumes: Mapped[List["Resume"]] = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    gap_analyses: Mapped[List["SkillGapAnalysis"]] = relationship("SkillGapAnalysis", back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    """Uploaded and parsed user resumes."""

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parsed_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
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

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="resumes")
    extracted_skills: Mapped[List["ExtractedSkill"]] = relationship("ExtractedSkill", back_populates="resume", cascade="all, delete-orphan")
    gap_analyses: Mapped[List["SkillGapAnalysis"]] = relationship("SkillGapAnalysis", back_populates="resume", cascade="all, delete-orphan")


class ExtractedSkill(Base):
    """Skills identified from parsed resumes."""

    __tablename__ = "extracted_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    canonical_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    years_experience: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    resume: Mapped["Resume"] = relationship("Resume", back_populates="extracted_skills")


class JobListing(Base):
    """Job postings from market ingestion or user submissions."""

    __tablename__ = "job_listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(50), default="us", nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    salary_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salary_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="adzuna", nullable=False)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    skills: Mapped[List["JobSkill"]] = relationship("JobSkill", back_populates="job_listing", cascade="all, delete-orphan")


class JobSkill(Base):
    """Skills associated with or required by job postings."""

    __tablename__ = "job_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    job_listing_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    canonical_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    importance_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("job_listing_id", "skill_name", name="uq_job_listing_skill"),
    )

    # Relationships
    job_listing: Mapped["JobListing"] = relationship("JobListing", back_populates="skills")


class SkillGapAnalysis(Base):
    """Persisted skill gap analysis record."""

    __tablename__ = "skill_gap_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id: Mapped[int] = mapped_column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_role: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_listings_analyzed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data_source: Mapped[str] = mapped_column(String(100), default="Adzuna Sample Fixtures", nullable=False)
    is_sample_data: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    results_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="gap_analyses")
    resume: Mapped["Resume"] = relationship("Resume", back_populates="gap_analyses")
