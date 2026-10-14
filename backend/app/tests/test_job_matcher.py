"""Tests for job recommendations service and API endpoints.

Verifies:
1. Match-score calculation against a known fixture (resume skills + mock listings with known overlaps).
2. Ranking order: listings strictly ordered by match_percentage descending.
3. Ownership check: User A cannot query recommendations for User B's resume (403 Forbidden).
4. Missing-credentials fallback: Gracefully returns clearly-labeled sample fixtures with banner.
5. Nonexistent resume check: Returns 404 Not Found.
"""

import io
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
from app.models import User, Resume, ExtractedSkill
from app.services.job_matcher import JobMatcherService

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
        json={"email": "job_user1@example.com", "password": "Password123!", "full_name": "Job User 1"},
    )
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user2_headers(client):
    reg = client.post(
        "/api/auth/register",
        json={"email": "job_user2@example.com", "password": "Password123!", "full_name": "Job User 2"},
    )
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_test_pdf_bytes(text_lines):
    doc = pymupdf.open()
    page = doc.new_page()
    full_text = "\n".join(text_lines)
    page.insert_text((50, 72), full_text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ---------------------------------------------------------------------------
# 1. MATCH-SCORE CALCULATION ON KNOWN FIXTURES
# ---------------------------------------------------------------------------

def test_job_matcher_match_score_calculation_known_fixtures():
    """Verify match-score calculation against known resume skills and mock listings."""
    db = TestingSessionLocal()
    try:
        # Create user & resume
        user = User(email="test_known@example.com", hashed_password="hashed_pw")
        db.add(user)
        db.commit()
        db.refresh(user)

        resume = Resume(
            user_id=user.id,
            filename="backend_dev.pdf",
            file_path="/tmp/fake_backend_dev.pdf",
            raw_text="Experienced engineer proficient in Python, Docker, and PostgreSQL.",
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # Add extracted skills for this candidate
        db.add(ExtractedSkill(resume_id=resume.id, skill_name="Python", canonical_name="Python", category="Programming Languages"))
        db.add(ExtractedSkill(resume_id=resume.id, skill_name="Docker", canonical_name="Docker", category="DevOps"))
        db.add(ExtractedSkill(resume_id=resume.id, skill_name="PostgreSQL", canonical_name="PostgreSQL", category="Databases"))
        db.commit()

        # Known mock listings:
        # Listing 1: requires Python, Docker (2 required, 2 matched -> 100.0%)
        # Listing 2: requires Python, React, TypeScript (3 required, 1 matched -> 33.3%)
        # Listing 3: requires Kubernetes, Terraform, AWS (3 required, 0 matched -> 0.0%)
        mock_listings = [
            {
                "id": "mock-1",
                "title": "Backend Python Developer",
                "company": "Alpha Tech",
                "location": "Remote",
                "description": "Seeking Python engineer with Docker experience.",
                "salary_min": 130000,
                "salary_max": 160000,
                "url": "https://example.com/jobs/alpha-1",
                "posted_at": "2026-10-10T00:00:00Z",
            },
            {
                "id": "mock-2",
                "title": "Full Stack Engineer",
                "company": "Beta Systems",
                "location": "New York, NY",
                "description": "Seeking Full Stack engineer skilled in Python, React, and TypeScript.",
                "salary_min": 120000,
                "salary_max": 150000,
                "url": "https://example.com/jobs/beta-2",
                "posted_at": "2026-10-11T00:00:00Z",
            },
            {
                "id": "mock-3",
                "title": "Cloud Architect",
                "company": "Gamma Cloud",
                "location": "San Francisco, CA",
                "description": "Requires deep knowledge of Kubernetes, Terraform, and AWS cloud.",
                "salary_min": 170000,
                "salary_max": 200000,
                "url": "https://example.com/jobs/gamma-3",
                "posted_at": "2026-10-12T00:00:00Z",
            },
        ]

        service = JobMatcherService(db=db)
        result = service.recommend_jobs(
            user_id=user.id,
            resume_id=resume.id,
            provided_listings=mock_listings,
        )

        assert result["total_recommended"] == 3
        recs = {r["job_id"]: r for r in result["recommendations"]}

        # Listing 1: 2/2 = 100.0%
        assert recs["mock-1"]["match_percentage"] == 100.0
        assert set(recs["mock-1"]["matched_skills"]) == {"Python", "Docker"}
        assert recs["mock-1"]["missing_skills"] == []
        assert recs["mock-1"]["salary_range"] == "$130,000 - $160,000"
        assert recs["mock-1"]["apply_url"] == "https://example.com/jobs/alpha-1"

        # Listing 2: 1/3 = 33.3%
        assert recs["mock-2"]["match_percentage"] == 33.3
        assert recs["mock-2"]["matched_skills"] == ["Python"]
        assert set(recs["mock-2"]["missing_skills"]) == {"React", "TypeScript"}

        # Listing 3: 0/3 = 0.0%
        assert recs["mock-3"]["match_percentage"] == 0.0
        assert recs["mock-3"]["matched_skills"] == []
        assert set(recs["mock-3"]["missing_skills"]) == {"Amazon Web Services", "Kubernetes", "Terraform"}

    finally:
        db.close()


# ---------------------------------------------------------------------------
# 2. RANKING ORDER & MINIMUM MATCH FILTER TESTS
# ---------------------------------------------------------------------------

def test_job_matcher_ranking_order_and_min_match():
    """Verify listings are ranked strictly descending by match percentage, and min_match filters correctly."""
    db = TestingSessionLocal()
    try:
        user = User(email="test_rank@example.com", hashed_password="hashed_pw")
        db.add(user)
        db.commit()
        db.refresh(user)

        resume = Resume(
            user_id=user.id,
            filename="rank_test.pdf",
            file_path="/tmp/fake_rank.pdf",
            raw_text="Skills: Python, FastAPI.",
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        db.add(ExtractedSkill(resume_id=resume.id, skill_name="Python", canonical_name="Python", category="Programming Languages"))
        db.add(ExtractedSkill(resume_id=resume.id, skill_name="FastAPI", canonical_name="FastAPI", category="Backend Frameworks"))
        db.commit()

        mock_listings = [
            # 0% match
            {"id": "rank-low", "title": "DevOps", "company": "Co C", "description": "Needs Terraform and Kubernetes."},
            # 100% match
            {"id": "rank-high", "title": "Python Lead", "company": "Co A", "description": "Needs Python and FastAPI."},
            # 50% match
            {"id": "rank-mid", "title": "Python Developer", "company": "Co B", "description": "Needs Python and React."},
        ]

        service = JobMatcherService(db=db)

        # 1. Full ranking without min_match
        result = service.recommend_jobs(
            user_id=user.id,
            resume_id=resume.id,
            provided_listings=mock_listings,
        )

        ranked = result["recommendations"]
        assert len(ranked) == 3
        # Strict descending order check: 100.0% -> 50.0% -> 0.0%
        assert ranked[0]["job_id"] == "rank-high"
        assert ranked[0]["match_percentage"] == 100.0
        assert ranked[1]["job_id"] == "rank-mid"
        assert ranked[1]["match_percentage"] == 50.0
        assert ranked[2]["job_id"] == "rank-low"
        assert ranked[2]["match_percentage"] == 0.0

        # 2. Filter with min_match = 60.0%
        filtered_result = service.recommend_jobs(
            user_id=user.id,
            resume_id=resume.id,
            min_match=60.0,
            provided_listings=mock_listings,
        )
        assert filtered_result["total_recommended"] == 1
        assert filtered_result["recommendations"][0]["job_id"] == "rank-high"

    finally:
        db.close()


# ---------------------------------------------------------------------------
# 3. OWNERSHIP ENFORCEMENT TEST (User A cannot access User B's resume)
# ---------------------------------------------------------------------------

def test_job_matcher_ownership_check(client, user1_headers, user2_headers):
    """Verify user A cannot query recommendations for user B's resume (HTTP 403)."""
    # User 2 uploads a resume
    pdf_bytes = create_test_pdf_bytes([
        "Alice Smith",
        "Senior Software Engineer",
        "Technical Skills: Python, Docker, React, PostgreSQL",
        "Experience: 5 years designing distributed web systems and REST APIs.",
    ])
    upload_res = client.post(
        "/api/resumes/upload",
        headers=user2_headers,
        files={"file": ("alice_resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 201
    user2_resume_id = upload_res.json()["id"]

    # User 1 attempts to query recommendations for User 2's resume
    forbidden_res = client.get(
        f"/api/jobs/recommendations?resume_id={user2_resume_id}",
        headers=user1_headers,
    )
    assert forbidden_res.status_code == 403
    assert "permission" in forbidden_res.json()["detail"].lower()

    # User 2 can query their own resume successfully
    allowed_res = client.get(
        f"/api/jobs/recommendations?resume_id={user2_resume_id}",
        headers=user2_headers,
    )
    assert allowed_res.status_code == 200
    assert allowed_res.json()["resume_id"] == user2_resume_id


# ---------------------------------------------------------------------------
# 4. MISSING-CREDENTIALS FALLBACK & ENDPOINT BEHAVIOR
# ---------------------------------------------------------------------------

def test_job_matcher_missing_credentials_fallback(client, user1_headers, monkeypatch):
    """Verify GET /api/jobs/recommendations returns clearly-labeled sample data when credentials not set."""
    monkeypatch.setattr(settings, "ADZUNA_APP_ID", "")
    monkeypatch.setattr(settings, "ADZUNA_APP_KEY", "")

    # User 1 uploads a resume
    pdf_bytes = create_test_pdf_bytes([
        "Bob Developer",
        "Full Stack Developer",
        "Core Skills: Python, FastAPI, Docker, and PostgreSQL.",
        "Summary: Passionate about high performance backend development.",
    ])
    upload_res = client.post(
        "/api/resumes/upload",
        headers=user1_headers,
        files={"file": ("bob_resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 201
    resume_id = upload_res.json()["id"]

    # Call recommendations endpoint
    rec_res = client.get(
        f"/api/jobs/recommendations?resume_id={resume_id}&limit=5",
        headers=user1_headers,
    )
    assert rec_res.status_code == 200
    data = rec_res.json()

    # Verify fallback banner and metadata
    assert data["is_sample_data"] is True
    assert "SAMPLE DATA" in data["banner_message"]
    assert data["resume_id"] == resume_id
    assert len(data["recommendations"]) > 0
    assert len(data["recommendations"]) <= 5

    # Check structure of recommended items
    first = data["recommendations"][0]
    assert "job_id" in first
    assert "title" in first
    assert "company" in first
    assert "match_percentage" in first
    assert isinstance(first["matched_skills"], list)
    assert isinstance(first["missing_skills"], list)
    assert "description_snippet" in first
    assert "apply_url" in first


# ---------------------------------------------------------------------------
# 5. NONEXISTENT RESUME RETURNS 404
# ---------------------------------------------------------------------------

def test_job_matcher_nonexistent_resume_returns_404(client, user1_headers):
    """Verify querying recommendations for a nonexistent resume returns 404."""
    resp = client.get(
        "/api/jobs/recommendations?resume_id=999999",
        headers=user1_headers,
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 6. REGRESSION TEST: CANDIDATE'S REAL SKILL SET AGAINST IT-RELEVANT LISTINGS
# ---------------------------------------------------------------------------

def test_job_matcher_candidate_real_skills_nonzero_match():
    """Regression test: verify candidate's actual extracted skill set matches IT listings with non-zero %.
    
    Verifies:
    1. Candidate with Full Stack skills (React, Node.js, JavaScript, Python, etc.) achieves non-zero match score on IT roles.
    2. Skills in job titles (e.g. 'React Developer') are properly extracted alongside description text.
    3. Listings with 0 detected skills cleanly report is_scorable=False and match_percentage=None (not misleading 0.0%).
    4. Scorable listings are ranked above unscored listings.
    """
    db = TestingSessionLocal()
    try:
        user = User(email="candidate_it@example.com", hashed_password="hashed_pw")
        db.add(user)
        db.commit()
        db.refresh(user)

        resume = Resume(
            user_id=user.id,
            filename="Kamaleshwaran_Resume.pdf",
            file_path="/tmp/kamaleshwaran_resume.pdf",
            raw_text="Experienced Full Stack Developer with expertise in React, JavaScript, Node.js, Python, SQL, Git, and REST APIs.",
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # Candidate's actual extracted skills from diagnostic:
        candidate_skills = [
            ("Git", "DevOps"),
            ("JavaScript", "Programming Languages"),
            ("React", "Frontend Frameworks"),
            ("Material UI", "Frontend Frameworks"),
            ("Node.js", "Backend Frameworks"),
            ("Express.js", "Backend Frameworks"),
            ("Flask", "Backend Frameworks"),
            ("REST API", "Web Technologies"),
            ("MongoDB", "Databases"),
            ("SQL", "Databases"),
            ("HTML5", "Web Technologies"),
            ("CSS3", "Web Technologies"),
        ]
        for s_name, cat in candidate_skills:
            db.add(ExtractedSkill(
                resume_id=resume.id,
                skill_name=s_name,
                canonical_name=s_name,
                category=cat,
            ))
        db.commit()

        # IT Mock Listings:
        # Listing 1: Title: 'Full Stack Engineer - React & Node.js', requires React, Node.js, JavaScript, Docker
        # (3 matched out of 4 required -> 75.0% match)
        # Listing 2: Title: 'Frontend React Developer', requires React, JavaScript, TypeScript
        # (2 matched out of 3 required -> 66.7% match)
        # Listing 3: Unscorable listing with 0 recognized tech skills
        mock_it_listings = [
            {
                "id": "it-1",
                "title": "Full Stack Engineer - React & Node.js",
                "company": "Tech Innovators",
                "location": "Remote",
                "description": "We are seeking a Full Stack developer with strong skills in React, Node.js, and JavaScript. Docker is a plus.",
                "salary_min": 120000,
                "salary_max": 150000,
                "url": "https://example.com/apply/it-1",
                "posted_at": "2026-10-12T00:00:00Z",
            },
            {
                "id": "it-2",
                "title": "Frontend React Developer",
                "company": "CloudFront Labs",
                "location": "New York, NY",
                "description": "Building modern UI dashboards. Required: React, JavaScript, TypeScript.",
                "salary_min": 110000,
                "salary_max": 140000,
                "url": "https://example.com/apply/it-2",
                "posted_at": "2026-10-12T00:00:00Z",
            },
            {
                "id": "unscored-3",
                "title": "General Associate",
                "company": "Generic Corp",
                "location": "Austin, TX",
                "description": "Fast paced environment, great benefits, click apply for details.",
                "salary_min": 50000,
                "salary_max": 60000,
                "url": "https://example.com/apply/unscored-3",
                "posted_at": "2026-10-12T00:00:00Z",
            },
        ]

        service = JobMatcherService(db=db)
        result = service.recommend_jobs(
            user_id=user.id,
            resume_id=resume.id,
            provided_listings=mock_it_listings,
        )

        recs = result["recommendations"]
        assert len(recs) == 3

        # Scorable listings must have non-zero match percentages
        it_1 = next(r for r in recs if r["job_id"] == "it-1")
        assert it_1["match_percentage"] is not None
        assert it_1["match_percentage"] > 0.0
        assert it_1["match_percentage"] == 75.0
        assert "React" in it_1["matched_skills"]
        assert "Node.js" in it_1["matched_skills"]
        assert "JavaScript" in it_1["matched_skills"]
        assert "Docker" in it_1["missing_skills"]
        assert it_1["is_scorable"] is True

        it_2 = next(r for r in recs if r["job_id"] == "it-2")
        assert it_2["match_percentage"] is not None
        assert it_2["match_percentage"] > 0.0
        assert it_2["match_percentage"] == 66.7
        assert "React" in it_2["matched_skills"]
        assert "JavaScript" in it_2["matched_skills"]
        assert it_2["is_scorable"] is True

        # Unscorable listing: must cleanly report is_scorable=False and match_percentage=None
        unscored = next(r for r in recs if r["job_id"] == "unscored-3")
        assert unscored["is_scorable"] is False
        assert unscored["match_percentage"] is None
        assert unscored["matched_skills"] == []

        # Ranking: Scorable listings ordered descending (75.0% -> 66.7%), unscored listing last
        assert recs[0]["job_id"] == "it-1"
        assert recs[1]["job_id"] == "it-2"
        assert recs[2]["job_id"] == "unscored-3"

    finally:
        db.close()

