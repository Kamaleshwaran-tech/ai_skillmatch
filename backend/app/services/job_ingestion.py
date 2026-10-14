"""Job listing ingestion service with multi-level deduplication.

Deduplication rules:
1. Primary: Unique external listing ID (e.g. Adzuna ID).
2. Secondary: Normalized composite key: normalized_title + normalized_company + normalized_location.
"""

import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import JobListing, JobSkill
from app.services.skill_extractor import SkillExtractor


class JobIngestionService:
    """Service handling job ingestion, normalization, and deduplication."""

    def __init__(self, db: Optional[Session] = None, skill_extractor: Optional[SkillExtractor] = None):
        self.db = db
        self.skill_extractor = skill_extractor or SkillExtractor()

    @staticmethod
    def normalize_text(text: Optional[str]) -> str:
        """Normalize string: lowercase, collapse whitespace, strip punctuation."""
        if not text:
            return ""
        cleaned = re.sub(r"[^\w\s]", "", text.lower())
        return " ".join(cleaned.split())

    @classmethod
    def generate_content_fingerprint(cls, title: str, company: str, location: str) -> str:
        """Create composite content hash/fingerprint for title, company, and location."""
        norm_title = cls.normalize_text(title)
        norm_company = cls.normalize_text(company)
        norm_location = cls.normalize_text(location)
        return f"{norm_title}|{norm_company}|{norm_location}"

    @classmethod
    def deduplicate_job_stream(
        cls,
        jobs: List[Dict[str, Any]],
        existing_external_ids: Optional[set] = None,
        existing_fingerprints: Optional[set] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Deduplicate an in-memory batch of jobs against both itself and existing known entries.
        
        Returns:
            Tuple of (unique_jobs, duplicate_count)
        """
        seen_external_ids = set(existing_external_ids) if existing_external_ids else set()
        seen_fingerprints = set(existing_fingerprints) if existing_fingerprints else set()

        unique_jobs = []
        duplicate_count = 0

        for job in jobs:
            ext_id = str(job.get("id", "")).strip()
            title = job.get("title", "")
            company = job.get("company", "")
            location = job.get("location", "")
            fingerprint = cls.generate_content_fingerprint(title, company, location)

            # Rule 1: Check external ID
            if ext_id and ext_id in seen_external_ids:
                duplicate_count += 1
                continue

            # Rule 2: Check normalized title + company + location composite fingerprint
            if fingerprint and fingerprint in seen_fingerprints:
                duplicate_count += 1
                continue

            # Valid new listing
            if ext_id:
                seen_external_ids.add(ext_id)
            if fingerprint:
                seen_fingerprints.add(fingerprint)

            unique_jobs.append(job)

        return unique_jobs, duplicate_count

    def ingest_and_persist_jobs(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Deduplicate against the database and save new job listings with extracted skills."""
        if not self.db:
            raise ValueError("Database session required for persistence.")

        # Query existing external IDs
        stmt = select(JobListing.external_id).where(JobListing.external_id.isnot(None))
        existing_ids = set(self.db.scalars(stmt).all())

        # Query existing fingerprints from DB
        stmt_all = select(JobListing.title, JobListing.company, JobListing.location)
        existing_rows = self.db.execute(stmt_all).all()
        existing_fingerprints = {
            self.generate_content_fingerprint(r[0], r[1], r[2]) for r in existing_rows
        }

        unique_jobs, dup_count = self.deduplicate_job_stream(
            jobs,
            existing_external_ids=existing_ids,
            existing_fingerprints=existing_fingerprints,
        )

        persisted = []
        for j in unique_jobs:
            ext_id = str(j.get("id", "")).strip() or None
            job_record = JobListing(
                external_id=ext_id,
                title=j.get("title", "Untitled Job"),
                company=j.get("company", "Unknown Company"),
                location=j.get("location", ""),
                country=j.get("country", "us"),
                description=j.get("description", ""),
                salary_min=j.get("salary_min"),
                salary_max=j.get("salary_max"),
                url=j.get("url"),
                source=j.get("source", "adzuna"),
            )
            self.db.add(job_record)
            self.db.flush()

            # Extract skills for this job listing
            extracted = self.skill_extractor.extract_skills(
                f"{job_record.title}\n{job_record.description}"
            )
            for sk in extracted:
                job_skill = JobSkill(
                    job_listing_id=job_record.id,
                    skill_name=sk["matched_text"],
                    canonical_name=sk["canonical_name"],
                    importance_weight=sk.get("confidence", 1.0),
                    is_required=True,
                )
                self.db.add(job_skill)

            persisted.append(job_record)

        self.db.commit()
        return {
            "total_received": len(jobs),
            "unique_ingested": len(persisted),
            "duplicates_filtered": dup_count,
        }
