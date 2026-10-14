"""Unit and integration tests for resume parser, skill extractor, normalizer, and API routes.

Tests cover:
- Valid PDF extraction
- Valid DOCX extraction
- Empty file rejection
- Scanned PDF rejection with explanation
- Alias case 1: JS -> JavaScript
- Alias case 2: Postgre SQL / Node / ML -> PostgreSQL, Node.js, Machine Learning
- False-positive case: 'C' inside unrelated words ('Company', 'Co-op', 'cat') and stand-alone false positives
- Ownership checks on upload, skills access, and deletion
"""

import os
import io
import pytest
import pymupdf
import docx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.services.resume_parser import ResumeParserService
from app.services.skill_normalizer import SkillNormalizer
from app.services.skill_extractor import SkillExtractor
from fastapi import HTTPException


# Database fixture setup
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
def auth_headers(client):
    reg = client.post(
        "/api/auth/register",
        json={"email": "resume_user@example.com", "password": "Password123!", "full_name": "Resume User"},
    )
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_user_headers(client):
    reg = client.post(
        "/api/auth/register",
        json={"email": "other_user@example.com", "password": "Password123!", "full_name": "Other User"},
    )
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. PARSER UNIT TESTS
# ---------------------------------------------------------------------------

def test_parse_valid_pdf(tmp_path):
    """Test PyMuPDF parsing on a valid text PDF document."""
    pdf_path = tmp_path / "valid_resume.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (50, 72),
        "John Doe\nSoftware Engineer\nTechnical Skills: Python, FastAPI, Docker, PostgreSQL\nExperience: 5 years in backend development.",
    )
    doc.save(str(pdf_path))
    doc.close()

    result = ResumeParserService.parse_file(str(pdf_path), "valid_resume.pdf")
    assert "Python" in result["raw_text"]
    assert "FastAPI" in result["raw_text"]
    assert result["page_count"] == 1
    assert result["metadata"]["format"] == "pdf"


def test_parse_valid_docx(tmp_path):
    """Test python-docx parsing on a valid DOCX document."""
    docx_path = tmp_path / "valid_resume.docx"
    doc = docx.Document()
    doc.add_heading("Jane Smith - Full Stack Developer", level=1)
    doc.add_paragraph("Skills: React, TypeScript, Node.js, Next.js, Jest, Git")
    doc.add_paragraph("Experience: Developed modern web applications using Redux and Tailwind CSS.")
    doc.save(str(docx_path))

    result = ResumeParserService.parse_file(str(docx_path), "valid_resume.docx")
    assert "TypeScript" in result["raw_text"]
    assert "React" in result["raw_text"]
    assert result["metadata"]["format"] == "docx"


def test_parse_empty_file_rejected(tmp_path):
    """Test that completely empty (0 bytes) files are rejected with a clear explanation."""
    empty_path = tmp_path / "empty.pdf"
    empty_path.write_bytes(b"")

    with pytest.raises(HTTPException) as exc_info:
        ResumeParserService.parse_file(str(empty_path), "empty.pdf")
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()


def test_parse_scanned_pdf_rejected_with_explanation(tmp_path):
    """Test that a scanned / image-only PDF is rejected with an explanation rather than an empty list."""
    scanned_path = tmp_path / "scanned_doc.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    # Create a dummy 100x100 RGB image simulating a scanned document page
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 100, 100), False)
    page.insert_image(pymupdf.Rect(50, 50, 400, 500), pixmap=pix)
    doc.save(str(scanned_path))
    doc.close()

    with pytest.raises(HTTPException) as exc_info:
        ResumeParserService.parse_file(str(scanned_path), "scanned_doc.pdf")
    assert exc_info.value.status_code == 422
    assert "scanned document or image-only" in exc_info.value.detail


# ---------------------------------------------------------------------------
# 2. SKILL NORMALIZER & EXTRACTOR ALIAS AND FALSE-POSITIVE TESTS
# ---------------------------------------------------------------------------

def test_alias_resolution_js_to_javascript():
    """Test alias resolution: JS -> JavaScript."""
    normalizer = SkillNormalizer()
    extractor = SkillExtractor(normalizer)

    text = "Proficient in JS and modern frontend UI architectures."
    extracted = extractor.extract_skills(text)

    canonicals = [s["canonical_name"] for s in extracted]
    assert "JavaScript" in canonicals

    js_entry = next(s for s in extracted if s["canonical_name"] == "JavaScript")
    assert js_entry["matched_text"] == "JS"
    assert "JS" in js_entry["evidence_snippet"]


def test_alias_resolution_postgres_node_ml():
    """Test alias resolution: Postgre SQL -> PostgreSQL, Node -> Node.js, ML -> Machine Learning."""
    normalizer = SkillNormalizer()
    extractor = SkillExtractor(normalizer)

    text = (
        "Experienced in backend engineering using Node and Postgre SQL. "
        "Built predictive ML models with deep learning pipelines in Python."
    )
    extracted = extractor.extract_skills(text)
    canonicals = {s["canonical_name"]: s for s in extracted}

    assert "PostgreSQL" in canonicals
    assert "Node.js" in canonicals
    assert "Machine Learning" in canonicals
    assert "Python" in canonicals

    assert canonicals["PostgreSQL"]["matched_text"] in ["Postgre SQL", "PostgreSQL"]
    assert canonicals["Node.js"]["matched_text"] in ["Node", "Node.js"]
    assert canonicals["Machine Learning"]["matched_text"] in ["ML", "Machine Learning"]


def test_false_positive_prevention_c_and_substrings():
    """Test that single-letter 'C' is NOT falsely matched inside unrelated words (Company, Cat, Co-op)."""
    normalizer = SkillNormalizer()
    extractor = SkillExtractor(normalizer)

    # Text containing words starting with C or containing C, but NOT the C programming language
    false_positive_text = (
        "The Company organized a community event for cat lovers in Chicago. "
        "He served as a member of Committee C during the conference session."
    )
    extracted = extractor.extract_skills(false_positive_text)
    canonicals = [s["canonical_name"] for s in extracted]

    # 'C' programming language MUST NOT be extracted
    assert "C" not in canonicals

    # However, when C appears with programming context, it should match:
    valid_c_text = "Proficient in C programming language and embedded systems software developer."
    valid_extracted = extractor.extract_skills(valid_c_text)
    valid_canonicals = [s["canonical_name"] for s in valid_extracted]
    assert "C" in valid_canonicals


# ---------------------------------------------------------------------------
# 3. END-TO-END RESUME API ROUTES TESTS
# ---------------------------------------------------------------------------

def test_api_upload_resume_and_get_skills_and_delete(client, auth_headers, second_user_headers, tmp_path):
    """Test full API lifecycle: POST upload, GET skills, ownership enforcement, and DELETE."""
    # Create sample PDF file in memory
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (50, 72),
        "Jane Developer\nFull Stack Engineer\nSkills: JavaScript, TypeScript, React, Docker, Python\nExperience building web applications.",
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    # 1. Upload resume
    upload_res = client.post(
        "/api/resumes/upload",
        headers=auth_headers,
        files={"file": ("resume_jane.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 201
    upload_data = upload_res.json()
    resume_id = upload_data["id"]
    assert upload_data["filename"] == "resume_jane.pdf"
    assert upload_data["extracted_skills_count"] >= 4

    skills_names = [s["canonical_name"] for s in upload_data["skills"]]
    assert "JavaScript" in skills_names
    assert "TypeScript" in skills_names
    assert "React" in skills_names
    assert "Docker" in skills_names

    # 2. GET /api/resumes/{id}/skills (Owner)
    skills_res = client.get(f"/api/resumes/{resume_id}/skills", headers=auth_headers)
    assert skills_res.status_code == 200
    skills_data = skills_res.json()
    assert skills_data["resume_id"] == resume_id
    assert skills_data["total_skills"] >= 4

    # 3. GET /api/resumes/{id}/skills (Non-owner -> 403 Forbidden)
    forbidden_get = client.get(f"/api/resumes/{resume_id}/skills", headers=second_user_headers)
    assert forbidden_get.status_code == 403
    assert "permission" in forbidden_get.json()["detail"].lower()

    # 4. DELETE /api/resumes/{id} (Non-owner -> 403 Forbidden)
    forbidden_del = client.delete(f"/api/resumes/{resume_id}", headers=second_user_headers)
    assert forbidden_del.status_code == 403

    # 5. DELETE /api/resumes/{id} (Owner -> 200 OK)
    delete_res = client.delete(f"/api/resumes/{resume_id}", headers=auth_headers)
    assert delete_res.status_code == 200
    assert delete_res.json()["status"] == "success"

    # 6. Verify resume is now deleted
    skills_after_del = client.get(f"/api/resumes/{resume_id}/skills", headers=auth_headers)
    assert skills_after_del.status_code == 404


# ---------------------------------------------------------------------------
# 4. ACTIVE RESUME & HISTORY PERSISTENCE TESTS
# ---------------------------------------------------------------------------

def _make_pdf_bytes(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_get_active_resume_with_no_resumes_returns_clean_empty(client, auth_headers):
    """Verify GET /api/resumes/active with no resumes returns 200 clean empty response (not 500)."""
    res = client.get("/api/resumes/active", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["has_active_resume"] is False
    assert data["resume"] is None
    assert "no resume uploaded yet" in data["message"].lower()


def test_uploading_second_resume_deactivates_first_and_retains_history(client, auth_headers):
    """Verify uploading a second resume marks it active, deactivates the first, and retains history & skills."""
    pdf_a = _make_pdf_bytes(
        "Candidate A\nBackend Engineer\nSkills: Python, FastAPI, PostgreSQL\n5 years building scalable backend systems."
    )
    pdf_b = _make_pdf_bytes(
        "Candidate B\nFrontend & DevOps Engineer\nSkills: React, TypeScript, Docker, Kubernetes\n4 years frontend architecture."
    )

    # 1. Upload Resume A
    res_a = client.post(
        "/api/resumes/upload",
        headers=auth_headers,
        files={"file": ("resume_a.pdf", pdf_a, "application/pdf")},
    )
    assert res_a.status_code == 201
    data_a = res_a.json()
    id_a = data_a["id"]
    assert data_a["is_active"] is True
    assert data_a["replaced_previous"] is False

    # 2. Upload Resume B (replaces A as active)
    res_b = client.post(
        "/api/resumes/upload",
        headers=auth_headers,
        files={"file": ("resume_b.pdf", pdf_b, "application/pdf")},
    )
    assert res_b.status_code == 201
    data_b = res_b.json()
    id_b = data_b["id"]
    assert data_b["is_active"] is True
    assert data_b["replaced_previous"] is True

    # 3. Verify GET /api/resumes lists both resumes with B active and A inactive
    list_res = client.get("/api/resumes", headers=auth_headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total_count"] == 2
    by_id = {item["id"]: item for item in list_data["resumes"]}
    assert by_id[id_b]["is_active"] is True
    assert by_id[id_a]["is_active"] is False

    # 4. Verify Resume A's extracted skills are still intact and queryable by its own resume_id
    skills_a = client.get(f"/api/resumes/{id_a}/skills", headers=auth_headers)
    assert skills_a.status_code == 200
    assert skills_a.json()["is_active"] is False
    names_a = [s["canonical_name"] for s in skills_a.json()["skills"]]
    assert "Python" in names_a
    assert "FastAPI" in names_a


def test_get_active_resume_returns_right_one(client, auth_headers):
    """Verify GET /api/resumes/active always returns the latest active resume."""
    pdf_1 = _make_pdf_bytes(
        "First Resume\nSoftware Engineer\nSkills: Python, Django, SQL\nExperience in web development."
    )
    pdf_2 = _make_pdf_bytes(
        "Second Resume\nCloud Engineer\nSkills: Docker, Kubernetes, Terraform, Linux\nExperience in cloud infrastructure."
    )

    client.post(
        "/api/resumes/upload",
        headers=auth_headers,
        files={"file": ("first_resume.pdf", pdf_1, "application/pdf")},
    )
    res_2 = client.post(
        "/api/resumes/upload",
        headers=auth_headers,
        files={"file": ("second_resume.pdf", pdf_2, "application/pdf")},
    )
    id_2 = res_2.json()["id"]

    active_res = client.get("/api/resumes/active", headers=auth_headers)
    assert active_res.status_code == 200
    active_data = active_res.json()
    assert active_data["has_active_resume"] is True
    assert active_data["resume"]["id"] == id_2
    assert active_data["resume"]["filename"] == "second_resume.pdf"
    assert active_data["resume"]["is_active"] is True
    skill_names = [s["canonical_name"] for s in active_data["resume"]["skills"]]
    assert "Docker" in skill_names
    assert "Kubernetes" in skill_names


def test_active_resume_and_history_ownership_isolation(client, auth_headers, second_user_headers):
    """Verify strict ownership isolation between two users for active resume and resume list."""
    pdf_user1 = _make_pdf_bytes(
        "User One Resume\nData Scientist\nSkills: Python, Machine Learning, Pandas\nWorked on predictive models."
    )
    upload_1 = client.post(
        "/api/resumes/upload",
        headers=auth_headers,
        files={"file": ("user1_resume.pdf", pdf_user1, "application/pdf")},
    )
    assert upload_1.status_code == 201
    user1_resume_id = upload_1.json()["id"]

    # User 2 has uploaded nothing -> active should be empty and list should be empty
    u2_active = client.get("/api/resumes/active", headers=second_user_headers)
    assert u2_active.status_code == 200
    assert u2_active.json()["has_active_resume"] is False

    u2_list = client.get("/api/resumes", headers=second_user_headers)
    assert u2_list.status_code == 200
    assert u2_list.json()["total_count"] == 0

    # User 2 cannot activate User 1's resume
    forbidden_activate = client.post(
        f"/api/resumes/{user1_resume_id}/activate",
        headers=second_user_headers,
    )
    assert forbidden_activate.status_code == 403

    # User 2 uploads their own resume -> does not affect User 1's active resume
    pdf_user2 = _make_pdf_bytes(
        "User Two Resume\nFrontend Developer\nSkills: JavaScript, React, TypeScript\nWorked on UI components."
    )
    upload_2 = client.post(
        "/api/resumes/upload",
        headers=second_user_headers,
        files={"file": ("user2_resume.pdf", pdf_user2, "application/pdf")},
    )
    assert upload_2.status_code == 201
    user2_resume_id = upload_2.json()["id"]

    u1_active_after = client.get("/api/resumes/active", headers=auth_headers)
    assert u1_active_after.json()["resume"]["id"] == user1_resume_id

    u2_active_after = client.get("/api/resumes/active", headers=second_user_headers)
    assert u2_active_after.json()["resume"]["id"] == user2_resume_id

