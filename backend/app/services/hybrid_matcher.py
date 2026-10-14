"""Hybrid skill matcher combining rule-based, alias, and semantic vector similarity.

Implements strict 5-stage decision order:
1. exact canonical match
2. alias match
3. semantic comparison (threshold configurable via SEMANTIC_SIMILARITY_THRESHOLD in .env)
4. evidence validation against original resume sentence / context
5. else needs_review

Rule: A high similarity score alone must never produce 'matched' without evidence validation.
"""

import re
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.skill_normalizer import SkillNormalizer
from app.services.semantic_matcher import semantic_matcher, SemanticMatcher


class HybridMatcher:
    """Evaluates candidate resume skills against target job requirements according to the 5-stage pipeline."""

    def __init__(
        self,
        normalizer: Optional[SkillNormalizer] = None,
        matcher: Optional[SemanticMatcher] = None,
        similarity_threshold: Optional[float] = None,
    ):
        self.normalizer = normalizer or SkillNormalizer()
        self.matcher = matcher or semantic_matcher
        self.threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.SEMANTIC_SIMILARITY_THRESHOLD
        )

    def validate_evidence(self, required_skill: str, candidate_text: str, evidence_sentence: str) -> bool:
        """Stage 4: Validate that candidate evidence genuinely supports the required skill.
        
        Guards against semantic over-reach:
        E.g. Candidate resume has 'built REST APIs' while job requires 'FastAPI'.
        Even if an embedding model scores them similarly, without evidence of FastAPI specifically
        or a legitimate direct framework mention, it must fail evidence validation.
        """
        if not evidence_sentence:
            return False

        clean_evidence = evidence_sentence.lower()
        clean_req = required_skill.lower()
        clean_cand = candidate_text.lower()

        # If candidate text or canonical name appears in the evidence sentence
        req_def = self.normalizer.get_skill_definition(required_skill)
        aliases = [clean_req]
        if req_def:
            aliases.extend([a.lower() for a in req_def.get("aliases", [])])

        # Check if the requirement or any of its known aliases actually appears in evidence
        has_direct_mention = any(
            re.search(r"\b" + re.escape(alias) + r"\b", clean_evidence)
            for alias in aliases
        )
        if has_direct_mention:
            return True

        # Check if candidate text is mentioned in evidence
        cand_in_evidence = re.search(r"\b" + re.escape(clean_cand) + r"\b", clean_evidence) is not None

        # If candidate text is only a general/related concept (e.g. 'REST APIs') and required
        # is a specific tool/framework ('FastAPI'), evidence validation FAILS.
        if cand_in_evidence:
            # If the candidate text itself is what was matched semantically, verify equivalence
            # Specific framework check: general conceptual phrase cannot validate a specific tech stack requirement
            if clean_cand in ["rest api", "rest apis", "restful api", "apis", "web services", "backend"] and clean_req in ["fastapi", "django", "flask", "express.js", "spring boot"]:
                return False
            # Check canonical equality
            cand_norm = self.normalizer.normalize(candidate_text, evidence_sentence)
            if cand_norm and cand_norm["canonical_name"].lower() == clean_req:
                return True

        return False

    def match_requirement(
        self,
        required_skill: str,
        candidate_skills: List[Dict[str, Any]],
        resume_raw_text: str = "",
    ) -> Dict[str, Any]:
        """Evaluate a single required skill against the candidate's extracted skills and raw resume text.
        
        Exact Decision Order:
        1. Exact canonical match
        2. Alias match
        3. Semantic comparison (similarity >= threshold)
        4. Evidence validation against original resume sentence
        5. Else needs_review (or missing)
        """
        req_clean = required_skill.strip()
        req_norm = self.normalizer.normalize(req_clean)
        canonical_req = req_norm["canonical_name"] if req_norm else req_clean

        # --- Stage 1: Exact canonical match ---
        for cand in candidate_skills:
            cand_canonical = cand.get("canonical_name", cand.get("skill_name", "")).strip()
            if cand_canonical.lower() == canonical_req.lower():
                return {
                    "skill": required_skill,
                    "canonical_name": canonical_req,
                    "status": "matched",
                    "method": "exact",
                    "similarity_score": 1.0,
                    "matched_candidate_text": cand.get("matched_text", cand_canonical),
                    "evidence_text": cand.get("evidence_snippet", f"Exact match for {canonical_req}"),
                    "explanation": f"Exact canonical match verified for '{canonical_req}'.",
                }

        # --- Stage 2: Alias match ---
        req_def = self.normalizer.get_skill_definition(canonical_req)
        known_aliases = [a.lower() for a in req_def.get("aliases", [])] if req_def else []

        for cand in candidate_skills:
            cand_raw = cand.get("matched_text", cand.get("skill_name", "")).strip().lower()
            cand_canonical = cand.get("canonical_name", "").strip().lower()

            if cand_raw in known_aliases or cand_canonical in known_aliases:
                return {
                    "skill": required_skill,
                    "canonical_name": canonical_req,
                    "status": "matched",
                    "method": "alias",
                    "similarity_score": 0.98,
                    "matched_candidate_text": cand.get("matched_text", cand_raw),
                    "evidence_text": cand.get("evidence_snippet", f"Alias match in candidate profile: {cand_raw}"),
                    "explanation": f"Recognized alias '{cand_raw}' directly maps to required skill '{canonical_req}'.",
                }

        # --- Stage 3: Semantic comparison ---
        # Find best candidate by semantic similarity
        best_cand = None
        highest_sim = -1.0

        cand_texts = [
            c.get("matched_text") or c.get("canonical_name") or c.get("skill_name")
            for c in candidate_skills
        ]

        if cand_texts:
            similarity_tensor = self.matcher.batch_compare(cand_texts, [canonical_req])
            # similarity_tensor shape: [len(cand_texts), 1]
            for i, cand in enumerate(candidate_skills):
                sim_score = round(float(similarity_tensor[i][0].item()), 4)
                if sim_score > highest_sim:
                    highest_sim = sim_score
                    best_cand = (cand, sim_score)

        if best_cand and highest_sim >= self.threshold:
            cand_obj, sim_score = best_cand
            cand_matched_text = cand_obj.get("matched_text", "")
            evidence_snippet = cand_obj.get("evidence_snippet", "")

            # --- Stage 4: Evidence validation against the original resume sentence ---
            is_valid_evidence = self.validate_evidence(
                required_skill=canonical_req,
                candidate_text=cand_matched_text,
                evidence_sentence=evidence_snippet or resume_raw_text,
            )

            if is_valid_evidence:
                return {
                    "skill": required_skill,
                    "canonical_name": canonical_req,
                    "status": "matched",
                    "method": "semantic",
                    "similarity_score": sim_score,
                    "matched_candidate_text": cand_matched_text,
                    "evidence_text": evidence_snippet,
                    "explanation": (
                        f"Semantic similarity score ({sim_score:.2f} >= threshold {self.threshold:.2f}) "
                        f"between '{cand_matched_text}' and '{canonical_req}' confirmed by evidence validation."
                    ),
                }
            else:
                # Rule: High similarity alone must never produce "matched" without evidence validation
                return {
                    "skill": required_skill,
                    "canonical_name": canonical_req,
                    "status": "needs_review",
                    "method": "semantic",
                    "similarity_score": sim_score,
                    "matched_candidate_text": cand_matched_text,
                    "evidence_text": evidence_snippet,
                    "explanation": (
                        f"Semantic similarity score ({sim_score:.2f}) met threshold ({self.threshold:.2f}) "
                        f"for candidate mention '{cand_matched_text}', but evidence validation failed: "
                        f"mentioning a related concept does not confirm competency in required skill '{canonical_req}'."
                    ),
                }

        # --- Stage 5: Else needs_review / missing ---
        if best_cand and highest_sim > 0.45:
            cand_obj, sim_score = best_cand
            cand_matched_text = cand_obj.get("matched_text", "")
            return {
                "skill": required_skill,
                "canonical_name": canonical_req,
                "status": "needs_review",
                "method": "semantic",
                "similarity_score": sim_score,
                "matched_candidate_text": cand_matched_text,
                "evidence_text": cand_obj.get("evidence_snippet", ""),
                "explanation": (
                    f"Candidate possesses related skill '{cand_matched_text}' with moderate similarity "
                    f"({sim_score:.2f} < threshold {self.threshold:.2f}). Flagged for manual review."
                ),
            }

        return {
            "skill": required_skill,
            "canonical_name": canonical_req,
            "status": "missing",
            "method": "none",
            "similarity_score": 0.0,
            "matched_candidate_text": None,
            "evidence_text": "",
            "explanation": f"No direct, alias, or semantic match for required skill '{canonical_req}' was found in candidate profile.",
        }

    def match_all_requirements(
        self,
        required_skills: List[str],
        candidate_skills: List[Dict[str, Any]],
        resume_raw_text: str = "",
    ) -> List[Dict[str, Any]]:
        """Batch evaluate all required skills against the candidate's profile."""
        return [
            self.match_requirement(req, candidate_skills, resume_raw_text)
            for req in required_skills
        ]
