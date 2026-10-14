"""Adzuna API implementation of JobProvider with safe fallback to labeled sample fixture data."""

import os
import json
import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.services.job_provider import JobProvider


class AdzunaJobProvider(JobProvider):
    """Job provider querying the official Adzuna REST API.
    
    Credentials are read from settings (environment variables) and never hardcoded.
    If credentials are missing or the API call fails/times out, cleanly serves a
    clearly-labeled fixture dataset with banner metadata.
    """

    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(self, sample_fixture_path: Optional[str] = None):
        if sample_fixture_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sample_fixture_path = os.path.join(base_dir, "taxonomy", "sample_jobs.json")
        self.sample_fixture_path = sample_fixture_path
        self._sample_data: Optional[List[Dict[str, Any]]] = None

    def _load_sample_fixtures(self) -> List[Dict[str, Any]]:
        """Load sample job fixtures from disk."""
        if self._sample_data is None:
            if os.path.exists(self.sample_fixture_path):
                with open(self.sample_fixture_path, "r", encoding="utf-8") as f:
                    self._sample_data = json.load(f)
            else:
                self._sample_data = []
        return self._sample_data

    def _filter_sample_fixtures(
        self,
        query: str = "",
        location: str = "",
        page: int = 1,
        results_per_page: int = 20,
        category: Optional[str] = None,
        what_or: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Filter local sample fixtures by role/query, what_or, and location."""
        all_jobs = self._load_sample_fixtures()
        q_lower = query.lower().strip()
        what_or_lower = what_or.lower().strip() if what_or else ""
        loc_lower = location.lower().strip()

        filtered = []
        for job in all_jobs:
            matches_query = True
            matches_loc = True

            text_to_search = f"{job.get('title', '')} {job.get('description', '')} {job.get('company', '')}".lower()

            if q_lower:
                tokens = [t for t in q_lower.split() if len(t) > 1]
                matches_query = (q_lower in text_to_search) or (bool(tokens) and any(t in text_to_search for t in tokens))
            elif what_or_lower:
                or_tokens = [t for t in what_or_lower.split() if len(t) > 1]
                matches_query = bool(or_tokens) and any(t in text_to_search for t in or_tokens)

            if loc_lower:
                job_loc = job.get("location", "").lower()
                matches_loc = loc_lower in job_loc or ("remote" in loc_lower and "remote" in job_loc)

            if matches_query and matches_loc:
                filtered.append(job)

        # If filtered is empty but what_or was given, fall back to returning tech fixtures
        if not filtered and (q_lower or what_or_lower):
            filtered = all_jobs

        start = (page - 1) * results_per_page
        end = start + results_per_page
        paged_results = filtered[start:end]

        return {
            "results": paged_results,
            "total_count": len(filtered),
            "is_sample_data": True,
            "banner_message": "SAMPLE DATA — not live (Adzuna credentials not configured or live API offline)",
            "data_source": "Adzuna Sample Fixtures",
        }

    def search_jobs(
        self,
        query: str = "",
        location: str = "",
        page: int = 1,
        results_per_page: int = 20,
        country: Optional[str] = None,
        category: Optional[str] = None,
        what_or: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Query official Adzuna API, falling back to labeled sample fixtures if credentials are missing or API fails."""
        app_id = settings.ADZUNA_APP_ID.strip() if settings.ADZUNA_APP_ID else ""
        app_key = settings.ADZUNA_APP_KEY.strip() if settings.ADZUNA_APP_KEY else ""

        # If credentials are not configured, serve sample fixtures immediately
        if not app_id or not app_key or app_id == "your_adzuna_app_id_here":
            return self._filter_sample_fixtures(query, location, page, results_per_page, category, what_or)

        # Call live Adzuna API
        target_country = country or settings.ADZUNA_COUNTRY or "us"
        url = f"{self.BASE_URL}/{target_country}/search/{page}"
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": min(results_per_page, 50),
            "content-type": "application/json",
        }
        if query:
            params["what"] = query
        if what_or:
            params["what_or"] = what_or
        if location:
            params["where"] = location
        if category:
            params["category"] = category

        try:
            with httpx.Client(timeout=8.0) as client:
                response = client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    raw_results = data.get("results", [])
                    standardized = []
                    for item in raw_results:
                        company_info = item.get("company", {})
                        location_info = item.get("location", {})
                        standardized.append({
                            "id": str(item.get("id")),
                            "title": item.get("title", ""),
                            "company": company_info.get("display_name", "Unknown Company"),
                            "location": location_info.get("display_name", ""),
                            "country": target_country,
                            "description": item.get("description", ""),
                            "salary_min": item.get("salary_min"),
                            "salary_max": item.get("salary_max"),
                            "url": item.get("redirect_url", ""),
                            "posted_at": item.get("created"),
                            "source": "adzuna_live",
                        })

                    return {
                        "results": standardized,
                        "total_count": data.get("count", len(standardized)),
                        "is_sample_data": False,
                        "banner_message": None,
                        "data_source": "Adzuna Live API",
                    }
                else:
                    # Non-200 from live API, fall back with warning
                    fallback = self._filter_sample_fixtures(query, location, page, results_per_page, category, what_or)
                    fallback["banner_message"] = (
                        f"SAMPLE DATA — not live (Adzuna API returned status {response.status_code})"
                    )
                    return fallback

        except Exception as e:
            fallback = self._filter_sample_fixtures(query, location, page, results_per_page, category, what_or)
            fallback["banner_message"] = (
                f"SAMPLE DATA — not live (Adzuna request failed: {str(e)})"
            )
            return fallback
