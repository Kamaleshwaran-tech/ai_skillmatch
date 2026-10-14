"""Resume repository for database operations on Resumes and ExtractedSkills."""

import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Resume, ExtractedSkill, SkillGapAnalysis


class ResumeRepository:
    """Repository handling Resume, active state, history, and ExtractedSkill persistence."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, resume_id: int) -> Optional[Resume]:
        """Fetch a resume by ID."""
        return self.db.get(Resume, resume_id)

    def get_active_resume(self, user_id: int) -> Optional[Resume]:
        """Fetch the current user's active resume."""
        stmt = (
            select(Resume)
            .where(Resume.user_id == user_id, Resume.is_active == True)  # noqa: E712
            .order_by(Resume.created_at.desc(), Resume.id.desc())
        )
        return self.db.scalars(stmt).first()

    def get_user_resumes(self, user_id: int) -> List[Resume]:
        """Fetch all resumes (active + past) belonging to a user ordered by newest first."""
        stmt = (
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc(), Resume.id.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_latest_analysis_for_resume(self, resume_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Fetch the most recent persisted skill gap analysis for a specific resume."""
        stmt = (
            select(SkillGapAnalysis)
            .where(SkillGapAnalysis.resume_id == resume_id, SkillGapAnalysis.user_id == user_id)
            .order_by(SkillGapAnalysis.created_at.desc(), SkillGapAnalysis.id.desc())
        )
        analysis = self.db.scalars(stmt).first()
        if analysis and analysis.results_json:
            try:
                data = json.loads(analysis.results_json)
                data["analysis_id"] = analysis.id
                return data
            except (ValueError, TypeError):
                return None
        return None

    def create_resume_with_skills(
        self,
        user_id: int,
        filename: str,
        file_path: str,
        file_type: str,
        file_size_bytes: int,
        raw_text: str,
        sections: List[dict],
        extracted_skills: List[dict],
    ) -> Resume:
        """Create a new active resume and deactivate any previous resumes for this user.
        
        Previous resumes and their extracted skills are retained in history.
        """
        # Deactivate any currently active resumes for this user
        existing_active = list(
            self.db.scalars(
                select(Resume).where(Resume.user_id == user_id, Resume.is_active == True)  # noqa: E712
            ).all()
        )
        replaced_previous = len(existing_active) > 0
        for prev in existing_active:
            prev.is_active = False

        resume = Resume(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            raw_text=raw_text,
            parsed_json=json.dumps({"sections": sections}),
            is_active=True,
        )
        self.db.add(resume)
        self.db.flush()  # Populates resume.id

        for sk in extracted_skills:
            db_skill = ExtractedSkill(
                resume_id=resume.id,
                skill_name=sk.get("matched_text", sk["canonical_name"]),
                canonical_name=sk["canonical_name"],
                category=sk.get("category"),
                confidence_score=sk.get("confidence", 1.0),
                years_experience=sk.get("years_experience"),
            )
            self.db.add(db_skill)

        self.db.commit()
        self.db.refresh(resume)
        resume.replaced_previous = replaced_previous
        return resume

    def activate_resume(self, resume: Resume) -> Resume:
        """Mark a specific resume as active for its owner and deactivate all others."""
        existing_active = list(
            self.db.scalars(
                select(Resume).where(
                    Resume.user_id == resume.user_id,
                    Resume.id != resume.id,
                    Resume.is_active == True,  # noqa: E712
                )
            ).all()
        )
        for prev in existing_active:
            prev.is_active = False

        resume.is_active = True
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def delete(self, resume: Resume) -> None:
        """Delete resume record and associated skills from DB.
        
        If the deleted resume was active, promote the user's most recent remaining resume if one exists.
        """
        was_active = resume.is_active
        user_id = resume.user_id
        self.db.delete(resume)
        self.db.commit()

        if was_active:
            remaining = self.get_user_resumes(user_id)
            if remaining:
                remaining[0].is_active = True
                self.db.commit()
