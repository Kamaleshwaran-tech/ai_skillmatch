"""Pydantic schemas for Role Learning Roadmap response."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.skill_gap import EvaluatedSkillItem, ThresholdMetadata


class RoadmapStep(BaseModel):
    """Single ordered step in a role learning roadmap."""

    step_number: int = Field(..., description="1-indexed deterministic sequence number ordered by demand %")
    skill: str = Field(..., description="Skill name from market demand")
    canonical_name: str = Field(..., description="Canonical skill name")
    status: str = Field(..., description="Gap status: 'missing' or 'needs_review'")
    demand_percentage: float = Field(..., description="Real market demand percentage for this skill")
    matching_listings_count: int = Field(..., description="Number of analyzed listings requiring this skill")
    total_listings_analyzed: int = Field(..., description="Total unique listings analyzed")
    priority: str = Field(..., description="Project-defined priority: High, Medium, or Low")
    ai_explanation_available: bool = Field(
        ...,
        description="True only if the LLM successfully generated the explanation; False if LLM failed/timed out",
    )
    explanation: str = Field(
        ...,
        description="Plain-language explanation from LLM, or 'AI explanation unavailable' if LLM call failed",
    )
    resource_suggestions: List[str] = Field(
        default_factory=list,
        description="General resource types suggested by LLM (official docs, reputable free platform, practice project)",
    )
    practice_project_idea: Optional[str] = Field(
        None,
        description="General practice project idea returned by the LLM, if available",
    )


class RoadmapResponse(BaseModel):
    """Response model for GET /api/roadmap."""

    resume_id: int
    target_role: str
    target_location: Optional[str] = None
    overall_match_percentage: float
    total_listings_analyzed: int
    data_source: str
    is_sample_data: bool
    banner_message: Optional[str] = None
    priority_thresholds: ThresholdMetadata = ThresholdMetadata()
    resource_disclaimer: str = (
        "Resource suggestions are general learning categories and platforms, "
        "not a specific verified course list or live URL directory."
    )
    roadmap_steps: List[RoadmapStep]
    matched_skills: List[EvaluatedSkillItem]
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
