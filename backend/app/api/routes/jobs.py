"""Job listings routes with query and location filters."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.job_provider_adzuna import AdzunaJobProvider
from app.services.job_matcher import JobMatcherService
from app.schemas.jobs import JobSearchResponse, JobRecommendationsResponse

router = APIRouter()
job_provider = AdzunaJobProvider()


@router.get(
    "/search",
    response_model=JobSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search job listings with role and location filters",
)
def search_jobs(
    role: Optional[str] = Query(None, description="Job title, keywords, or role to search"),
    location: Optional[str] = Query(None, description="Geographic city, state, or remote"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
):
    """Retrieve job listings from Adzuna (or labeled sample fixtures if API credentials are not set)."""
    search_query = role or ""
    loc_query = location or ""

    results = job_provider.search_jobs(
        query=search_query,
        location=loc_query,
        page=page,
        results_per_page=limit,
    )

    return results


@router.get(
    "/recommendations",
    response_model=JobRecommendationsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get personalized job recommendations based on resume skills",
)
def get_job_recommendations(
    resume_id: int = Query(..., description="ID of the resume to match against jobs"),
    location: Optional[str] = Query(None, description="Geographic city, state, or remote filter"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of recommendations to return"),
    min_match: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum match percentage threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recommend and rank job listings tailored to the candidate's extracted skills."""
    service = JobMatcherService(db=db)
    return service.recommend_jobs(
        user_id=current_user.id,
        resume_id=resume_id,
        location=location,
        limit=limit,
        min_match=min_match,
    )

