"""Skill gap analysis orchestration service.

Wires together:
1. Candidate extracted skills and resume evidence (Task 3)
2. Market demand telemetry from live Adzuna or labeled sample fixtures (Task 4)
3. 5-stage hybrid matcher with semantic vectors and evidence validation (Task 5)
4. Project-defined priority thresholds:
     High   >= 70%
     Medium 40% - 69.9%
     Low    < 40%
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import Resume, SkillGapAnalysis
from app.services.market_demand_service import MarketDemandService
from app.services.hybrid_matcher import HybridMatcher
from app.services.skill_normalizer import SkillNormalizer


class SkillGapService:
    """Orchestrates comprehensive skill gap analysis."""

    def __init__(
        self,
        db: Session,
        market_demand_service: Optional[MarketDemandService] = None,
        hybrid_matcher: Optional[HybridMatcher] = None,
    ):
        self.db = db
        self.market_demand_service = market_demand_service or MarketDemandService()
        self.hybrid_matcher = hybrid_matcher or HybridMatcher()
        self.normalizer = SkillNormalizer()

    @staticmethod
    def calculate_priority(demand_percentage: float) -> str:
        """Assign project-defined priority based on market demand percentage.
        
        Note: Project-defined thresholds, not industry standards:
        - High: >= 70%
        - Medium: 40% - 69.9%
        - Low: < 40%
        """
        if demand_percentage >= 70.0:
            return "High"
        elif demand_percentage >= 40.0:
            return "Medium"
        else:
            return "Low"

    def analyze_resume_gap(
        self,
        user_id: int,
        resume_id: int,
        target_role: str,
        target_location: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Run end-to-end skill gap analysis for a user's resume."""
        resume = self.db.get(Resume, resume_id)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID {resume_id} not found.",
            )

        # Ownership check
        if resume.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to analyze this resume.",
            )

        # 1. Candidate extracted skills
        candidate_skills = []
        for s in resume.extracted_skills:
            candidate_skills.append({
                "canonical_name": s.canonical_name or s.skill_name,
                "matched_text": s.skill_name,
                "category": s.category,
                "evidence_snippet": s.skill_name,
            })

        # 2. Fetch market demand for target role
        demand_analysis = self.market_demand_service.analyze_market_demand(
            role=target_role,
            location=target_location or "",
            limit=limit,
        )

        total_listings = demand_analysis.get("total_unique_listings_analyzed", 0)
        data_source = "Adzuna Sample Fixtures" if demand_analysis.get("is_sample_data") else "Adzuna Live API"
        is_sample_data = demand_analysis.get("is_sample_data", True)
        banner_message = demand_analysis.get("banner_message")
        top_skills = demand_analysis.get("top_skills", [])

        # 3. Evaluate each in-demand skill using HybridMatcher
        matched_skills = []
        missing_skills = []
        needs_review_skills = []

        for req in top_skills:
            skill_name = req["skill_name"]
            demand_pct = req["demand_percentage"]
            matching_count = req["matching_listings_count"]
            priority = self.calculate_priority(demand_pct)

            # Evaluate against candidate skills with 5-stage hybrid matcher
            match_res = self.hybrid_matcher.match_requirement(
                required_skill=skill_name,
                candidate_skills=candidate_skills,
                resume_raw_text=resume.raw_text or "",
            )

            evaluated_item = {
                "skill": skill_name,
                "canonical_name": match_res["canonical_name"],
                "status": match_res["status"],
                "method": match_res["method"],
                "similarity_score": match_res.get("similarity_score"),
                "demand_percentage": demand_pct,
                "matching_listings_count": matching_count,
                "total_listings_analyzed": total_listings,
                "priority": priority,
                "matched_candidate_text": match_res.get("matched_candidate_text"),
                "evidence_text": match_res.get("evidence_text"),
                "explanation": match_res["explanation"],
            }

            if match_res["status"] == "matched":
                matched_skills.append(evaluated_item)
            elif match_res["status"] == "needs_review":
                needs_review_skills.append(evaluated_item)
            else:
                missing_skills.append(evaluated_item)

        total_market_skills = len(top_skills)
        match_percentage = (
            round((len(matched_skills) / total_market_skills) * 100, 2)
            if total_market_skills > 0
            else 0.0
        )

        analysis_timestamp = datetime.now(timezone.utc)

        full_results = {
            "user_id": user_id,
            "resume_id": resume_id,
            "target_role": target_role,
            "target_location": target_location,
            "total_listings_analyzed": total_listings,
            "data_source": data_source,
            "is_sample_data": is_sample_data,
            "banner_message": banner_message,
            "analysis_timestamp": analysis_timestamp.isoformat(),
            "priority_thresholds": {
                "high_threshold": ">= 70.0%",
                "medium_threshold": "40.0% - 69.9%",
                "low_threshold": "< 40.0%",
                "note": "Project-defined priority thresholds, not industry standards",
            },
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "needs_review_skills": needs_review_skills,
            "summary": {
                "total_demanded_skills": total_market_skills,
                "matched_count": len(matched_skills),
                "missing_count": len(missing_skills),
                "needs_review_count": len(needs_review_skills),
                "overall_match_percentage": match_percentage,
            },
        }

        # 4. Persist analysis to database
        gap_record = SkillGapAnalysis(
            user_id=user_id,
            resume_id=resume_id,
            target_role=target_role,
            target_location=target_location,
            total_listings_analyzed=total_listings,
            data_source=data_source,
            is_sample_data=is_sample_data,
            results_json=json.dumps(full_results),
            created_at=analysis_timestamp,
        )
        self.db.add(gap_record)
        self.db.commit()
        self.db.refresh(gap_record)

        full_results["analysis_id"] = gap_record.id
        return full_results

    def get_analysis_by_id(self, analysis_id: int, user_id: int) -> Dict[str, Any]:
        """Retrieve persisted skill gap analysis by ID with ownership enforcement."""
        analysis = self.db.get(SkillGapAnalysis, analysis_id)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill gap analysis with ID {analysis_id} not found.",
            )

        if analysis.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this analysis.",
            )

        data = json.loads(analysis.results_json)
        data["analysis_id"] = analysis.id
        return data
