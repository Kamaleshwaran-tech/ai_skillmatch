"""API routes package."""

from fastapi import APIRouter
from app.api.routes import auth, resumes, jobs, market_demand, skill_gap, roadmap

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(market_demand.router, prefix="/market-demand", tags=["Market Demand"])
api_router.include_router(skill_gap.router, prefix="/skill-gap", tags=["Skill Gap"])
api_router.include_router(roadmap.router, prefix="/roadmap", tags=["Learning Roadmap"])
