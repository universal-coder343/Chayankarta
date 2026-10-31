"""
Resume ranking orchestrator — Milestone 4.

Responsibilities
----------------
1. Fetch the JD and candidate resumes from MongoDB.
2. Optionally redact PII from resume text before embedding (Milestone 5).
3. Batch-embed any documents that don't yet have a stored embedding,
   then persist the new embeddings back to MongoDB.
4. Score every resume against the JD using the hybrid scorer.
5. Apply min_score filter, sort by final_score, return the top-k results.

Usage
-----
>>> from .ranker import rank_resumes
>>> response = await rank_resumes(db, rank_request)
"""

import asyncio
import copy
import logging
from concurrent.futures import ThreadPoolExecutor
from math import ceil

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..config import get_settings
from ..models.ranking import (
    CandidateRank,
    RankRequest,
    RankResponse,
    ScoringWeights,
)
from .embedder import embed_texts
from .scorer import build_explanation, score_resume_against_jd

logger = logging.getLogger(__name__)

# Thread-pool for CPU-bound embedding work (model inference).
_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="embedder")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def rank_resumes(
    db: AsyncIOMotorDatabase,
    request: RankRequest,
) -> RankResponse:
    """
    Rank resumes against a job description.

    Args:
        db      : Motor async database instance.
        request : RankRequest from the API endpoint.

    Returns:
        RankResponse with sorted, filtered candidate list.

    Raises:
        ValueError: If the JD or no resumes are found.
    """
    settings = get_settings()
    weights: ScoringWeights = request.weights or ScoringWeights(
        semantic=settings.weight_semantic,
        skill_overlap=settings.weight_skill,
        experience=settings.weight_experience,
        education=settings.weight_education,
    )

    # ------------------------------------------------------------------ #
    # 1. Fetch JD
    # ------------------------------------------------------------------ #
    jd_doc = await db["job_descriptions"].find_one({"_id": request.jd_id})
    if jd_doc is None:
        raise ValueError(f"Job description '{request.jd_id}' not found.")

    logger.info("Ranking against JD: '%s' (id=%s)", jd_doc.get("title"), request.jd_id)

    # ------------------------------------------------------------------ #
    # 2. Fetch resumes
    # ------------------------------------------------------------------ #
    if request.resume_ids:
        query = {"_id": {"$in": request.resume_ids}}
    else:
        query = {}

    cursor = db["resumes"].find(query)
    resume_docs: list[dict] = await cursor.to_list(length=None)

    if not resume_docs:
        raise ValueError("No resumes found matching the given criteria.")

    logger.info("Found %d resume(s) to rank.", len(resume_docs))

    # ------------------------------------------------------------------ #
    # 3. Redaction (Milestone 5): use redacted_text for embedding/scoring
    #    but keep original data intact in MongoDB
    # ------------------------------------------------------------------ #
    redaction_enabled = settings.enable_redaction
    scoring_docs = _prepare_scoring_docs(
        resume_docs, redaction_enabled, settings.redact_institutions
    )

    # ------------------------------------------------------------------ #
    # 4. Batch-embed documents that lack a stored embedding
    # ------------------------------------------------------------------ #
    await _ensure_embeddings(db, scoring_docs, jd_doc, redaction_enabled)

    # ------------------------------------------------------------------ #
    # 5. Score every resume (run in thread-pool to avoid blocking event loop)
    # ------------------------------------------------------------------ #
    loop = asyncio.get_running_loop()

    def _score_all():
        results = []
        for rdoc, orig_doc in zip(scoring_docs, resume_docs):
            final_score, breakdown = score_resume_against_jd(rdoc, jd_doc, weights)
            explanation = build_explanation(final_score, breakdown, jd_doc)
            results.append((orig_doc, rdoc, final_score, breakdown, explanation))
        return results

    scored = await loop.run_in_executor(_EXECUTOR, _score_all)

    # ------------------------------------------------------------------ #
    # 6. Sort → filter by min_score → paginate → build response
    # ------------------------------------------------------------------ #
    scored.sort(key=lambda x: x[2], reverse=True)

    # Apply min_score filter
    min_score = request.min_score
    filtered = [(od, rd, fs, bd, ex) for od, rd, fs, bd, ex in scored if fs >= min_score]

    total_after_filter = len(filtered)
    top_k = min(request.top_k, total_after_filter)
    top_results = filtered[:top_k]

    rankings: list[CandidateRank] = []
    for rank_pos, (orig_doc, _, final_score, breakdown, explanation) in enumerate(
        top_results, start=1
    ):
        ner = orig_doc.get("ner") or {}
        rankings.append(
            CandidateRank(
                rank=rank_pos,
                resume_id=str(orig_doc["_id"]),
                filename=orig_doc.get("filename", ""),
                candidate_name=ner.get("name"),
                final_score=final_score,
                breakdown=breakdown,
                explanation=explanation,
            )
        )

    logger.info(
        "Ranking complete. Top-%d of %d candidates (after filter). Best score: %.1f",
        top_k,
        total_after_filter,
        rankings[0].final_score if rankings else 0.0,
    )

    total_pages = max(1, ceil(total_after_filter / request.top_k))

    return RankResponse(
        jd_id=request.jd_id,
        jd_title=jd_doc.get("title", ""),
        total_resumes_evaluated=len(scored),
        weights_used=weights,
        rankings=rankings,
        page=1,
        page_size=request.top_k,
        total_pages=total_pages,
        redaction_enabled=redaction_enabled,
    )


# ---------------------------------------------------------------------------
# Redaction helper
# ---------------------------------------------------------------------------

def _prepare_scoring_docs(
    resume_docs: list[dict],
    redaction_enabled: bool,
    redact_institutions: bool,
) -> list[dict]:
    """
    Return shallow copies of resume docs with raw_text replaced by
    redacted text (if redaction is enabled), so embeddings are computed
    on bias-free text. The originals are not mutated.
    """
    if not redaction_enabled:
        return resume_docs  # no copy needed — originals used directly

    from .redactor import redact_pii

    scoring_docs: list[dict] = []
    for rdoc in resume_docs:
        scoring_doc = copy.copy(rdoc)  # shallow copy
        raw = rdoc.get("raw_text", "")
        result = redact_pii(raw, redact_institutions=redact_institutions)
        scoring_doc["raw_text"] = result.redacted_text
        # Don't reuse stored embedding when redaction is enabled —
        # we need an embedding of the *redacted* text
        scoring_doc["embedding"] = None
        scoring_docs.append(scoring_doc)
    return scoring_docs


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

async def _ensure_embeddings(
    db: AsyncIOMotorDatabase,
    resume_docs: list[dict],
    jd_doc: dict,
    redaction_enabled: bool,
) -> None:
    """
    Batch-embed any documents that don't have a stored embedding,
    then write the new embeddings back to MongoDB (only for raw, non-redacted docs).
    """
    resumes_to_embed = [r for r in resume_docs if not r.get("embedding")]
    needs_jd_embed = not jd_doc.get("embedding")

    texts_to_embed: list[str] = []
    sources: list[tuple[str, dict]] = []  # ("resume" | "jd", doc)

    for rdoc in resumes_to_embed:
        texts_to_embed.append(rdoc.get("raw_text", ""))
        sources.append(("resume", rdoc))

    if needs_jd_embed:
        texts_to_embed.append(jd_doc.get("raw_text", ""))
        sources.append(("jd", jd_doc))

    if not texts_to_embed:
        return

    logger.info(
        "Batch-embedding %d document(s) (resumes: %d, jd: %d) …",
        len(texts_to_embed),
        len(resumes_to_embed),
        int(needs_jd_embed),
    )

    loop = asyncio.get_running_loop()
    embeddings: list[list[float]] = await loop.run_in_executor(
        _EXECUTOR,
        lambda: embed_texts(texts_to_embed),
    )

    write_tasks = []
    for (source_type, doc), vec in zip(sources, embeddings):
        doc["embedding"] = vec

        # Only persist to MongoDB when we're NOT using redacted text
        # (redacted scoring_docs are ephemeral copies)
        if source_type == "jd":
            write_tasks.append(
                db["job_descriptions"].update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"embedding": vec}},
                )
            )
        elif source_type == "resume" and not redaction_enabled:
            write_tasks.append(
                db["resumes"].update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"embedding": vec}},
                )
            )

    if write_tasks:
        await asyncio.gather(*write_tasks)
        logger.info("Persisted %d new embedding(s) to MongoDB.", len(write_tasks))
