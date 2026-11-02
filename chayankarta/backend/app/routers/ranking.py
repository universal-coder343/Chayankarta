"""
Rankings API router — Milestone 4.

Endpoints
---------
POST /api/rankings/         : Rank all (or specified) resumes against a JD.
GET  /api/rankings/         : Same as POST but via query params (jd_id, top_k, min_score).
POST /api/rankings/backfill : Embed all unembedded resumes/JDs in the DB.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, Query

from ..db import get_database
from ..models.ranking import RankRequest, RankResponse
from ..services.ranker import _EXECUTOR, rank_resumes

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# POST /api/rankings/ — rank with full request body
# ---------------------------------------------------------------------------

@router.post("/", response_model=RankResponse, status_code=200)
async def rank_candidates(body: RankRequest):
    """
    Rank candidates against a job description.

    The body allows fine-grained control over weights, resume subset, and filters.
    On success returns a ranked list of candidates with score breakdowns.
    """
    db = get_database()
    try:
        response = await rank_resumes(db, body)
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=422, detail=msg)
    return response


# ---------------------------------------------------------------------------
# GET /api/rankings/ — rank via query parameters (quick convenience)
# ---------------------------------------------------------------------------

@router.get("/", response_model=RankResponse, status_code=200)
async def rank_candidates_get(
    jd_id: str = Query(..., description="Job description ID to rank against."),
    top_k: int = Query(10, ge=1, le=200, description="Maximum candidates to return."),
    min_score: float = Query(0.0, ge=0.0, le=100.0, description="Minimum score (0–100) to include."),
):
    """
    Convenience GET endpoint for rankings.

    Equivalent to POST /api/rankings/ with jd_id, top_k, min_score in the body.
    """
    db = get_database()
    request = RankRequest(jd_id=jd_id, top_k=top_k, min_score=min_score)
    try:
        response = await rank_resumes(db, request)
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=422, detail=msg)
    return response


# ---------------------------------------------------------------------------
# POST /api/rankings/backfill — embed all documents without embeddings
# ---------------------------------------------------------------------------

@router.post("/backfill", status_code=200)
async def backfill_embeddings():
    """
    Backfill embeddings for all resumes and job descriptions in MongoDB
    that do not yet have a stored embedding vector.

    This is safe to call multiple times (idempotent).
    """
    db = get_database()
    from ..services.embedder import embed_texts

    # --- Resumes ---
    resume_cursor = db["resumes"].find(
        {"embedding": {"$exists": False}},
        {"_id": 1, "raw_text": 1},
    )
    resume_docs = await resume_cursor.to_list(length=None)

    # Also catch docs where embedding is null/None
    resume_null_cursor = db["resumes"].find(
        {"embedding": None},
        {"_id": 1, "raw_text": 1},
    )
    resume_docs += await resume_null_cursor.to_list(length=None)

    # Deduplicate by _id
    seen_ids: set = set()
    unique_resumes = []
    for r in resume_docs:
        if r["_id"] not in seen_ids:
            seen_ids.add(r["_id"])
            unique_resumes.append(r)

    # --- JDs ---
    jd_cursor = db["job_descriptions"].find(
        {"embedding": {"$exists": False}},
        {"_id": 1, "raw_text": 1},
    )
    jd_docs = await jd_cursor.to_list(length=None)
    jd_null_cursor = db["job_descriptions"].find(
        {"embedding": None},
        {"_id": 1, "raw_text": 1},
    )
    jd_docs_null = await jd_null_cursor.to_list(length=None)

    seen_jd_ids: set = set()
    unique_jds = []
    for j in jd_docs + jd_docs_null:
        if j["_id"] not in seen_jd_ids:
            seen_jd_ids.add(j["_id"])
            unique_jds.append(j)

    all_docs = [("resume", d) for d in unique_resumes] + [("jd", d) for d in unique_jds]

    if not all_docs:
        return {"message": "All documents already have embeddings.", "embedded": 0}

    texts = [d.get("raw_text", "") for _, d in all_docs]

    loop = asyncio.get_running_loop()
    embeddings = await loop.run_in_executor(_EXECUTOR, lambda: embed_texts(texts))

    update_tasks = []
    for (dtype, doc), vec in zip(all_docs, embeddings):
        collection = "resumes" if dtype == "resume" else "job_descriptions"
        update_tasks.append(
            db[collection].update_one(
                {"_id": doc["_id"]},
                {"$set": {"embedding": vec}},
            )
        )

    await asyncio.gather(*update_tasks)

    logger.info(
        "Backfill complete: %d resumes + %d JDs embedded.",
        len(unique_resumes),
        len(unique_jds),
    )

    return {
        "message": "Backfill complete.",
        "embedded": len(all_docs),
        "resumes": len(unique_resumes),
        "job_descriptions": len(unique_jds),
    }
