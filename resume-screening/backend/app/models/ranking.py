"""
Pydantic v2 models for resume ranking and fairness audit.

Covers:
- ScoringWeights  : per-component weight overrides
- RankRequest     : body sent to POST /api/rankings
- ScoreBreakdown  : per-component scores for explainability
- CandidateRank   : a single ranked candidate with scores
- RankResponse    : full ranking API response
- FairnessMetrics : fairness audit response models
"""

from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class ScoringWeights(BaseModel):
    """
    Relative importance of each scoring component.
    All weights should sum to 1.0.
    """

    semantic: float = Field(
        default=0.40, ge=0.0, le=1.0,
        description="Semantic embedding cosine-similarity weight.",
    )
    skill_overlap: float = Field(
        default=0.35, ge=0.0, le=1.0,
        description="Required-skills overlap weight (Jaccard-based).",
    )
    experience: float = Field(
        default=0.15, ge=0.0, le=1.0,
        description="Experience-years match weight.",
    )
    education: float = Field(
        default=0.10, ge=0.0, le=1.0,
        description="Education requirement match weight.",
    )


class RankRequest(BaseModel):
    """Request body for the ranking endpoint."""

    jd_id: str = Field(
        ...,
        description="MongoDB _id of the job description to rank against.",
    )
    resume_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Explicit list of resume IDs to rank. "
            "If empty, all resumes in the DB are ranked."
        ),
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=200,
        description="Return only the top-k ranked candidates.",
    )
    min_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Minimum final_score (0-100) to include in results.",
    )
    weights: Optional[ScoringWeights] = Field(
        default=None,
        description="Optional overrides for the component weights.",
    )


# ---------------------------------------------------------------------------
# Per-candidate score breakdown (explainability)
# ---------------------------------------------------------------------------

class ScoreBreakdown(BaseModel):
    """Explainable breakdown of a candidate's overall score."""

    semantic_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Cosine similarity between resume and JD embeddings.",
    )
    skill_overlap_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Required+preferred skills overlap score.",
    )
    experience_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Normalised experience-years match.",
    )
    education_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Education requirement overlap score.",
    )
    matched_skills: list[str] = Field(
        default_factory=list,
        description="Required JD skills found in the resume.",
    )
    missing_skills: list[str] = Field(
        default_factory=list,
        description="Required JD skills NOT found in the resume.",
    )
    preferred_matched: list[str] = Field(
        default_factory=list,
        description="Preferred JD skills found in the resume.",
    )


class CandidateRank(BaseModel):
    """A single ranked candidate entry."""

    rank: int = Field(..., description="1-based rank position.")
    resume_id: str
    filename: str
    candidate_name: Optional[str] = None
    final_score: float = Field(
        ..., ge=0.0, le=100.0,
        description="Weighted composite score, normalised 0–100.",
    )
    breakdown: ScoreBreakdown
    explanation: str = Field(
        default="",
        description="Short human-readable explanation of the score.",
    )


class RankResponse(BaseModel):
    """Full ranking response for a given job description."""

    jd_id: str
    jd_title: str
    total_resumes_evaluated: int
    weights_used: ScoringWeights
    rankings: list[CandidateRank]
    page: int = 1
    page_size: int = Field(default=10)
    total_pages: int = 1
    redaction_enabled: bool = False


# ---------------------------------------------------------------------------
# Fairness Audit models (Milestone 5)
# ---------------------------------------------------------------------------

class GroupMetrics(BaseModel):
    """Score metrics for a single demographic group proxy."""

    group_label: str
    count: int
    mean_score: float
    std_score: float
    selection_rate: float = Field(
        ...,
        description="Fraction of this group selected above threshold.",
    )


class FairnessAuditResponse(BaseModel):
    """Response from the fairness audit endpoint."""

    threshold: float = Field(
        default=60.0,
        description="Score threshold used for selection rate calculation.",
    )
    total_candidates: int
    groups: list[GroupMetrics]
    disparate_impact_ratio: Optional[float] = Field(
        default=None,
        description=(
            "Min selection rate / max selection rate across groups. "
            "Values < 0.8 fail the 4/5 rule."
        ),
    )
    passes_four_fifths_rule: Optional[bool] = None
    score_delta_redaction: Optional[float] = Field(
        default=None,
        description=(
            "Mean absolute score difference between redacted and raw scoring. "
            "Only present when redaction is toggled."
        ),
    )
    redaction_enabled: bool = False
    summary: str = ""
