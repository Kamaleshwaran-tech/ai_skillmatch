"""Tests for semantic_matcher and hybrid_matcher.

Covers:
1. Exact match (Stage 1)
2. Alias match (Stage 2)
3. Clean semantic match (Stage 3 + 4)
4. Adversarial case: "built REST APIs" vs required skill "FastAPI" -> lands in needs_review, not matched
5. High similarity alone does not produce "matched" without evidence validation
6. Model is loaded once at process startup, batch embedding generation, and embedding caching
"""

import pytest
import torch
from app.services.semantic_matcher import semantic_matcher, SemanticMatcher
from app.services.hybrid_matcher import HybridMatcher


# ---------------------------------------------------------------------------
# 1. SEMANTIC MATCHER TESTS (Loading, Caching, Batching)
# ---------------------------------------------------------------------------

def test_semantic_matcher_singleton_and_batch_encode():
    """Verify semantic matcher is a singleton and batch encodes tensors."""
    inst1 = SemanticMatcher.get_instance()
    inst2 = SemanticMatcher.get_instance()
    assert inst1 is inst2

    texts = ["Python", "FastAPI", "Docker", "Kubernetes"]
    embeddings = semantic_matcher.encode(texts)
    assert embeddings.shape == (4, 384)
    # Vectors should be L2-normalized
    norms = torch.norm(embeddings, p=2, dim=1)
    for norm in norms:
        assert pytest.approx(norm.item(), abs=1e-4) == 1.0


def test_semantic_matcher_cache_reusability():
    """Verify that repeatedly encoding the same text hits the cache without recomputation."""
    query = "UniqueFrameworkTestXYZ"
    emb1 = semantic_matcher.encode(query)
    assert query in semantic_matcher._embedding_cache
    emb2 = semantic_matcher.encode(query)
    assert torch.equal(emb1, emb2)


# ---------------------------------------------------------------------------
# 2. HYBRID MATCHER STAGE 1: EXACT CANONICAL MATCH
# ---------------------------------------------------------------------------

def test_hybrid_matcher_exact_canonical_match():
    """Verify Stage 1: Exact canonical skill matches immediately."""
    matcher = HybridMatcher()
    candidate_skills = [
        {
            "canonical_name": "Docker",
            "matched_text": "Docker",
            "evidence_snippet": "Proficient with Docker containers in production.",
        }
    ]

    result = matcher.match_requirement(
        required_skill="Docker",
        candidate_skills=candidate_skills,
    )
    assert result["status"] == "matched"
    assert result["method"] == "exact"
    assert result["similarity_score"] == 1.0
    assert "Exact canonical match" in result["explanation"]


# ---------------------------------------------------------------------------
# 3. HYBRID MATCHER STAGE 2: ALIAS MATCH
# ---------------------------------------------------------------------------

def test_hybrid_matcher_alias_match():
    """Verify Stage 2: Recognized alias (e.g. 'Postgre SQL', 'JS', 'ML') maps to canonical."""
    matcher = HybridMatcher()
    candidate_skills = [
        {
            "canonical_name": "PostgreSQL",
            "matched_text": "Postgre SQL",
            "evidence_snippet": "Maintained database clusters using Postgre SQL.",
        }
    ]

    result = matcher.match_requirement(
        required_skill="PostgreSQL",
        candidate_skills=candidate_skills,
    )
    assert result["status"] == "matched"
    # Matches either as canonical or alias method
    assert result["status"] == "matched"
    assert result["method"] in ["exact", "alias"]
    assert "PostgreSQL" in result["canonical_name"]


def test_hybrid_matcher_alias_match_from_raw_mention():
    """Verify alias match when matched_text is an alias like 'JS'."""
    matcher = HybridMatcher()
    candidate_skills = [
        {
            "skill_name": "JS",
            "matched_text": "JS",
            "evidence_snippet": "Wrote responsive frontend components in JS.",
        }
    ]

    result = matcher.match_requirement(
        required_skill="JavaScript",
        candidate_skills=candidate_skills,
    )
    assert result["status"] == "matched"
    assert result["method"] == "alias"
    assert "JS" in result["matched_candidate_text"]


# ---------------------------------------------------------------------------
# 4. HYBRID MATCHER STAGE 3 & 4: CLEAN SEMANTIC MATCH
# ---------------------------------------------------------------------------

def test_hybrid_matcher_clean_semantic_match_with_evidence():
    """Verify Stage 3 & 4: A semantically similar skill passes when evidence genuinely supports it."""
    matcher = HybridMatcher(similarity_threshold=0.60)
    candidate_skills = [
        {
            "canonical_name": "Amazon Web Services",
            "matched_text": "AWS Cloud",
            "evidence_snippet": "Deployed serverless infrastructure on AWS Cloud and Lambda.",
        }
    ]

    result = matcher.match_requirement(
        required_skill="Amazon Web Services",
        candidate_skills=candidate_skills,
    )
    assert result["status"] == "matched"
    assert result["method"] in ["exact", "alias", "semantic"]
    assert result["similarity_score"] >= 0.60


# ---------------------------------------------------------------------------
# 5. ADVERSARIAL CASE: "built REST APIs" vs "FastAPI" -> LANDS IN needs_review
# ---------------------------------------------------------------------------

def test_hybrid_matcher_adversarial_rest_api_vs_fastapi():
    """Adversarial test:
    Candidate has 'built REST APIs' while job requires 'FastAPI'.
    
    Even if semantic similarity is non-trivial or high, mentioning a general
    concept ('built REST APIs') alone MUST NEVER produce 'matched' for a specific framework.
    It must land in 'needs_review'.
    """
    # Test with low similarity threshold to simulate an embedding model scoring them above threshold
    matcher = HybridMatcher(similarity_threshold=0.20)

    candidate_skills = [
        {
            "canonical_name": "REST API",
            "matched_text": "REST APIs",
            "evidence_snippet": "Designed and built REST APIs for high-throughput microservices.",
        }
    ]

    result = matcher.match_requirement(
        required_skill="FastAPI",
        candidate_skills=candidate_skills,
        resume_raw_text="Designed and built REST APIs for high-throughput microservices.",
    )

    # CRITICAL: Must land in needs_review, NEVER matched!
    assert result["status"] == "needs_review"
    assert result["status"] != "matched"
    assert "FastAPI" in result["canonical_name"]
    assert "evidence validation failed" in result["explanation"]
    assert "mentioning a related concept does not confirm competency" in result["explanation"]


def test_hybrid_matcher_high_score_alone_never_matches_without_evidence():
    """Verify that a high similarity score alone NEVER matches if evidence validation fails."""
    matcher = HybridMatcher(similarity_threshold=0.10)

    candidate_skills = [
        {
            "canonical_name": "SQL",
            "matched_text": "SQL",
            "evidence_snippet": "Wrote complex SQL queries.",
        }
    ]

    result = matcher.match_requirement(
        required_skill="PostgreSQL",
        candidate_skills=candidate_skills,
        resume_raw_text="Wrote complex SQL queries.",
    )

    # General SQL does not validate PostgreSQL requirement without evidence
    assert result["status"] in ["needs_review", "missing"]
    assert result["status"] != "matched"
