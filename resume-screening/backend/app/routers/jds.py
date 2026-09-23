"""
Job Descriptions API router — create, list, get, and delete JDs.
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..db import get_database
from ..models.job_description import (
    JobDescriptionNER,
    JobDescriptionCreate,
    JobDescriptionListResponse,
    JobDescriptionResponse,
)
from ..services.jd_parser import parse_job_description

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Request body schema ---
class JDCreateRequest(BaseModel):
    """Request body for creating a job description."""

    title: str
    company: str | None = None
    raw_text: str


def _doc_to_response(doc: dict) -> JobDescriptionResponse:
    """Convert a MongoDB document to a JobDescriptionResponse."""
    return JobDescriptionResponse(
        id=str(doc["_id"]),
        title=doc["title"],
        company=doc.get("company"),
        raw_text=doc["raw_text"],
        created_time=doc["created_time"],
        ner=JobDescriptionNER(**doc["ner"]) if doc.get("ner") else None,
    )


@router.post("/", response_model=JobDescriptionResponse, status_code=201)
async def create_job_description(body: JDCreateRequest):
    """
    Create a new job description.

    The text is run through the JD parser to extract required/preferred
    skills, experience, and education requirements.
    """
    db = get_database()

    # Run NER / skills extraction
    ner_result = parse_job_description(body.raw_text)

    now = datetime.now(timezone.utc)
    jd_id = str(uuid.uuid4())

    jd_doc = JobDescriptionCreate(
        title=body.title,
        company=body.company,
        raw_text=body.raw_text,
        created_time=now,
        ner=ner_result,
    )

    doc_dict = jd_doc.model_dump()
    doc_dict["_id"] = jd_id

    await db["job_descriptions"].insert_one(doc_dict)
    logger.info("Job description '%s' stored with id=%s", body.title, jd_id)

    return _doc_to_response(doc_dict)


@router.get("/", response_model=JobDescriptionListResponse)
async def list_job_descriptions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
):
    """List all job descriptions with pagination."""
    db = get_database()
    collection = db["job_descriptions"]

    total = await collection.count_documents({})
    cursor = collection.find({}).sort("created_time", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)

    return JobDescriptionListResponse(
        total=total,
        skip=skip,
        limit=limit,
        job_descriptions=[_doc_to_response(doc) for doc in docs],
    )


@router.get("/{jd_id}", response_model=JobDescriptionResponse)
async def get_job_description(jd_id: str):
    """Get a single job description by ID."""
    db = get_database()
    doc = await db["job_descriptions"].find_one({"_id": jd_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Job description not found.")
    return _doc_to_response(doc)


@router.delete("/{jd_id}", status_code=204)
async def delete_job_description(jd_id: str):
    """Delete a job description by ID."""
    db = get_database()
    result = await db["job_descriptions"].delete_one({"_id": jd_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job description not found.")
    logger.info("Deleted job description id=%s", jd_id)
