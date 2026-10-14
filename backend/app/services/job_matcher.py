"""Job recommendation service matching candidate resume skills to job listings.

Independent recommendation capability utilizing:
1. Candidate extracted skills from Task 3.
2. Adzuna JobProvider from Task 4 (live API or labeled fixture fallback).
3. SkillExtractor to detect required skills in job descriptions.
4. HybridMatcher from Task 5 to evaluate exact, alias, and semantic matches.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import Resume
from app.services.job_provider import JobProvider
from app.services.job_provider_adzuna import AdzunaJobProvider
from app.services.hybrid_matcher import HybridMatcher
from app.services.skill_extractor import SkillExtractor


class JobMatcherService:
    """Service that scores and ranks job listings according to candidate resume skills."""

    def __init__(
        self,
        db: Session,
        job_provider: Optional[JobProvider] = None,
        hybrid_matcher: Optional[HybridMatcher] = None,
        skill_extractor: Optional[SkillExtractor] = None,
    ):
        self.db = db
        self.job_provider = job_provider or AdzunaJobProvider()
        self.hybrid_matcher = hybrid_matcher or HybridMatcher()
        self.skill_extractor = skill_extractor or SkillExtractor()

    @staticmethod
    def format_salary_range(
        salary_min: Optional[float],
        salary_max: Optional[float],
    ) -> Optional[str]:
        """Format minimum and maximum salary figures into a clean readable string."""
        if salary_min is not None and salary_max is not None:
            return f"${salary_min:,.0f} - ${salary_max:,.0f}"
        elif salary_min is not None:
            return f"${salary_min:,.0f}+"
        elif salary_max is not None:
            return f"Up to ${salary_max:,.0f}"
        return None

    def recommend_jobs(
        self,
        user_id: int,
        resume_id: int,
        location: Optional[str] = None,
        limit: int = 20,
        min_match: Optional[float] = None,
        provided_listings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate ranked job recommendations for a specific resume.
        
        Args:
            user_id: ID of requesting user for strict ownership verification.
            resume_id: ID of the candidate resume.
            location: Optional geographical location filter.
            limit: Maximum count of recommendations to return (default 20).
            min_match: Minimum match percentage threshold (0-100).
            provided_listings: Optional mock listing dataset for deterministic unit testing.
            
        Returns:
            Dictionary matching JobRecommendationsResponse schema.
        """
        resume = self.db.get(Resume, resume_id)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID {resume_id} not found.",
            )

        # Strict ownership verification
        if resume.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access recommendations for this resume.",
            )

        # 1. Collect candidate's canonical skills and matched text
        candidate_skills: List[Dict[str, Any]] = []
        canonical_skill_names: List[str] = []

        for s in resume.extracted_skills:
            c_name = s.canonical_name or s.skill_name
            candidate_skills.append({
                "canonical_name": c_name,
                "matched_text": s.skill_name,
                "category": s.category,
                "evidence_snippet": s.skill_name,
            })
            if c_name not in canonical_skill_names:
                canonical_skill_names.append(c_name)

        # Build search query from the resume's top skills
        top_skills = canonical_skill_names[:5]
        target_category = "it-jobs" if canonical_skill_names else None

        # 2. Query Adzuna job listings or use provided fixtures
        if provided_listings is not None:
            raw_listings = provided_listings
            is_sample_data = True
            banner_message = "SAMPLE DATA — not live (Test Fixtures)"
            data_source = "Test Fixtures"
        else:
            # Strategy A: Use what_or with top skills + IT category filter
            search_response = self.job_provider.search_jobs(
                query="",
                what_or=" ".join(top_skills),
                category=target_category,
                location=location or "",
                page=1,
                results_per_page=max(limit * 2, 50),
            )
            raw_listings = search_response.get("results", [])
            is_sample_data = search_response.get("is_sample_data", False)
            banner_message = search_response.get("banner_message")
            data_source = search_response.get("data_source", "Adzuna")

            # Strategy B: If what_or returned 0 results, fall back to searching primary top skill
            if not raw_listings and top_skills:
                primary_resp = self.job_provider.search_jobs(
                    query=top_skills[0],
                    category=target_category,
                    location=location or "",
                    page=1,
                    results_per_page=max(limit * 2, 50),
                )
                raw_listings = primary_resp.get("results", [])
                is_sample_data = primary_resp.get("is_sample_data", is_sample_data)
                banner_message = primary_resp.get("banner_message", banner_message)
                data_source = primary_resp.get("data_source", data_source)

            # Strategy C: Broad IT fallback (guaranteed strictly IT category, never unrelated non-tech jobs)
            if not raw_listings:
                fallback_resp = self.job_provider.search_jobs(
                    query="",
                    category=target_category,
                    location=location or "",
                    page=1,
                    results_per_page=max(limit * 2, 50),
                )
                raw_listings = fallback_resp.get("results", [])
                is_sample_data = fallback_resp.get("is_sample_data", is_sample_data)
                banner_message = fallback_resp.get("banner_message", banner_message)
                data_source = fallback_resp.get("data_source", data_source)

        # 3. Analyze each listing and compute match scores
        scored_listings: List[Dict[str, Any]] = []

        for job in raw_listings:
            job_title = job.get("title", "")
            job_desc = job.get("description", "")
            # Combine title + description so critical skills present in the role title are captured
            full_job_text = f"{job_title}. {job_desc}" if job_title else job_desc
            extracted_job_skills = self.skill_extractor.extract_skills(full_job_text)

            # Get unique canonical required skills in this job listing
            required_canonical = list(dict.fromkeys([
                s["canonical_name"] for s in extracted_job_skills if s.get("canonical_name")
            ]))

            total_required = len(required_canonical)
            matched_skills: List[str] = []
            missing_skills: List[str] = []

            if total_required == 0:
                # Insufficient requirement data in the job snippet to compute a fair score
                match_percentage = None
                is_scorable = False
            else:
                is_scorable = True
                for req in required_canonical:
                    match_res = self.hybrid_matcher.match_requirement(
                        required_skill=req,
                        candidate_skills=candidate_skills,
                        resume_raw_text=resume.raw_text or "",
                    )
                    if match_res["status"] == "matched":
                        matched_skills.append(req)
                    else:
                        missing_skills.append(req)

                match_percentage = round((len(matched_skills) / total_required) * 100.0, 1)

            # Optional minimum match threshold filter
            if min_match is not None:
                if match_percentage is None or match_percentage < min_match:
                    continue

            raw_desc = job_desc.strip()
            desc_snippet = raw_desc[:250] + ("..." if len(raw_desc) > 250 else "")

            scored_listings.append({
                "job_id": str(job.get("id")),
                "title": job.get("title", ""),
                "company": job.get("company", "Unknown"),
                "location": job.get("location"),
                "salary_range": self.format_salary_range(
                    job.get("salary_min"),
                    job.get("salary_max"),
                ),
                "posted_date": job.get("posted_at") or job.get("created"),
                "match_percentage": match_percentage,
                "is_scorable": is_scorable,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills[:10],
                "description_snippet": desc_snippet,
                "apply_url": job.get("url") or job.get("redirect_url"),
            })

        # 4. Rank listings: scorable listings by match score descending, unscored listings at the bottom
        scored_listings.sort(
            key=lambda x: (
                1 if x["match_percentage"] is not None else 0,
                x["match_percentage"] if x["match_percentage"] is not None else -1.0,
            ),
            reverse=True,
        )

        recommendations = scored_listings[:limit]

        return {
            "resume_id": resume_id,
            "total_recommended": len(recommendations),
            "top_resume_skills": top_skills[:3],
            "is_sample_data": is_sample_data,
            "banner_message": banner_message,
            "data_source": data_source,
            "recommendations": recommendations,
        }
