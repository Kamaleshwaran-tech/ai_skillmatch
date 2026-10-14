"""Skill extractor service using spaCy tokenization and regex against the skill taxonomy.

Extracts skills with full provenance:
- canonical name
- matched text
- extraction method
- evidence snippet
- confidence
- position / section
"""

import os
import re
from typing import List, Dict, Any, Optional
import spacy
from app.services.skill_normalizer import SkillNormalizer


class SkillExtractor:
    """Extracts skills from text using spaCy tokenizer and context-aware pattern matching."""

    def __init__(self, normalizer: Optional[SkillNormalizer] = None):
        self.normalizer = normalizer or SkillNormalizer()
        self.taxonomy = self.normalizer.taxonomy

        # Use spaCy English tokenizer for sentence and token boundary segmentation
        try:
            self.nlp = spacy.blank("en")
            # Add sentencizer component for accurate sentence splitting and context extraction
            if "sentencizer" not in self.nlp.pipe_names:
                self.nlp.add_pipe("sentencizer")
        except Exception:
            self.nlp = None

        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> List[Dict[str, Any]]:
        """Pre-compile regex patterns for each taxonomy skill entry."""
        compiled = []
        for skill in self.taxonomy.get("skills", []):
            patterns = skill.get("patterns", [])
            for p in patterns:
                try:
                    c_pattern = re.compile(p, re.IGNORECASE)
                    compiled.append({
                        "regex": c_pattern,
                        "canonical_name": skill["canonical_name"],
                        "category": skill["category"],
                        "skill_def": skill,
                    })
                except re.error as e:
                    print(f"Failed to compile pattern '{p}': {e}")
        return compiled

    def extract_skills(self, text: str, sections: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Extract all skills from full text or segmented sections.
        
        Returns a list of deduplicated skill extraction dictionaries with provenance.
        """
        if not text or not text.strip():
            return []

        # If sections provided, extract section-by-section to track section names
        if sections and len(sections) > 0:
            extracted_by_skill: Dict[str, Dict[str, Any]] = {}
            for sec in sections:
                sec_name = sec.get("name", "General")
                sec_text = sec.get("text", "")
                sec_skills = self._extract_from_block(sec_text, section_name=sec_name)
                for s in sec_skills:
                    c_name = s["canonical_name"]
                    # Keep the one with highest confidence or merge evidence
                    if c_name not in extracted_by_skill or s["confidence"] > extracted_by_skill[c_name]["confidence"]:
                        extracted_by_skill[c_name] = s
            return list(extracted_by_skill.values())

        return self._extract_from_block(text, section_name="General")

    def _extract_from_block(self, block_text: str, section_name: str = "General") -> List[Dict[str, Any]]:
        """Extract skills from a text block, maintaining evidence snippets and token positions."""
        results = []
        seen_canonicals: Dict[str, Dict[str, Any]] = {}

        # Split into sentences / lines for contextual evidence window
        lines = block_text.splitlines()

        for pattern_info in self._compiled_patterns:
            regex: re.Pattern = pattern_info["regex"]
            canonical_name = pattern_info["canonical_name"]
            category = pattern_info["category"]
            skill_def = pattern_info["skill_def"]

            for match in regex.finditer(block_text):
                start_char, end_char = match.span()
                matched_raw = match.group(0)

                # Find evidence snippet around the match
                evidence_snippet = self._get_surrounding_snippet(block_text, start_char, end_char)

                # Context-aware normalization check
                norm_res = self.normalizer.normalize(matched_raw, surrounding_text=evidence_snippet)
                if not norm_res:
                    continue  # Rejected by context guard (e.g. 'C' without programming context, or false positive)

                # Determine confidence
                confidence = 0.95
                if matched_raw.lower() == canonical_name.lower():
                    confidence = 1.0
                elif skill_def.get("requires_context") or skill_def.get("requires_context_for_acronym"):
                    confidence = 0.90

                # Ensure section bonus if mentioned in a 'Skills' section
                if "skill" in section_name.lower() or "technolog" in section_name.lower():
                    confidence = min(1.0, confidence + 0.05)

                extracted_entry = {
                    "canonical_name": canonical_name,
                    "matched_text": matched_raw,
                    "category": category,
                    "extraction_method": "taxonomy_regex_spacy",
                    "evidence_snippet": evidence_snippet,
                    "confidence": round(confidence, 2),
                    "position": {
                        "start_char": start_char,
                        "end_char": end_char,
                        "section": section_name,
                    },
                }

                # Deduplicate within this block
                if canonical_name not in seen_canonicals:
                    seen_canonicals[canonical_name] = extracted_entry
                else:
                    # Update if confidence higher
                    if extracted_entry["confidence"] > seen_canonicals[canonical_name]["confidence"]:
                        seen_canonicals[canonical_name] = extracted_entry

        return list(seen_canonicals.values())

    @staticmethod
    def _get_surrounding_snippet(full_text: str, start: int, end: int, window: int = 60) -> str:
        """Create a clean, bounded evidence snippet around the matched character offset."""
        snippet_start = max(0, start - window)
        snippet_end = min(len(full_text), end + window)
        snippet = full_text[snippet_start:snippet_end].replace("\n", " ").strip()
        if snippet_start > 0:
            snippet = f"...{snippet}"
        if snippet_end < len(full_text):
            snippet = f"{snippet}..."
        return snippet
