"""Skill gap analysis routes: POST /api/skill-gap/analyze and GET /api/skill-gap/{analysis_id}."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.skill_gap_service import SkillGapService
from app.schemas.skill_gap import SkillGapAnalysisRequest, SkillGapAnalysisResponse

router = APIRouter()


@router.post(
    "/analyze",
    response_model=SkillGapAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze skill gaps between resume and target role market demand",
)
def analyze_skill_gap(
    request: SkillGapAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run comprehensive skill gap analysis for an uploaded resume against live or fixture market demand."""
    service = SkillGapService(db)
    result = service.analyze_resume_gap(
        user_id=current_user.id,
        resume_id=request.resume_id,
        target_role=request.target_role,
        target_location=request.target_location,
        limit=request.limit or 50,
    )
    return result


@router.get(
    "/{analysis_id}",
    response_model=SkillGapAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve previously generated skill gap analysis by ID",
)
def get_skill_gap_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve persisted skill gap analysis by ID with ownership enforcement."""
    service = SkillGapService(db)
    return service.get_analysis_by_id(analysis_id, current_user.id)
