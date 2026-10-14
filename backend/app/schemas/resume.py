"""Schemas for Resume upload, retrieval, history, and skill extraction."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class ExtractedSkillPosition(BaseModel):
    start_char: int
    end_char: int
    section: str = "General"


class ExtractedSkillOut(BaseModel):
    id: Optional[int] = None
    canonical_name: str
    matched_text: str
    category: str
    extraction_method: str
    evidence_snippet: str
    confidence: float
    position: Optional[ExtractedSkillPosition] = None
    years_experience: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ResumeUploadResponse(BaseModel):
    id: int
    filename: str
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    is_active: bool = True
    replaced_previous: bool = False
    extracted_skills_count: int
    skills: List[ExtractedSkillOut]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeHistoryItem(BaseModel):
    id: int
    filename: str
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    is_active: bool
    extracted_skills_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeListResponse(BaseModel):
    total_count: int
    resumes: List[ResumeHistoryItem]


class ActiveResumeResponse(BaseModel):
    has_active_resume: bool
    message: str
    resume: Optional[ResumeUploadResponse] = None
    latest_analysis: Optional[Dict[str, Any]] = None


class ResumeDetailOut(BaseModel):
    id: int
    user_id: int
    filename: str
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    is_active: bool = True
    raw_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeSkillsResponse(BaseModel):
    resume_id: int
    filename: str
    is_active: bool = True
    total_skills: int
    skills: List[ExtractedSkillOut]
