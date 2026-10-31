"""
Hybrid resume-to-JD scoring service — Milestone 4.

Combines four complementary signals into one composite score:

1. **Semantic similarity** (cosine, 40%)  — holistic text relevance
2. **Skill overlap** (required + preferred, 35%) — hard requirement match
3. **Experience match** (capped ratio, 15%)  — years-of-experience requirement
4. **Education match** (level comparison, 10%)  — degree requirement

Default weights: {semantic: 0.40, skill: 0.35, experience: 0.15, education: 0.10}
(configurable via settings / RankRequest.weights)

Final score is normalised to **0–100** (not 0–1) for display.

Usage
-----
>>> from .scorer import score_resume_against_jd
>>> overall_100, breakdown = score_resume_against_jd(resume_doc, jd_doc)
"""

import logging
import re
from typing import Optional

from ..models.job_description import JobDescriptionNER
from ..models.ranking import ScoreBreakdown, ScoringWeights
from ..models.resume import ResumeNER
from .embedder import cosine_similarity, embed_text

logger = logging.getLogger(__name__)

# Default weights (applied when caller doesn't provide weights)
_DEFAULT_WEIGHTS = ScoringWeights()

# Education keyword → canonical level (higher = higher degree)
_EDUCATION_LEVEL: dict[str, int] = {
    "high school": 1, "ged": 1,
    "diploma": 2, "associate": 2,
    "bachelor": 3, "b.tech": 3, "b.e": 3, "b.sc": 3, "b.s": 3,
    "b.a": 3, "bca": 3, "bba": 3, "b.com": 3,
    "master": 4, "m.tech": 4, "m.e": 4, "m.sc": 4, "m.s": 4,
    "m.a": 4, "mca": 4, "mba": 4, "m.com": 4,
    "phd": 5, "ph.d": 5, "doctorate": 5,
}

_YEAR_PATTERN = re.compile(r"(\d+)\+?\s*(?:years?|yrs?)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_resume_against_jd(
    resume_doc: dict,
    jd_doc: dict,
    weights: Optional[ScoringWeights] = None,
) -> tuple[float, ScoreBreakdown]:
    """
    Compute a composite score for one resume against one job description.

    Args:
        resume_doc : Raw MongoDB document for the resume.
        jd_doc     : Raw MongoDB document for the job description.
        weights    : Optional weight overrides. Uses defaults if None.

    Returns:
        Tuple of (final_score_0_to_100, ScoreBreakdown).
    """
    w = weights or _DEFAULT_WEIGHTS

    # --- 1. Semantic score ---
    sem_score = _semantic_score(resume_doc, jd_doc)

    # --- 2. Skill overlap (required + preferred) ---
    skill_score, matched, missing, pref_matched = _skill_overlap_score(resume_doc, jd_doc)

    # --- 3. Experience match ---
    exp_score = _experience_score(resume_doc, jd_doc)

    # --- 4. Education match ---
    edu_score = _education_score(resume_doc, jd_doc)

    # --- Composite (0–1) ---
    overall_01 = (
        w.semantic * sem_score
        + w.skill_overlap * skill_score
        + w.experience * exp_score
        + w.education * edu_score
    )
    overall_01 = max(0.0, min(1.0, overall_01))

    # Normalise to 0–100
    final_score = round(overall_01 * 100, 2)

    breakdown = ScoreBreakdown(
        semantic_score=round(sem_score, 4),
        skill_overlap_score=round(skill_score, 4),
        experience_score=round(exp_score, 4),
        education_score=round(edu_score, 4),
        matched_skills=matched,
        missing_skills=missing,
        preferred_matched=pref_matched,
    )

    logger.debug(
        "Resume '%s' vs JD '%s': final=%.1f (sem=%.3f, skill=%.3f, exp=%.3f, edu=%.3f)",
        resume_doc.get("filename", "?"),
        jd_doc.get("title", "?"),
        final_score,
        sem_score,
        skill_score,
        exp_score,
        edu_score,
    )

    return final_score, breakdown


def build_explanation(
    final_score: float,
    breakdown: ScoreBreakdown,
    jd_doc: dict,
) -> str:
    """
    Generate a short human-readable explanation of a candidate's score.

    Args:
        final_score : 0–100 composite score.
        breakdown   : ScoreBreakdown with component scores.
        jd_doc      : JD document (for context).

    Returns:
        A 1–2 sentence explanation string.
    """
    parts: list[str] = []

    # Skill comment
    total_req = len(breakdown.matched_skills) + len(breakdown.missing_skills)
    if total_req > 0:
        matched_pct = len(breakdown.matched_skills) / total_req * 100
        parts.append(
            f"Matched {len(breakdown.matched_skills)}/{total_req} required skills "
            f"({matched_pct:.0f}%)."
        )
    else:
        parts.append("No required skills specified in JD.")

    # Semantic comment
    sem = breakdown.semantic_score
    if sem >= 0.75:
        parts.append("Strong semantic alignment with the job description.")
    elif sem >= 0.50:
        parts.append("Moderate semantic alignment with the job description.")
    else:
        parts.append("Low semantic alignment with the job description.")

    # Experience comment
    exp = breakdown.experience_score
    if exp >= 1.0:
        parts.append("Meets or exceeds experience requirement.")
    elif exp >= 0.5:
        parts.append("Partially meets experience requirement.")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Component scorers
# ---------------------------------------------------------------------------

def _semantic_score(resume_doc: dict, jd_doc: dict) -> float:
    """
    Cosine similarity between the resume and JD embeddings.
    Uses cached embeddings if available; encodes on-the-fly otherwise.
    """
    if not resume_doc.get("embedding"):
        resume_doc["embedding"] = embed_text(resume_doc.get("raw_text", ""))
    if not jd_doc.get("embedding"):
        jd_doc["embedding"] = embed_text(jd_doc.get("raw_text", ""))

    return cosine_similarity(resume_doc["embedding"], jd_doc["embedding"])


def _skill_overlap_score(
    resume_doc: dict,
    jd_doc: dict,
) -> tuple[float, list[str], list[str], list[str]]:
    """
    Hybrid skill-overlap score combining required and preferred skills.

    Scoring formula:
      - Required skills have 2× weight vs preferred skills.
      - Score = (2 * req_matched + pref_matched) / (2 * req_total + pref_total)
      - Falls back to Jaccard if no required skills listed.

    Returns:
        (score, matched_required, missing_required, matched_preferred)
    """
    resume_ner = resume_doc.get("ner") or {}
    jd_ner = jd_doc.get("ner") or {}

    resume_skills: set[str] = {s.lower() for s in (resume_ner.get("skills") or [])}
    required_skills: list[str] = jd_ner.get("required_skills") or []
    preferred_skills: list[str] = jd_ner.get("preferred_skills") or []

    req_lower: set[str] = {s.lower() for s in required_skills}
    pref_lower: set[str] = {s.lower() for s in preferred_skills}

    if not req_lower and not pref_lower:
        return 1.0, [], [], []

    # Required matches
    req_intersection = resume_skills & req_lower
    matched = [s for s in required_skills if s.lower() in req_intersection]
    missing = [s for s in required_skills if s.lower() not in req_intersection]

    # Preferred matches
    pref_intersection = resume_skills & pref_lower
    pref_matched = [s for s in preferred_skills if s.lower() in pref_intersection]

    # Weighted formula
    req_total = len(req_lower)
    pref_total = len(pref_lower)
    numerator = 2 * len(req_intersection) + len(pref_intersection)
    denominator = 2 * req_total + pref_total

    score = numerator / denominator if denominator > 0 else 0.0

    return score, sorted(matched), sorted(missing), sorted(pref_matched)


def _experience_score(resume_doc: dict, jd_doc: dict) -> float:
    """
    Experience-years score: ratio of candidate years to required years, capped at 1.0.
    Candidate years extracted from raw_text via regex.
    """
    jd_ner = jd_doc.get("ner") or {}
    required_years: Optional[int] = jd_ner.get("min_experience_years")

    if not required_years:
        return 1.0  # No requirement → full score

    candidate_years = _extract_max_years(resume_doc.get("raw_text", ""))

    if candidate_years is None:
        return 0.5  # Unknown — partial credit

    return min(1.0, candidate_years / required_years)


def _extract_max_years(text: str) -> Optional[int]:
    """Extract the maximum years-of-experience figure mentioned in text."""
    matches = _YEAR_PATTERN.findall(text)
    if not matches:
        return None
    years = [int(y) for y in matches if y.isdigit()]
    return max(years) if years else None


def _education_score(resume_doc: dict, jd_doc: dict) -> float:
    """
    Education match: checks if the resume's highest education level
    meets or exceeds the JD's education requirements.
    Returns a score in [0, 1].
    """
    jd_ner = jd_doc.get("ner") or {}
    resume_ner = resume_doc.get("ner") or {}

    jd_edu: list[str] = jd_ner.get("education_requirements") or []
    resume_edu: list[str] = resume_ner.get("education") or []

    if not jd_edu:
        return 1.0

    required_level = max(
        (_education_level_for(e) for e in jd_edu),
        default=0,
    )
    if required_level == 0:
        return 1.0

    candidate_level = max(
        (_education_level_for(e) for e in resume_edu),
        default=0,
    )

    if candidate_level == 0:
        return 0.0

    if candidate_level >= required_level:
        return 1.0

    return candidate_level / required_level


def _education_level_for(label: str) -> int:
    """Return the numeric education level for a label string."""
    label_lower = label.lower()
    for keyword, level in _EDUCATION_LEVEL.items():
        if keyword in label_lower:
            return level
    return 0
