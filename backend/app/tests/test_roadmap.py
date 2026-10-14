"""Tests for Role Learning Roadmap service and GET /api/roadmap endpoint.

Verifies:
1. Deterministic ordering of missing + needs_review skills by real demand_percentage descending
2. Reuse of SkillGapService output (matched_skills, priority_thresholds disclaimer, overall_match_percentage)
3. Tightly scoped LLM prompt constraints (explicitly prohibiting fabricated course titles, URLs,
   instructor names, certifications, or time estimates)
4. Ownership check (User B cannot request a roadmap for User A's resume_id -> 403 Forbidden)
5. Resilient LLM failure/timeout fallback (returns 200 OK with ordered demand-data steps and
   'AI explanation unavailable' per step, never blocking the response or fabricating explanations)
"""

import json
import httpx
import pytest
import pymupdf
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.services.roadmap_service import (
    RoadmapService,
    AI_EXPLANATION_UNAVAILABLE_NOTE,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user1_headers(client):
    reg = client.post(
        "/api/auth/register",
        json={
            "email": "roadmap_user1@example.com",
            "password": "Password123!",
            "full_name": "Roadmap User 1",
        },
    )
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user2_headers(client):
    reg = client.post(
        "/api/auth/register",
        json={
            "email": "roadmap_user2@example.com",
            "password": "Password123!",
            "full_name": "Roadmap User 2",
        },
    )
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def uploaded_resume_id(client, user1_headers):
    """Upload a valid PDF resume for User 1."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (50, 72),
        "Alex Engineer\nSkills: Python, Git\nExperience building backend services with Python and Git.",
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    res = client.post(
        "/api/resumes/upload",
        headers=user1_headers,
        files={"file": ("alex_roadmap.pdf", pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 201
    return res.json()["id"]


def test_deterministic_ordering_by_demand_percentage():
    """Verify missing and needs_review skills are ordered strictly by demand_percentage descending."""
    missing = [
        {
            "skill": "Kubernetes",
            "canonical_name": "Kubernetes",
            "status": "missing",
            "demand_percentage": 35.0,
            "matching_listings_count": 7,
            "total_listings_analyzed": 20,
            "priority": "Low",
        },
        {
            "skill": "Docker",
            "canonical_name": "Docker",
            "status": "missing",
            "demand_percentage": 85.0,
            "matching_listings_count": 17,
            "total_listings_analyzed": 20,
            "priority": "High",
        },
        {
            "skill": "PostgreSQL",
            "canonical_name": "PostgreSQL",
            "status": "missing",
            "demand_percentage": 60.0,
            "matching_listings_count": 12,
            "total_listings_analyzed": 20,
            "priority": "Medium",
        },
    ]
    needs_review = [
        {
            "skill": "Amazon Web Services",
            "canonical_name": "Amazon Web Services",
            "status": "needs_review",
            "demand_percentage": 75.0,
            "matching_listings_count": 15,
            "total_listings_analyzed": 20,
            "priority": "High",
        },
        {
            "skill": "TypeScript",
            "canonical_name": "TypeScript",
            "status": "needs_review",
            "demand_percentage": 60.0,
            "matching_listings_count": 12,
            "total_listings_analyzed": 20,
            "priority": "Medium",
        },
    ]

    ordered = RoadmapService.order_skills_by_demand(missing, needs_review)
    ordered_names = [s["skill"] for s in ordered]
    ordered_demands = [s["demand_percentage"] for s in ordered]

    # Expected order: Docker (85%), AWS (75%), PostgreSQL (60%, missing), TypeScript (60%, needs_review), Kubernetes (35%)
    assert ordered_names == [
        "Docker",
        "Amazon Web Services",
        "PostgreSQL",
        "TypeScript",
        "Kubernetes",
    ]
    assert ordered_demands == sorted(ordered_demands, reverse=True)


def test_roadmap_endpoint_ordering_and_mocked_llm_success(
    client, user1_headers, uploaded_resume_id, monkeypatch
):
    """Verify GET /api/roadmap orders steps by real demand %, includes matched_skills, and parses LLM output."""
    monkeypatch.setattr(settings, "ADZUNA_APP_ID", "")
    monkeypatch.setattr(settings, "ADZUNA_APP_KEY", "")

    # Verify prompt constraints explicitly forbid fabricating courses, URLs, instructors, certs, or time estimates
    sample_prompt = RoadmapService.build_skill_prompt("Docker", "Backend Developer")
    assert "DO NOT fabricate" in sample_prompt
    assert "course titles" in sample_prompt
    assert "URLs" in sample_prompt
    assert "instructor names" in sample_prompt
    assert "certifications" in sample_prompt
    assert "time estimates" in sample_prompt

    def fake_llm_completion(self, prompt: str) -> str:
        return json.dumps(
            {
                "explanation": "Essential containerization technology for packaging and deploying services consistently.",
                "resource_suggestions": [
                    "Official documentation and reference guides",
                    "Interactive tutorials on freeCodeCamp or roadmap.sh",
                    "Practice project: containerize a multi-service REST API with a database",
                ],
                "practice_project_idea": "Containerize a FastAPI service and PostgreSQL database using Docker Compose.",
            }
        )

    monkeypatch.setattr(RoadmapService, "_request_llm_completion", fake_llm_completion)

    res = client.get(
        "/api/roadmap",
        params={
            "resume_id": uploaded_resume_id,
            "target_role": "Developer",
            "target_location": "San Francisco, CA",
        },
        headers=user1_headers,
    )
    assert res.status_code == 200
    data = res.json()

    assert data["resume_id"] == uploaded_resume_id
    assert data["target_role"] == "Developer"
    assert data["overall_match_percentage"] >= 0.0
    assert "Project-defined priority thresholds, not industry standards" in data["priority_thresholds"]["note"]
    assert "general learning categories" in data["resource_disclaimer"]
    assert isinstance(data["matched_skills"], list)
    assert len(data["matched_skills"]) > 0

    steps = data["roadmap_steps"]
    assert len(steps) > 0

    # Verify deterministic ordering by demand_percentage descending and 1-indexed step_number
    demands = [step["demand_percentage"] for step in steps]
    assert demands == sorted(demands, reverse=True)

    for idx, step in enumerate(steps, start=1):
        assert step["step_number"] == idx
        assert step["status"] in ("missing", "needs_review")
        assert step["priority"] in ("High", "Medium", "Low")
        assert step["ai_explanation_available"] is True
        assert "Essential containerization technology" in step["explanation"]
        assert len(step["resource_suggestions"]) == 3


def test_roadmap_ownership_check(client, user1_headers, user2_headers, uploaded_resume_id):
    """Verify User 2 cannot generate a roadmap for User 1's resume_id (403 Forbidden)."""
    forbidden_res = client.get(
        "/api/roadmap",
        params={"resume_id": uploaded_resume_id, "target_role": "Developer"},
        headers=user2_headers,
    )
    assert forbidden_res.status_code == 403
    assert "permission" in forbidden_res.json()["detail"].lower()

    not_found_res = client.get(
        "/api/roadmap",
        params={"resume_id": 99999, "target_role": "Developer"},
        headers=user1_headers,
    )
    assert not_found_res.status_code == 404


def test_roadmap_llm_failure_and_timeout_fallback(
    client, user1_headers, uploaded_resume_id, monkeypatch
):
    """Verify LLM failure/timeout never blocks the response and returns data-only steps with 'AI explanation unavailable'."""
    monkeypatch.setattr(settings, "ADZUNA_APP_ID", "")
    monkeypatch.setattr(settings, "ADZUNA_APP_KEY", "")

    def failing_llm_completion(self, prompt: str) -> str:
        raise httpx.TimeoutException("LLM request timed out after 8.0 seconds")

    monkeypatch.setattr(RoadmapService, "_request_llm_completion", failing_llm_completion)

    res = client.get(
        "/api/roadmap",
        params={"resume_id": uploaded_resume_id, "target_role": "Developer"},
        headers=user1_headers,
    )
    assert res.status_code == 200
    data = res.json()

    steps = data["roadmap_steps"]
    assert len(steps) > 0

    # Verify steps are still deterministically ordered by demand_percentage descending
    demands = [step["demand_percentage"] for step in steps]
    assert demands == sorted(demands, reverse=True)

    # Verify every step has real demand data and the explicit 'AI explanation unavailable' note
    for step in steps:
        assert step["ai_explanation_available"] is False
        assert step["explanation"] == AI_EXPLANATION_UNAVAILABLE_NOTE
        assert step["resource_suggestions"] == []
        assert step["practice_project_idea"] is None
        assert step["demand_percentage"] >= 0.0
        assert step["priority"] in ("High", "Medium", "Low")
