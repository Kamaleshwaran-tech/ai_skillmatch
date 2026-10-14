"""Market demand routes calculating skill demand percentages across analyzed job listings."""

from typing import Optional
from fastapi import APIRouter, Query, status
from app.services.market_demand_service import MarketDemandService
from app.schemas.jobs import MarketDemandResponse

router = APIRouter()
market_demand_service = MarketDemandService()


@router.get(
    "",
    response_model=MarketDemandResponse,
    status_code=status.HTTP_200_OK,
    summary="Get technical skill demand percentages with denominator",
)
def get_market_demand(
    role: Optional[str] = Query(None, description="Filter demand by job title or role"),
    location: Optional[str] = Query(None, description="Filter demand by geographic location"),
    limit: int = Query(50, ge=1, le=200, description="Maximum listings to analyze"),
):
    """Calculate demand percentages for skills extracted from job listings.
    
    Formula:
      demand_% = (unique listings containing skill S / total unique relevant listings analyzed) * 100
      
    Includes the denominator (total_listings_analyzed) alongside each percentage.
    """
    role_filter = role or ""
    loc_filter = location or ""

    return market_demand_service.analyze_market_demand(
        role=role_filter,
        location=loc_filter,
        limit=limit,
    )
