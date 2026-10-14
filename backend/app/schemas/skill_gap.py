"""Pydantic schemas for Skill Gap Analysis request and response."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SkillGapAnalysisRequest(BaseModel):
    resume_id: int = Field(..., description="ID of the uploaded resume to analyze")
    target_role: Optional[str] = Field("", description="Target job title or role to match against")
    target_location: Optional[str] = Field(None, description="Target geographic city, state, or remote")
    limit: Optional[int] = Field(50, ge=5, le=100, description="Max job postings to analyze")


class EvaluatedSkillItem(BaseModel):
    skill: str
    canonical_name: str
    status: str  # "matched", "missing", "needs_review"
    method: str  # "exact", "alias", "semantic", "none"
    similarity_score: Optional[float] = None
    demand_percentage: float
    matching_listings_count: int
    total_listings_analyzed: int
    priority: str  # "High (>=70%)", "Medium (40-69%)", "Low (<40%)"
    matched_candidate_text: Optional[str] = None
    evidence_text: Optional[str] = None
    explanation: str


class ThresholdMetadata(BaseModel):
    high_threshold: str = ">= 70.0%"
    medium_threshold: str = "40.0% - 69.9%"
    low_threshold: str = "< 40.0%"
    note: str = "Project-defined priority thresholds, not industry standards"


class SkillGapAnalysisResponse(BaseModel):
    analysis_id: int
    user_id: int
    resume_id: int
    target_role: str
    target_location: Optional[str] = None
    total_listings_analyzed: int
    data_source: str
    is_sample_data: bool
    banner_message: Optional[str] = None
    analysis_timestamp: datetime
    priority_thresholds: ThresholdMetadata = ThresholdMetadata()
    matched_skills: List[EvaluatedSkillItem]
    missing_skills: List[EvaluatedSkillItem]
    needs_review_skills: List[EvaluatedSkillItem]
    summary: dict

    model_config = ConfigDict(from_attributes=True)
