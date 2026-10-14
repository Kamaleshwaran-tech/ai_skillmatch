"""Role Learning Roadmap route: GET /api/roadmap."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.roadmap import RoadmapResponse
from app.services.roadmap_service import RoadmapService

router = APIRouter()


@router.get(
    "",
    response_model=RoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate an ordered learning roadmap for a target role based on market demand",
)
def get_learning_roadmap(
    resume_id: int = Query(..., description="ID of the user's resume"),
    target_role: str = Query(..., min_length=1, description="Target job role or stack"),
    target_location: Optional[str] = Query(None, description="Optional geographic location or remote"),
    limit: int = Query(50, ge=5, le=100, description="Max job listings to analyze for market demand"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a deterministic, market-demand-ordered learning roadmap for a target role."""
    service = RoadmapService(db=db)
    return service.generate_roadmap(
        user_id=current_user.id,
        resume_id=resume_id,
        target_role=target_role,
        target_location=target_location,
        limit=limit,
    )
