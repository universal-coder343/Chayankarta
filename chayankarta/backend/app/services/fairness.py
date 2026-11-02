"""
Fairness Audit Service — Milestone 5.

Computes bias / fairness metrics across candidate groups.

Methodology
-----------
Because we cannot legally ask for demographic data, we use *proxy* signals
detectable from resumes BEFORE redaction:
  - gender_proxy : presence of gendered pronouns / titles (Mr/Ms/he/she)
  - institution_tier : broad tier based on keyword heuristics
    (Tier-1 ≡ IIT/IIM/NIT/BITS; Tier-2 ≡ other named institutes)

Metrics computed per group
--------------------------
- count                   : number of candidates in the group
- mean_score              : average final_score (0–100)
- std_score               : standard deviation of scores
- selection_rate          : fraction selected at the given threshold

Fairness metrics
----------------
- disparate_impact_ratio  : min_selection_rate / max_selection_rate
  Values < 0.8 fail the 4/5 rule (EEOC guideline).
- score_delta_redaction   : mean absolute Δ score (redacted vs raw),
  to quantify how much redaction actually changed ranking.

Usage
-----
>>> from .fairness import compute_fairness_audit
>>> report = await compute_fairness_audit(db, threshold=60.0)
"""

import asyncio
import copy
import logging
import math
import re
import statistics
from concurrent.futures import ThreadPoolExecutor

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..config import get_settings
from ..models.ranking import FairnessAuditResponse, GroupMetrics, ScoringWeights
from .embedder import embed_texts
from .scorer import score_resume_against_jd

logger = logging.getLogger(__name__)

_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="fairness")

# Institution tier heuristics
_TIER1_KEYWORDS = {"iit", "iim", "nit", "iiit", "bits", "iiser", "iisc", "xlri", "fms"}
_TIER2_KEYWORDS = {"university", "college", "institute", "polytechnic"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def compute_fairness_audit(
    db: AsyncIOMotorDatabase,
    jd_id: str | None = None,
    threshold: float = 60.0,
) -> FairnessAuditResponse:
    """
    Compute fairness metrics for the current resume pool.

    Args:
        db        : Motor async database.
        jd_id     : Optional JD to score against. If None, uses first JD found.
        threshold : Score threshold (0–100) for 'selected' status.

    Returns:
        FairnessAuditResponse with group metrics, DI ratio, and redaction delta.
    """
    settings = get_settings()

    # --- Fetch JD ---
    if jd_id:
        jd_doc = await db["job_descriptions"].find_one({"_id": jd_id})
    else:
        jd_doc = await db["job_descriptions"].find_one({})

    if jd_doc is None:
        return FairnessAuditResponse(
            threshold=threshold,
            total_candidates=0,
            groups=[],
            summary="No job descriptions found in the database.",
            redaction_enabled=settings.enable_redaction,
        )

    # --- Fetch resumes ---
    cursor = db["resumes"].find({})
    resume_docs: list[dict] = await cursor.to_list(length=None)

    if not resume_docs:
        return FairnessAuditResponse(
            threshold=threshold,
            total_candidates=0,
            groups=[],
            summary="No resumes found in the database.",
            redaction_enabled=settings.enable_redaction,
        )

    weights = ScoringWeights(
        semantic=settings.weight_semantic,
        skill_overlap=settings.weight_skill,
        experience=settings.weight_experience,
        education=settings.weight_education,
    )

    # --- Score with raw text ---
    raw_scores = await _score_batch(resume_docs, jd_doc, weights, redact=False)

    # --- Score with redacted text (if redaction enabled) ---
    redacted_scores: list[float] | None = None
    if settings.enable_redaction:
        redacted_scores = await _score_batch(
            resume_docs, jd_doc, weights, redact=True,
            redact_institutions=settings.redact_institutions,
        )

    # Use whichever scores are appropriate for the audit
    active_scores = redacted_scores if redacted_scores is not None else raw_scores

    # --- Infer group labels ---
    labels = _infer_groups(resume_docs)

    # --- Compute group metrics ---
    group_data: dict[str, list[float]] = {}
    for score, label in zip(active_scores, labels):
        group_data.setdefault(label, []).append(score)

    groups: list[GroupMetrics] = []
    for label, scores in sorted(group_data.items()):
        n = len(scores)
        mean_s = statistics.mean(scores) if scores else 0.0
        std_s = statistics.pstdev(scores) if len(scores) > 1 else 0.0
        selected = sum(1 for s in scores if s >= threshold)
        sel_rate = selected / n if n > 0 else 0.0
        groups.append(
            GroupMetrics(
                group_label=label,
                count=n,
                mean_score=round(mean_s, 2),
                std_score=round(std_s, 2),
                selection_rate=round(sel_rate, 4),
            )
        )

    # --- Disparate Impact ---
    di_ratio: float | None = None
    passes_four_fifths: bool | None = None
    if len(groups) >= 2:
        selection_rates = [g.selection_rate for g in groups]
        max_rate = max(selection_rates)
        min_rate = min(selection_rates)
        if max_rate > 0:
            di_ratio = round(min_rate / max_rate, 4)
            passes_four_fifths = di_ratio >= 0.8

    # --- Redaction delta ---
    score_delta: float | None = None
    if redacted_scores is not None:
        deltas = [abs(r - r_raw) for r, r_raw in zip(redacted_scores, raw_scores)]
        score_delta = round(statistics.mean(deltas), 2) if deltas else None

    summary = _build_summary(di_ratio, passes_four_fifths, score_delta, groups)

    return FairnessAuditResponse(
        threshold=threshold,
        total_candidates=len(resume_docs),
        groups=groups,
        disparate_impact_ratio=di_ratio,
        passes_four_fifths_rule=passes_four_fifths,
        score_delta_redaction=score_delta,
        redaction_enabled=settings.enable_redaction,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _score_batch(
    resume_docs: list[dict],
    jd_doc: dict,
    weights: ScoringWeights,
    redact: bool = False,
    redact_institutions: bool = False,
) -> list[float]:
    """Score all resumes against jd_doc; returns list of final_scores."""
    from .ranker import _prepare_scoring_docs

    scoring_docs = _prepare_scoring_docs(resume_docs, redact, redact_institutions)

    # Ensure JD has an embedding
    if not jd_doc.get("embedding"):
        loop = asyncio.get_running_loop()
        vecs = await loop.run_in_executor(
            _EXECUTOR,
            lambda: embed_texts([jd_doc.get("raw_text", "")]),
        )
        jd_doc["embedding"] = vecs[0]

    # Embed scoring docs that are missing embeddings
    to_embed_indices = [i for i, d in enumerate(scoring_docs) if not d.get("embedding")]
    if to_embed_indices:
        texts = [scoring_docs[i].get("raw_text", "") for i in to_embed_indices]
        loop = asyncio.get_running_loop()
        vecs = await loop.run_in_executor(_EXECUTOR, lambda: embed_texts(texts))
        for idx, vec in zip(to_embed_indices, vecs):
            scoring_docs[idx]["embedding"] = vec

    loop = asyncio.get_running_loop()

    def _run():
        scores = []
        for sdoc in scoring_docs:
            final_score, _ = score_resume_against_jd(sdoc, jd_doc, weights)
            scores.append(final_score)
        return scores

    return await loop.run_in_executor(_EXECUTOR, _run)


def _infer_groups(resume_docs: list[dict]) -> list[str]:
    """
    Assign a group label to each resume based on detectable proxy signals.

    Priority:
      1. gender_proxy (he/she/Mr/Ms in raw_text)
      2. institution_tier (Tier-1 / Tier-2 / unknown from education field)
      3. "unknown" as fallback

    Labels: "gender_male_proxy", "gender_female_proxy",
            "institution_tier1", "institution_tier2", "unknown"
    """
    _he_re = re.compile(r"\b(he|him|his|himself|mr\.?)\b")
    _she_re = re.compile(r"\b(she|her|hers|herself|ms\.?|mrs\.?|miss)\b")

    labels: list[str] = []
    for doc in resume_docs:
        raw = doc.get("raw_text", "").lower()
        ner = doc.get("ner") or {}
        edu = " ".join(ner.get("education") or []).lower()

        # Gender proxy
        he_count = len(_he_re.findall(raw))
        she_count = len(_she_re.findall(raw))

        if he_count > she_count and he_count > 0:
            labels.append("gender_male_proxy")
        elif she_count > he_count and she_count > 0:
            labels.append("gender_female_proxy")
        elif any(k in edu for k in _TIER1_KEYWORDS):
            labels.append("institution_tier1")
        elif any(k in edu for k in _TIER2_KEYWORDS):
            labels.append("institution_tier2")
        else:
            labels.append("unknown")

    return labels




def _build_summary(
    di_ratio: float | None,
    passes: bool | None,
    score_delta: float | None,
    groups: list[GroupMetrics],
) -> str:
    """Build a human-readable summary of the audit results."""
    parts: list[str] = []

    if di_ratio is not None:
        status = "PASS ✓" if passes else "FAIL ✗"
        parts.append(
            f"Disparate Impact Ratio: {di_ratio:.2f} [{status}] "
            f"(4/5 rule threshold: 0.80)."
        )
    else:
        parts.append("Insufficient group diversity to compute disparate impact ratio.")

    if score_delta is not None:
        parts.append(
            f"Mean score delta (redacted vs raw): {score_delta:.1f} points."
        )

    if groups:
        best = max(groups, key=lambda g: g.selection_rate)
        worst = min(groups, key=lambda g: g.selection_rate)
        parts.append(
            f"Highest selection rate: '{best.group_label}' ({best.selection_rate:.1%}). "
            f"Lowest: '{worst.group_label}' ({worst.selection_rate:.1%})."
        )

    return " ".join(parts)
