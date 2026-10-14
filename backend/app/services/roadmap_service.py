"""Learning Roadmap Service.

Consumes the existing SkillGapService (Task 6) and MarketDemandService (Task 4) output
to produce a deterministic, market-driven learning sequence for a target role.

Key invariants:
1. Does NOT recompute skill matching logic — delegates directly to SkillGapService.
2. Orders missing + needs_review skills deterministically by real market demand_percentage
   descending (highest market opportunity first), never by LLM guess.
3. Calls an LLM per skill with a tightly scoped prompt asking only for:
   (a) a short plain-language explanation of what the skill is and why it matters for the role,
   (b) general resource types to learn it (official docs, reputable free platform by name,
       practice-project idea) — explicitly prohibiting fabricated course titles, URLs,
       instructor names, certifications, or time estimates.
4. Resilient fallback: if the LLM call fails, times out, or is unconfigured, returns the
   ordered skill list with real demand data and sets explanation="AI explanation unavailable"
   (ai_explanation_available=False) without blocking the response or fabricating explanations.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.skill_gap_service import SkillGapService

logger = logging.getLogger(__name__)

AI_EXPLANATION_UNAVAILABLE_NOTE = "AI explanation unavailable"
RESOURCE_DISCLAIMER_TEXT = (
    "Resource suggestions are general learning categories and platforms, "
    "not a specific verified course list or live URL directory."
)


class RoadmapService:
    """Generates a deterministic, market-demand-ordered learning roadmap for a target role."""

    def __init__(
        self,
        db: Session,
        skill_gap_service: Optional[SkillGapService] = None,
        llm_client: Optional[Callable[[str, str], Dict[str, Any]]] = None,
    ):
        self.db = db
        self.skill_gap_service = skill_gap_service or SkillGapService(db=db)
        self.llm_client = llm_client

    @staticmethod
    def order_skills_by_demand(
        missing_skills: List[Dict[str, Any]],
        needs_review_skills: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Order missing and needs_review skills deterministically by real market demand %.

        Sorting hierarchy:
        1. demand_percentage descending (highest market opportunity first)
        2. matching_listings_count descending
        3. status ('missing' before 'needs_review' on exact ties)
        4. skill name alphabetically (deterministic tie-breaker)
        """
        combined: List[Dict[str, Any]] = []

        for item in missing_skills:
            entry = dict(item)
            entry["status"] = "missing"
            combined.append(entry)

        for item in needs_review_skills:
            entry = dict(item)
            entry["status"] = "needs_review"
            combined.append(entry)

        combined.sort(
            key=lambda x: (
                -float(x.get("demand_percentage", 0.0)),
                -int(x.get("matching_listings_count", 0)),
                0 if x.get("status") == "missing" else 1,
                str(x.get("skill", "")).lower(),
            )
        )
        return combined

    @staticmethod
    def build_skill_prompt(skill_name: str, target_role: str) -> str:
        """Build a tightly scoped prompt for the LLM with strict anti-hallucination rules."""
        role_label = target_role.strip() if target_role and target_role.strip() else "Software Engineer"
        return (
            f"You are a technical career advisor. For the skill '{skill_name}' in the context of "
            f"the target role '{role_label}', respond with ONLY a valid JSON object containing:\n"
            f'  "explanation": A short plain-language explanation (2-3 sentences) of what '
            f"'{skill_name}' is and why it matters for a '{role_label}' role.\n"
            f'  "resource_suggestions": A JSON array of 3 general learning resource types '
            f"(1: official documentation type, 2: a reputable free learning platform by name "
            f"such as freeCodeCamp, MDN, roadmap.sh, Coursera, or edX, 3: a practice-project idea).\n"
            f'  "practice_project_idea": A concise 1-sentence practice project idea to apply {skill_name}.\n\n'
            f"STRICT RULES:\n"
            f"- DO NOT fabricate or invent specific course titles, URLs, instructor names, "
            f"certifications, or time estimates that you cannot verify.\n"
            f"- Provide only general resource types and well-known platform names.\n"
            f"- Output raw JSON only, with no markdown code fences."
        )

    def _request_llm_completion(self, prompt: str) -> str:
        """Execute an HTTP request to the configured LLM provider with a strict timeout."""
        gemini_key = settings.GEMINI_API_KEY or (
            settings.LLM_API_KEY if "gemini" in settings.LLM_MODEL_NAME.lower() else ""
        )
        openai_key = settings.OPENAI_API_KEY or (
            settings.LLM_API_KEY if "gemini" not in settings.LLM_MODEL_NAME.lower() else ""
        )
        timeout = settings.LLM_TIMEOUT_SECONDS

        if gemini_key:
            model = settings.LLM_MODEL_NAME or "gemini-2.0-flash"
            url = (
                settings.LLM_API_URL
                or f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json",
                },
            }
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, params={"key": gemini_key}, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

        if openai_key or settings.LLM_API_URL:
            url = settings.LLM_API_URL or "https://api.openai.com/v1/chat/completions"
            headers = {"Content-Type": "application/json"}
            if openai_key:
                headers["Authorization"] = f"Bearer {openai_key}"
            payload = {
                "model": settings.LLM_MODEL_NAME or "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]

        raise RuntimeError("No LLM API key or endpoint configured.")

    @staticmethod
    def _parse_llm_json(raw_text: str) -> Dict[str, Any]:
        """Parse and validate the JSON response from the LLM."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError("LLM response is not a JSON object.")

        explanation = parsed.get("explanation")
        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError("LLM response missing non-empty 'explanation'.")

        raw_resources = parsed.get("resource_suggestions", [])
        if isinstance(raw_resources, list):
            resource_suggestions = [str(r).strip() for r in raw_resources if str(r).strip()]
        else:
            resource_suggestions = []

        project_idea = parsed.get("practice_project_idea")
        if project_idea is not None:
            project_idea = str(project_idea).strip() or None

        return {
            "ai_explanation_available": True,
            "explanation": explanation.strip(),
            "resource_suggestions": resource_suggestions,
            "practice_project_idea": project_idea,
        }

    def generate_skill_guidance(self, skill_name: str, target_role: str) -> Dict[str, Any]:
        """Call the LLM for a single skill or return a clean 'AI explanation unavailable' fallback."""
        try:
            if self.llm_client is not None:
                res = self.llm_client(skill_name, target_role)
                explanation = res.get("explanation") if isinstance(res, dict) else None
                if not isinstance(explanation, str) or not explanation.strip():
                    raise ValueError("Injected llm_client returned empty explanation.")
                return {
                    "ai_explanation_available": True,
                    "explanation": explanation.strip(),
                    "resource_suggestions": list(res.get("resource_suggestions", [])),
                    "practice_project_idea": res.get("practice_project_idea"),
                }

            prompt = self.build_skill_prompt(skill_name=skill_name, target_role=target_role)
            raw_output = self._request_llm_completion(prompt)
            return self._parse_llm_json(raw_output)
        except Exception as exc:
            logger.warning(
                "LLM explanation unavailable for skill '%s' (role='%s'): %s",
                skill_name,
                target_role,
                exc,
            )
            return {
                "ai_explanation_available": False,
                "explanation": AI_EXPLANATION_UNAVAILABLE_NOTE,
                "resource_suggestions": [],
                "practice_project_idea": None,
            }

    def generate_roadmap(
        self,
        user_id: int,
        resume_id: int,
        target_role: str,
        target_location: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Generate an ordered learning roadmap by consuming SkillGapService output."""
        # 1. Reuse existing SkillGapService (includes ownership check on resume_id)
        gap_analysis = self.skill_gap_service.analyze_resume_gap(
            user_id=user_id,
            resume_id=resume_id,
            target_role=target_role,
            target_location=target_location,
            limit=limit,
        )

        matched_skills = gap_analysis.get("matched_skills", [])
        missing_skills = gap_analysis.get("missing_skills", [])
        needs_review_skills = gap_analysis.get("needs_review_skills", [])
        summary = gap_analysis.get("summary", {})
        overall_match_pct = float(summary.get("overall_match_percentage", 0.0))

        # 2. Deterministically order missing + needs_review skills by real demand % descending
        ordered_gap_skills = self.order_skills_by_demand(
            missing_skills=missing_skills,
            needs_review_skills=needs_review_skills,
        )

        # 3. Enrich each ordered step with LLM explanation & general resource suggestions (with safe fallback)
        roadmap_steps: List[Dict[str, Any]] = []
        for idx, item in enumerate(ordered_gap_skills, start=1):
            skill_name = item["skill"]
            llm_guidance = self.generate_skill_guidance(
                skill_name=skill_name,
                target_role=target_role,
            )

            roadmap_steps.append(
                {
                    "step_number": idx,
                    "skill": skill_name,
                    "canonical_name": item.get("canonical_name", skill_name),
                    "status": item["status"],
                    "demand_percentage": float(item.get("demand_percentage", 0.0)),
                    "matching_listings_count": int(item.get("matching_listings_count", 0)),
                    "total_listings_analyzed": int(
                        item.get("total_listings_analyzed", gap_analysis.get("total_listings_analyzed", 0))
                    ),
                    "priority": item.get("priority", "Low"),
                    "ai_explanation_available": llm_guidance["ai_explanation_available"],
                    "explanation": llm_guidance["explanation"],
                    "resource_suggestions": llm_guidance["resource_suggestions"],
                    "practice_project_idea": llm_guidance["practice_project_idea"],
                }
            )

        return {
            "resume_id": resume_id,
            "target_role": target_role,
            "target_location": target_location,
            "overall_match_percentage": overall_match_pct,
            "total_listings_analyzed": int(gap_analysis.get("total_listings_analyzed", 0)),
            "data_source": gap_analysis.get("data_source", "Adzuna Sample Fixtures"),
            "is_sample_data": bool(gap_analysis.get("is_sample_data", True)),
            "banner_message": gap_analysis.get("banner_message"),
            "priority_thresholds": gap_analysis.get(
                "priority_thresholds",
                {
                    "high_threshold": ">= 70.0%",
                    "medium_threshold": "40.0% - 69.9%",
                    "low_threshold": "< 40.0%",
                    "note": "Project-defined priority thresholds, not industry standards",
                },
            ),
            "resource_disclaimer": RESOURCE_DISCLAIMER_TEXT,
            "roadmap_steps": roadmap_steps,
            "matched_skills": matched_skills,
            "generated_at": datetime.now(timezone.utc),
        }
