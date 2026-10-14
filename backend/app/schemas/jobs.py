"""Schemas for Job search and Market demand responses."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class JobListingOut(BaseModel):
    id: str
    title: str
    company: str
    location: Optional[str] = None
    country: Optional[str] = "us"
    description: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    url: Optional[str] = None
    posted_at: Optional[str] = None
    source: str = "adzuna"

    model_config = ConfigDict(from_attributes=True)


class JobSearchResponse(BaseModel):
    results: List[JobListingOut]
    total_count: int
    is_sample_data: bool
    banner_message: Optional[str] = None
    data_source: str


class SkillDemandItem(BaseModel):
    skill_name: str
    category: str
    matching_listings_count: int
    total_listings_analyzed: int
    demand_percentage: float


class MarketDemandResponse(BaseModel):
    total_unique_listings_analyzed: int
    role_filter: str
    location_filter: str
    status: str
    is_sample_data: bool
    banner_message: Optional[str] = None
    message: Optional[str] = None
    top_skills: List[SkillDemandItem]


class JobRecommendationItem(BaseModel):
    job_id: str
    title: str
    company: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    posted_date: Optional[str] = None
    match_percentage: Optional[float] = None
    is_scorable: bool = True
    matched_skills: List[str]
    missing_skills: List[str]
    description_snippet: str
    apply_url: Optional[str] = None


class JobRecommendationsResponse(BaseModel):
    resume_id: int
    total_recommended: int
    top_resume_skills: List[str]
    is_sample_data: bool
    banner_message: Optional[str] = None
    data_source: str
    recommendations: List[JobRecommendationItem]

