"""Skill normalizer service mapping textual mentions and aliases to taxonomy canonical names.

Implements context-aware normalization to avoid blind substring matches (e.g. 'C', 'ML').
"""

import os
import json
import re
from typing import Dict, Any, Optional, List


class SkillNormalizer:
    """Normalizes raw skill strings to their canonical form in the taxonomy."""

    def __init__(self, taxonomy_path: Optional[str] = None):
        if taxonomy_path is None:
            # Default to backend/app/taxonomy/skills.json
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            taxonomy_path = os.path.join(base_dir, "taxonomy", "skills.json")

        self.taxonomy_path = taxonomy_path
        self.taxonomy: Dict[str, Any] = self._load_taxonomy()
        self.canonical_map: Dict[str, Dict[str, Any]] = {}
        self.alias_to_canonical: Dict[str, str] = {}
        self._build_lookup_indices()

    def _load_taxonomy(self) -> Dict[str, Any]:
        """Load skills.json taxonomy file."""
        if not os.path.exists(self.taxonomy_path):
            raise FileNotFoundError(f"Taxonomy file not found at: {self.taxonomy_path}")

        with open(self.taxonomy_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_lookup_indices(self) -> None:
        """Build rapid canonical lookup and alias index structures."""
        for skill in self.taxonomy.get("skills", []):
            canonical = skill["canonical_name"]
            self.canonical_map[canonical.lower()] = skill

            # Add canonical itself as an alias
            self.alias_to_canonical[canonical.lower()] = canonical

            for alias in skill.get("aliases", []):
                self.alias_to_canonical[alias.lower().strip()] = canonical

    def get_skill_definition(self, canonical_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve full taxonomy skill record."""
        return self.canonical_map.get(canonical_name.lower())

    def normalize(self, raw_mention: str, surrounding_text: str = "") -> Optional[Dict[str, Any]]:
        """Normalize a matched skill mention to its canonical taxonomy representation.
        
        Applies context checks for ambiguous abbreviations like 'C' and 'ML'.
        """
        clean_mention = raw_mention.strip()
        lower_mention = clean_mention.lower()

        # Direct alias lookup
        canonical = self.alias_to_canonical.get(lower_mention)
        if not canonical:
            # Try removing punctuation or extra spaces (e.g., 'Postgre SQL' -> 'postgresql')
            condensed = re.sub(r"[\s\-_.]", "", lower_mention)
            for alias, target_canonical in self.alias_to_canonical.items():
                if re.sub(r"[\s\-_.]", "", alias) == condensed:
                    canonical = target_canonical
                    break

        if not canonical:
            return None

        skill_def = self.get_skill_definition(canonical)
        if not skill_def:
            return None

        # Context-aware validation for single-character or ambiguous acronyms
        if skill_def.get("requires_context") and surrounding_text:
            context_keywords = skill_def.get("context_keywords", [])
            context_lower = surrounding_text.lower()
            # Must match at least one context keyword nearby
            has_context = any(kw in context_lower for kw in context_keywords)
            if not has_context:
                return None

        # Acronym context checking (e.g. ML = Machine Learning vs milliliter / mailing list)
        if skill_def.get("requires_context_for_acronym") and lower_mention in ["ml", "ai"]:
            if surrounding_text:
                keywords = skill_def.get("acronym_context_keywords", [])
                context_lower = surrounding_text.lower()
                has_context = any(kw in context_lower for kw in keywords)
                if not has_context:
                    return None

        return {
            "canonical_name": canonical,
            "category": skill_def.get("category", "other"),
            "original_matched_text": raw_mention,
        }
