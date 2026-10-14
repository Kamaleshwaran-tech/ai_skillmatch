"""Tests for skill gap analysis service and endpoints.

Verifies:
1. End-to-end POST /api/skill-gap/analyze and GET /api/skill-gap/{analysis_id}
2. Calculation of matched, missing, and needs_review skills
3. Inclusion of project-defined priority thresholds (High >= 70%, Medium 40-69%, Low < 40%)
4. Denominator (total unique listings analyzed) reported in response
5. Ownership protection (preventing user B from accessing user A's analysis)
"""

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
        json={"email": "gap_user1@example.com", "password": "Password123!", "full_name": "Gap User 1"},
    )
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user2_headers(client):
    reg = client.post(
        "/api/auth/register",
        json={"email": "gap_user2@example.com", "password": "Password123!", "full_name": "Gap User 2"},
    )
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def uploaded_resume_id(client, user1_headers):
    """Helper fixture uploading a valid resume for user 1."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (50, 72),
        "Alex Engineer\nSkills: Python, FastAPI, Docker, SQL\nExperience in backend microservices.",
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    res = client.post(
        "/api/resumes/upload",
        headers=user1_headers,
        files={"file": ("alex_resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 201
    return res.json()["id"]


def test_post_skill_gap_analyze_and_get_by_id(client, user1_headers, user2_headers, uploaded_resume_id, monkeypatch):
    """Test full skill gap analysis execution and GET retrieval with ownership checks."""
    monkeypatch.setattr(settings, "ADZUNA_APP_ID", "")
    monkeypatch.setattr(settings, "ADZUNA_APP_KEY", "")
    req_body = {
        "resume_id": uploaded_resume_id,
        "target_role": "Developer",
        "target_location": "San Francisco, CA",
        "limit": 10,
    }

    # 1. POST /api/skill-gap/analyze
    post_res = client.post("/api/skill-gap/analyze", json=req_body, headers=user1_headers)
    assert post_res.status_code == 201
    data = post_res.json()

    # Verify response schema fields
    assert "analysis_id" in data
    assert data["target_role"] == "Developer"
    assert data["target_location"] == "San Francisco, CA"
    assert data["total_listings_analyzed"] > 0
    assert "data_source" in data
    assert "analysis_timestamp" in data
    assert "priority_thresholds" in data
    assert "Project-defined" in data["priority_thresholds"]["note"]

    # Verify categories
    assert isinstance(data["matched_skills"], list)
    assert isinstance(data["missing_skills"], list)
    assert isinstance(data["needs_review_skills"], list)

    # Candidate has Python, FastAPI, Docker, SQL
    matched_names = [s["canonical_name"] for s in data["matched_skills"]]
    assert "Python" in matched_names or "FastAPI" in matched_names or "Docker" in matched_names

    # Check that priority labels are present (High, Medium, or Low)
    for s in data["matched_skills"] + data["missing_skills"] + data["needs_review_skills"]:
        assert s["priority"] in ["High", "Medium", "Low"]
        assert s["total_listings_analyzed"] == data["total_listings_analyzed"]

    analysis_id = data["analysis_id"]

    # 2. GET /api/skill-gap/{analysis_id} (Owner)
    get_res = client.get(f"/api/skill-gap/{analysis_id}", headers=user1_headers)
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["analysis_id"] == analysis_id
    assert get_data["summary"]["total_demanded_skills"] == data["summary"]["total_demanded_skills"]

    # 3. GET /api/skill-gap/{analysis_id} (Non-owner -> 403 Forbidden)
    forbidden_get = client.get(f"/api/skill-gap/{analysis_id}", headers=user2_headers)
    assert forbidden_get.status_code == 403
    assert "permission" in forbidden_get.json()["detail"].lower()


def test_skill_gap_analyze_nonexistent_resume_fails(client, user1_headers):
    """Verify 404 is returned if resume_id does not exist."""
    req_body = {
        "resume_id": 99999,
        "target_role": "Python Developer",
    }
    res = client.post("/api/skill-gap/analyze", json=req_body, headers=user1_headers)
    assert res.status_code == 404
