"""Unit and integration tests for Job Ingestion deduplication, Adzuna provider fallback,
and Market Demand percentage calculation.

Tests cover:
- Deduplication logic: by Adzuna listing ID, and by normalized title/company/location composite key.
- Demand calculation formula against a known fixture set:
    demand_% = unique listings containing skill S / total unique relevant listings analyzed * 100
- Denominator reporting alongside each percentage.
- Empty / insufficient-data state when zero matching listings are found.
- Endpoint validation: GET /api/jobs/search and GET /api/market-demand.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.job_ingestion import JobIngestionService
from app.services.market_demand_service import MarketDemandService
from app.services.job_provider_adzuna import AdzunaJobProvider


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. DEDUPLICATION LOGIC TESTS
# ---------------------------------------------------------------------------

def test_deduplication_by_external_id():
    """Verify listings with identical external IDs are deduplicated."""
    jobs = [
        {"id": "adzuna-101", "title": "Python Dev", "company": "Tech Corp", "location": "Remote"},
        {"id": "adzuna-101", "title": "Python Dev - Reposted", "company": "Tech Corp", "location": "Remote"},
        {"id": "adzuna-102", "title": "Frontend Dev", "company": "Tech Corp", "location": "Remote"},
    ]
    unique, dup_count = JobIngestionService.deduplicate_job_stream(jobs)
    assert len(unique) == 2
    assert dup_count == 1
    assert [j["id"] for j in unique] == ["adzuna-101", "adzuna-102"]


def test_deduplication_by_normalized_composite_key():
    """Verify listings with different or missing IDs but same title/company/location are deduplicated."""
    jobs = [
        {"id": "job-1", "title": "Senior Software Engineer", "company": "Acme Inc.", "location": "New York, NY"},
        # Same normalized composite: "senior software engineer|acme inc|new york ny"
        {"id": "job-2", "title": "  senior  Software   Engineer ", "company": "Acme Inc", "location": "New York, NY "},
        {"id": "job-3", "title": "Senior Software Engineer", "company": "Different Co", "location": "New York, NY"},
    ]
    unique, dup_count = JobIngestionService.deduplicate_job_stream(jobs)
    assert len(unique) == 2
    assert dup_count == 1
    assert unique[0]["id"] == "job-1"
    assert unique[1]["id"] == "job-3"


# ---------------------------------------------------------------------------
# 2. MARKET DEMAND CALCULATION ON KNOWN FIXTURE SET
# ---------------------------------------------------------------------------

def test_market_demand_calculation_known_fixtures():
    """Test market demand calculation on 4 known deterministic job fixtures.
    
    Known Dataset:
    - Job 1: mentions Python, FastAPI, Docker (3 skills)
    - Job 2: mentions Python, Docker (2 skills)
    - Job 3: mentions Python, React (2 skills)
    - Job 4: mentions React, TypeScript (2 skills)
    
    Total unique listings analyzed = 4
    Expected:
    - Python: 3 / 4 = 75.0%
    - Docker: 2 / 4 = 50.0%
    - React: 2 / 4 = 50.0%
    - FastAPI: 1 / 4 = 25.0%
    - TypeScript: 1 / 4 = 25.0%
    """
    known_jobs = [
        {
            "id": "known-1",
            "title": "Backend Python Developer",
            "company": "Company A",
            "location": "Remote",
            "description": "Seeking Python engineer with FastAPI and Docker experience.",
        },
        {
            "id": "known-2",
            "title": "DevOps Engineer",
            "company": "Company B",
            "location": "Austin, TX",
            "description": "Python scripting and containerization using Docker.",
        },
        {
            "id": "known-3",
            "title": "Full Stack Engineer",
            "company": "Company C",
            "location": "Boston, MA",
            "description": "Working with Python backend and React frontend.",
        },
        {
            "id": "known-4",
            "title": "Frontend Engineer",
            "company": "Company D",
            "location": "Seattle, WA",
            "description": "Building UI with React and TypeScript.",
        },
    ]

    service = MarketDemandService()
    result = service.analyze_market_demand(provided_jobs=known_jobs)

    # 1. Denominator check
    assert result["total_unique_listings_analyzed"] == 4
    assert result["status"] == "sufficient_data"

    skills_dict = {s["skill_name"]: s for s in result["top_skills"]}

    # 2. Denominator reported in every skill object
    for item in result["top_skills"]:
        assert item["total_listings_analyzed"] == 4

    # 3. Exact formula percentage verification
    assert skills_dict["Python"]["matching_listings_count"] == 3
    assert skills_dict["Python"]["demand_percentage"] == 75.0

    assert skills_dict["Docker"]["matching_listings_count"] == 2
    assert skills_dict["Docker"]["demand_percentage"] == 50.0

    assert skills_dict["React"]["matching_listings_count"] == 2
    assert skills_dict["React"]["demand_percentage"] == 50.0

    assert skills_dict["FastAPI"]["matching_listings_count"] == 1
    assert skills_dict["FastAPI"]["demand_percentage"] == 25.0

    assert skills_dict["TypeScript"]["matching_listings_count"] == 1
    assert skills_dict["TypeScript"]["demand_percentage"] == 25.0


# ---------------------------------------------------------------------------
# 3. EMPTY / INSUFFICIENT DATA STATE
# ---------------------------------------------------------------------------

def test_market_demand_empty_insufficient_data_state():
    """Verify empty/insufficient-data behavior when no jobs match the query."""
    service = MarketDemandService()
    result = service.analyze_market_demand(provided_jobs=[])

    assert result["total_unique_listings_analyzed"] == 0
    assert result["status"] == "insufficient_data"
    assert "Insufficient data" in result["message"]
    assert result["top_skills"] == []


# ---------------------------------------------------------------------------
# 4. API ENDPOINT TESTS (GET /api/jobs/search & GET /api/market-demand)
# ---------------------------------------------------------------------------

def test_api_jobs_search_with_sample_banner(client, monkeypatch):
    """Test GET /api/jobs/search endpoint serves labeled sample data when credentials not set."""
    monkeypatch.setattr(settings, "ADZUNA_APP_ID", "")
    monkeypatch.setattr(settings, "ADZUNA_APP_KEY", "")
    response = client.get("/api/jobs/search?role=Python&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["total_count"] > 0
    assert data["is_sample_data"] is True
    assert "SAMPLE DATA" in data["banner_message"]
    assert len(data["results"]) <= 5


def test_api_market_demand_endpoint(client, monkeypatch):
    """Test GET /api/market-demand endpoint calculates demand with denominator."""
    monkeypatch.setattr(settings, "ADZUNA_APP_ID", "")
    monkeypatch.setattr(settings, "ADZUNA_APP_KEY", "")
    response = client.get("/api/market-demand?role=Developer&limit=10")
    assert response.status_code == 200
    data = response.json()

    assert "total_unique_listings_analyzed" in data
    assert data["total_unique_listings_analyzed"] > 0
    assert data["is_sample_data"] is True
    assert "SAMPLE DATA" in data["banner_message"]
    assert len(data["top_skills"]) > 0

    # Ensure every returned skill has denominator matching total_unique_listings_analyzed
    for skill in data["top_skills"]:
        assert skill["total_listings_analyzed"] == data["total_unique_listings_analyzed"]
        assert 0.0 <= skill["demand_percentage"] <= 100.0


def test_api_market_demand_nonexistent_role_returns_insufficient_data(client):
    """Test GET /api/market-demand with a query that matches no listings."""
    response = client.get("/api/market-demand?role=NonexistentRoleXYZ123456&location=Nowhere")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "insufficient_data"
    assert data["total_unique_listings_analyzed"] == 0
    assert data["top_skills"] == []
