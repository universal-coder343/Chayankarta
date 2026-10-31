"""
Fairness Audit API router — Milestone 5.

Endpoints
---------
GET  /api/audit/fairness    : Compute and return fairness metrics.
GET  /api/audit/redact-preview/{resume_id} : Preview redacted text for a resume.
"""

import logging

from fastapi import APIRouter, HTTPException, Query

from ..db import get_database
from ..models.ranking import FairnessAuditResponse
from ..services.fairness import compute_fairness_audit

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# GET /api/audit/fairness
# ---------------------------------------------------------------------------

@router.get("/fairness", response_model=FairnessAuditResponse)
async def get_fairness_audit(
    jd_id: str = Query(
        default=None,
        description="JD to score resumes against. Defaults to first JD in DB.",
    ),
    threshold: float = Query(
        default=60.0,
        ge=0.0,
        le=100.0,
        description="Score threshold (0–100) for 'selected' status.",
    ),
):
    """
    Compute fairness metrics for the current resume pool.

    Returns group score distributions, disparate impact ratio (4/5 rule),
    and the score delta introduced by PII redaction.
    """
    db = get_database()
    result = await compute_fairness_audit(db, jd_id=jd_id, threshold=threshold)
    return result


# ---------------------------------------------------------------------------
# GET /api/audit/redact-preview/{resume_id}
# ---------------------------------------------------------------------------

@router.get("/redact-preview/{resume_id}")
async def redact_preview(resume_id: str):
    """
    Preview the PII-redacted version of a resume.

    Returns both the original and redacted text, plus a list of
    redacted item categories — useful for transparency / audit UI.
    """
    from ..config import get_settings
    from ..services.redactor import redact_pii

    db = get_database()
    doc = await db["resumes"].find_one({"_id": resume_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Resume not found.")

    settings = get_settings()
    raw_text = doc.get("raw_text", "")
    result = redact_pii(raw_text, redact_institutions=settings.redact_institutions)

    return {
        "resume_id": resume_id,
        "filename": doc.get("filename", ""),
        "original_text": raw_text,
        "redacted_text": result.redacted_text,
        "redaction_count": result.redaction_count,
        "redacted_categories": list(set(
            item.split(":")[0].strip("[]") for item in result.redacted_items
        )),
    }
