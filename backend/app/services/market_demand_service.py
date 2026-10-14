"""Market demand analysis service calculating skill frequency and percentage across job listings.

Formula:
  demand_% = (unique listings containing skill S / total unique relevant listings analyzed) * 100

Always returns denominator alongside each calculated percentage.
Handles empty or insufficient-data states gracefully.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from app.services.skill_extractor import SkillExtractor
from app.services.job_provider_adzuna import AdzunaJobProvider
from app.services.job_ingestion import JobIngestionService


class MarketDemandService:
    """Computes technical skill demand percentages across relevant job postings."""

    def __init__(
        self,
        job_provider: Optional[AdzunaJobProvider] = None,
        skill_extractor: Optional[SkillExtractor] = None,
    ):
        self.job_provider = job_provider or AdzunaJobProvider()
        self.skill_extractor = skill_extractor or SkillExtractor()

    def analyze_market_demand(
        self,
        role: str = "",
        location: str = "",
        limit: int = 50,
        provided_jobs: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Analyze technical skill demand across relevant job listings.
        
        Args:
            role: Target job title or skill keyword filter.
            location: Target geographic or remote filter.
            limit: Maximum listings to analyze.
            provided_jobs: Optional in-memory job list for deterministic fixture testing.
            
        Returns:
            Dict containing:
            - total_unique_listings_analyzed: The exact denominator
            - top_skills: List of skill records with count, demand_percentage, category
            - is_sample_data: True if fixtures were used
            - banner_message: Banner string if sample data was served
            - status: "sufficient_data" or "insufficient_data"
        """
        # 1. Fetch listings from provider if not explicitly provided
        if provided_jobs is not None:
            raw_jobs = provided_jobs
            is_sample_data = True
            banner_message = "FIXTURE TEST DATA"
        else:
            search_res = self.job_provider.search_jobs(
                query=role,
                location=location,
                results_per_page=limit,
            )
            raw_jobs = search_res.get("results", [])
            is_sample_data = search_res.get("is_sample_data", False)
            banner_message = search_res.get("banner_message")

        # 2. Deduplicate listings (primary ID + secondary normalized fingerprint)
        unique_jobs, _ = JobIngestionService.deduplicate_job_stream(raw_jobs)
        total_unique_listings = len(unique_jobs)

        # 3. Handle empty / insufficient-data state
        if total_unique_listings == 0:
            return {
                "total_unique_listings_analyzed": 0,
                "role_filter": role,
                "location_filter": location,
                "status": "insufficient_data",
                "message": (
                    f"No relevant job listings found for role '{role}' and location '{location}'. "
                    "Insufficient data to compute market demand."
                ),
                "is_sample_data": is_sample_data,
                "banner_message": banner_message,
                "top_skills": [],
            }

        # 4. Count unique listings containing each skill
        # Mapping: canonical_name -> set of job index / IDs
        skill_to_job_ids = defaultdict(set)
        skill_categories = {}

        for idx, job in enumerate(unique_jobs):
            job_key = str(job.get("id") or idx)
            combined_text = f"{job.get('title', '')}\n{job.get('description', '')}"

            extracted = self.skill_extractor.extract_skills(combined_text)
            for sk in extracted:
                c_name = sk["canonical_name"]
                skill_to_job_ids[c_name].add(job_key)
                skill_categories[c_name] = sk.get("category", "other")

        # 5. Compute demand percentage with denominator
        skills_ranked = []
        for c_name, matching_job_set in skill_to_job_ids.items():
            matching_count = len(matching_job_set)
            # Exact formula: matching / total_unique * 100
            demand_pct = round((matching_count / total_unique_listings) * 100, 2)

            skills_ranked.append({
                "skill_name": c_name,
                "category": skill_categories.get(c_name, "other"),
                "matching_listings_count": matching_count,
                "total_listings_analyzed": total_unique_listings,
                "demand_percentage": demand_pct,
            })

        # Sort descending by demand percentage, then alphabetically
        skills_ranked.sort(key=lambda x: (-x["demand_percentage"], x["skill_name"]))

        return {
            "total_unique_listings_analyzed": total_unique_listings,
            "role_filter": role,
            "location_filter": location,
            "status": "sufficient_data",
            "is_sample_data": is_sample_data,
            "banner_message": banner_message,
            "top_skills": skills_ranked,
        }
