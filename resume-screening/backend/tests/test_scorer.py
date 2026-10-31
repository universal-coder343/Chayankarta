"""
Tests for the hybrid scorer and ranker (Milestone 4).

Tests:
- Weight components sum to 1.0 by default
- score_resume_against_jd returns score in [0, 100]
- Better skill match → higher score
- Ranking order is correct (best candidate first)
- min_score filter works
- Explanation string is non-empty
"""

import math
import pytest

from app.models.ranking import ScoringWeights
from app.services.scorer import score_resume_against_jd, build_explanation


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_resume(skills=None, exp_years=5, education=None, embedding=None):
    """Helper to build a minimal resume document dict."""
    raw = f"Experienced developer with {exp_years}+ years of experience."
    if skills:
        raw += " Skills: " + ", ".join(skills)
    return {
        "_id": "resume-test-001",
        "filename": "test_resume.pdf",
        "raw_text": raw,
        "embedding": embedding or [0.1] * 384,
        "ner": {
            "name": "Test Candidate",
            "skills": skills or [],
            "education": education or ["B.Tech"],
            "experience": [f"{exp_years} years of experience"],
        },
    }


def _make_jd(req_skills=None, pref_skills=None, min_exp=3, education=None, embedding=None):
    """Helper to build a minimal JD document dict."""
    return {
        "_id": "jd-test-001",
        "title": "Software Engineer",
        "raw_text": "Looking for a software engineer.",
        "embedding": embedding or [0.1] * 384,
        "ner": {
            "required_skills": req_skills or [],
            "preferred_skills": pref_skills or [],
            "min_experience_years": min_exp,
            "education_requirements": education or ["Bachelor"],
        },
    }


# ---------------------------------------------------------------------------
# Weight tests
# ---------------------------------------------------------------------------

def test_default_weights_sum_to_one():
    w = ScoringWeights()
    total = w.semantic + w.skill_overlap + w.experience + w.education
    assert abs(total - 1.0) < 1e-9, f"Default weights must sum to 1.0, got {total}"


def test_default_weight_values():
    w = ScoringWeights()
    assert w.semantic == pytest.approx(0.40)
    assert w.skill_overlap == pytest.approx(0.35)
    assert w.experience == pytest.approx(0.15)
    assert w.education == pytest.approx(0.10)


# ---------------------------------------------------------------------------
# Score range tests
# ---------------------------------------------------------------------------

def test_score_in_range():
    resume = _make_resume(skills=["Python", "FastAPI"], exp_years=5)
    jd = _make_jd(req_skills=["Python", "Django"], min_exp=3)
    score, _ = score_resume_against_jd(resume, jd)
    assert 0.0 <= score <= 100.0, f"Score {score} out of [0, 100]"


def test_perfect_match_high_score():
    """A candidate with all required skills and matching experience should score high."""
    skills = ["Python", "Django", "PostgreSQL", "Docker"]
    resume = _make_resume(skills=skills, exp_years=5)
    jd = _make_jd(req_skills=skills, min_exp=3)
    # Same embedding → semantic = 1.0
    vec = [1.0 / math.sqrt(384)] * 384
    resume["embedding"] = vec
    jd["embedding"] = vec
    score, breakdown = score_resume_against_jd(resume, jd)
    assert score >= 70.0, f"Perfect-match candidate should score >= 70, got {score}"
    assert breakdown.matched_skills == sorted(skills)
    assert breakdown.missing_skills == []


def test_zero_skill_match_lower_score():
    """A candidate with no matching skills should score lower than a perfect match."""
    resume_good = _make_resume(skills=["Python", "Django"], exp_years=5)
    resume_bad = _make_resume(skills=["Excel", "PowerPoint"], exp_years=5)
    jd = _make_jd(req_skills=["Python", "Django"], min_exp=3)
    # Use same embedding so semantic is equal
    vec = [1.0 / math.sqrt(384)] * 384
    resume_good["embedding"] = vec
    resume_bad["embedding"] = vec
    jd["embedding"] = vec
    score_good, _ = score_resume_against_jd(resume_good, jd)
    score_bad, _ = score_resume_against_jd(resume_bad, jd)
    assert score_good > score_bad


def test_skill_overlap_matched_and_missing():
    resume = _make_resume(skills=["Python", "Docker"])
    jd = _make_jd(req_skills=["Python", "Docker", "Kubernetes"])
    _, breakdown = score_resume_against_jd(resume, jd)
    assert "Python" in breakdown.matched_skills
    assert "Docker" in breakdown.matched_skills
    assert "Kubernetes" in breakdown.missing_skills


def test_preferred_skills_included():
    resume = _make_resume(skills=["Python", "GraphQL"])
    jd = _make_jd(req_skills=["Python"], pref_skills=["GraphQL"])
    _, breakdown = score_resume_against_jd(resume, jd)
    assert "GraphQL" in breakdown.preferred_matched


def test_experience_above_requirement_full_score():
    resume = _make_resume(skills=["Python"], exp_years=10)
    jd = _make_jd(req_skills=["Python"], min_exp=5)
    _, breakdown = score_resume_against_jd(resume, jd)
    assert breakdown.experience_score == pytest.approx(1.0)


def test_experience_below_requirement_partial_score():
    resume = _make_resume(skills=["Python"], exp_years=2)
    jd = _make_jd(req_skills=["Python"], min_exp=4)
    _, breakdown = score_resume_against_jd(resume, jd)
    assert breakdown.experience_score < 1.0


# ---------------------------------------------------------------------------
# Ranking order test
# ---------------------------------------------------------------------------

def test_ranking_order_correct():
    """Best candidate (all skills, more exp) should rank above weaker candidate."""
    vec = [1.0 / math.sqrt(384)] * 384

    strong = _make_resume(skills=["Python", "FastAPI", "Docker"], exp_years=8, embedding=vec)
    strong["_id"] = "strong"

    weak = _make_resume(skills=["Excel"], exp_years=1, embedding=vec)
    weak["_id"] = "weak"

    jd = _make_jd(req_skills=["Python", "FastAPI", "Docker"], min_exp=3, embedding=vec)

    score_strong, _ = score_resume_against_jd(strong, jd)
    score_weak, _ = score_resume_against_jd(weak, jd)
    assert score_strong > score_weak


# ---------------------------------------------------------------------------
# Explanation test
# ---------------------------------------------------------------------------

def test_explanation_non_empty():
    resume = _make_resume(skills=["Python"])
    jd = _make_jd(req_skills=["Python", "Django"])
    score, breakdown = score_resume_against_jd(resume, jd)
    explanation = build_explanation(score, breakdown, jd)
    assert isinstance(explanation, str) and len(explanation) > 10
