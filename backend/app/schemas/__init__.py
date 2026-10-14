"""Schemas package exports."""

from app.schemas.auth import UserBase, UserCreate, UserLogin, UserOut, Token, TokenPayload
from app.schemas.resume import (
    ExtractedSkillOut,
    ResumeUploadResponse,
    ResumeDetailOut,
    ResumeSkillsResponse,
)
from app.schemas.jobs import (
    JobListingOut,
    JobSearchResponse,
    SkillDemandItem,
    MarketDemandResponse,
)
from app.schemas.skill_gap import (
    SkillGapAnalysisRequest,
    SkillGapAnalysisResponse,
    EvaluatedSkillItem,
    ThresholdMetadata,
)

__all__ = [
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserOut",
    "Token",
    "TokenPayload",
    "ExtractedSkillOut",
    "ResumeUploadResponse",
    "ResumeDetailOut",
    "ResumeSkillsResponse",
    "JobListingOut",
    "JobSearchResponse",
    "SkillDemandItem",
    "MarketDemandResponse",
    "SkillGapAnalysisRequest",
    "SkillGapAnalysisResponse",
    "EvaluatedSkillItem",
    "ThresholdMetadata",
]
