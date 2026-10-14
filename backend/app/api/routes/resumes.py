"""Resume management routes: upload, active resume retrieval, history listing, skills extraction, and deletion."""

import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models import User, Resume
from app.core.config import settings
from app.repositories.resume_repository import ResumeRepository
from app.services.resume_parser import ResumeParserService
from app.services.skill_extractor import SkillExtractor
from app.schemas.resume import (
    ResumeUploadResponse,
    ResumeSkillsResponse,
    ResumeListResponse,
    ResumeHistoryItem,
    ActiveResumeResponse,
    ExtractedSkillOut,
    ExtractedSkillPosition,
)

router = APIRouter()
skill_extractor = SkillExtractor()


def _extract_skill_outs_for_resume(resume: Resume) -> List[ExtractedSkillOut]:
    """Build ExtractedSkillOut list from resume raw_text or persisted DB relationship."""
    skill_outs: List[ExtractedSkillOut] = []
    if resume.raw_text:
        extracted = skill_extractor.extract_skills(resume.raw_text)
        for sk in extracted:
            pos = None
            if "position" in sk:
                pos = ExtractedSkillPosition(**sk["position"])
            skill_outs.append(
                ExtractedSkillOut(
                    canonical_name=sk["canonical_name"],
                    matched_text=sk["matched_text"],
                    category=sk["category"],
                    extraction_method=sk["extraction_method"],
                    evidence_snippet=sk["evidence_snippet"],
                    confidence=sk["confidence"],
                    position=pos,
                )
            )
    else:
        for sk in resume.extracted_skills:
            skill_outs.append(
                ExtractedSkillOut(
                    id=sk.id,
                    canonical_name=sk.canonical_name or sk.skill_name,
                    matched_text=sk.skill_name,
                    category=sk.category or "other",
                    extraction_method="database_persisted",
                    evidence_snippet=f"Persisted skill: {sk.skill_name}",
                    confidence=sk.confidence_score,
                )
            )
    return skill_outs


@router.get(
    "",
    response_model=ResumeListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all resumes for the current user (active and history)",
)
def list_user_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all uploaded resumes belonging to the authenticated user (active + past) with timestamps."""
    repo = ResumeRepository(db)
    resumes = repo.get_user_resumes(current_user.id)

    items = [
        ResumeHistoryItem(
            id=r.id,
            filename=r.filename,
            file_type=r.file_type,
            file_size_bytes=r.file_size_bytes,
            is_active=r.is_active,
            extracted_skills_count=len(r.extracted_skills),
            created_at=r.created_at,
        )
        for r in resumes
    ]

    return ResumeListResponse(
        total_count=len(items),
        resumes=items,
    )


@router.get(
    "/active",
    response_model=ActiveResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the current user's active resume and its extracted skills",
)
def get_active_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the authenticated user's currently active resume, or a clean empty response if none exists."""
    repo = ResumeRepository(db)
    resume = repo.get_active_resume(current_user.id)

    if not resume:
        return ActiveResumeResponse(
            has_active_resume=False,
            message="No resume uploaded yet.",
            resume=None,
            latest_analysis=None,
        )

    skill_outs = _extract_skill_outs_for_resume(resume)
    latest_analysis = repo.get_latest_analysis_for_resume(resume.id, current_user.id)

    resume_out = ResumeUploadResponse(
        id=resume.id,
        filename=resume.filename,
        file_type=resume.file_type,
        file_size_bytes=resume.file_size_bytes,
        is_active=resume.is_active,
        replaced_previous=False,
        extracted_skills_count=len(skill_outs),
        skills=skill_outs,
        created_at=resume.created_at,
    )

    return ActiveResumeResponse(
        has_active_resume=True,
        message=f"Active resume '{resume.filename}' loaded.",
        resume=resume_out,
        latest_analysis=latest_analysis,
    )


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse a resume file (sets as active)",
)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a PDF or DOCX resume, extract text, detect skills with provenance, and mark as active."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Only PDF (.pdf) and Word (.docx) files are supported.",
        )

    # Read file contents
    content = await file.read()
    file_size = len(content)

    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Save to disk with unique filename to prevent collisions
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    saved_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    try:
        with open(saved_path, "wb") as f:
            f.write(content)

        # Parse file text and detect scanned/empty issues
        parsed_doc = ResumeParserService.parse_file(saved_path, file.filename)
        raw_text = parsed_doc["raw_text"]
        sections = parsed_doc.get("sections", [])

        # Extract skills using taxonomy regex + spaCy context
        extracted_skills = skill_extractor.extract_skills(raw_text, sections=sections)

        # Persist to database (marks new resume active and deactivates previous ones for this user)
        repo = ResumeRepository(db)
        resume = repo.create_resume_with_skills(
            user_id=current_user.id,
            filename=file.filename,
            file_path=saved_path,
            file_type=ext.replace(".", ""),
            file_size_bytes=file_size,
            raw_text=raw_text,
            sections=sections,
            extracted_skills=extracted_skills,
        )

        # Build response with provenance
        skill_outs = []
        for sk in extracted_skills:
            pos = None
            if "position" in sk:
                pos = ExtractedSkillPosition(**sk["position"])
            skill_outs.append(
                ExtractedSkillOut(
                    canonical_name=sk["canonical_name"],
                    matched_text=sk["matched_text"],
                    category=sk["category"],
                    extraction_method=sk["extraction_method"],
                    evidence_snippet=sk["evidence_snippet"],
                    confidence=sk["confidence"],
                    position=pos,
                )
            )

        return ResumeUploadResponse(
            id=resume.id,
            filename=resume.filename,
            file_type=resume.file_type,
            file_size_bytes=resume.file_size_bytes,
            is_active=resume.is_active,
            replaced_previous=getattr(resume, "replaced_previous", False),
            extracted_skills_count=len(skill_outs),
            skills=skill_outs,
            created_at=resume.created_at,
        )

    except HTTPException:
        if os.path.exists(saved_path):
            try:
                os.remove(saved_path)
            except OSError:
                pass
        raise
    except Exception as e:
        if os.path.exists(saved_path):
            try:
                os.remove(saved_path)
            except OSError:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the resume: {str(e)}",
        )


@router.post(
    "/{id}/activate",
    response_model=ActiveResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Set a historical resume as the current active resume",
)
def activate_historical_resume(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Switch the user's active resume to a specific resume from their history."""
    repo = ResumeRepository(db)
    resume = repo.get_by_id(id)

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    if resume.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to activate this resume.",
        )

    resume = repo.activate_resume(resume)
    skill_outs = _extract_skill_outs_for_resume(resume)
    latest_analysis = repo.get_latest_analysis_for_resume(resume.id, current_user.id)

    resume_out = ResumeUploadResponse(
        id=resume.id,
        filename=resume.filename,
        file_type=resume.file_type,
        file_size_bytes=resume.file_size_bytes,
        is_active=resume.is_active,
        replaced_previous=True,
        extracted_skills_count=len(skill_outs),
        skills=skill_outs,
        created_at=resume.created_at,
    )

    return ActiveResumeResponse(
        has_active_resume=True,
        message=f"Resume '{resume.filename}' is now active.",
        resume=resume_out,
        latest_analysis=latest_analysis,
    )


@router.get(
    "/{id}/skills",
    response_model=ResumeSkillsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get extracted skills for a specific resume (ownership checked)",
)
def get_resume_skills(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all skills extracted from a resume. Enforces ownership check."""
    repo = ResumeRepository(db)
    resume = repo.get_by_id(id)

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    # Ownership check
    if resume.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view skills for this resume.",
        )

    skill_outs = _extract_skill_outs_for_resume(resume)

    return ResumeSkillsResponse(
        resume_id=resume.id,
        filename=resume.filename,
        is_active=resume.is_active,
        total_skills=len(skill_outs),
        skills=skill_outs,
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a resume and associated data (ownership checked)",
)
def delete_resume(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete resume from database and remove its physical file from storage."""
    repo = ResumeRepository(db)
    resume = repo.get_by_id(id)

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    # Ownership check
    if resume.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this resume.",
        )

    file_path = resume.file_path

    # Delete database record (cascades to extracted_skills)
    repo.delete(resume)

    # Remove physical file if it exists
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"Warning: could not delete file {file_path}: {e}")

    return {
        "status": "success",
        "message": f"Resume '{resume.filename}' (ID: {id}) and associated data removed successfully.",
    }
