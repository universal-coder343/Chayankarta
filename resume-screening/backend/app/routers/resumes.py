"""
Resume API router — upload, list, get, and delete resumes.
"""

import logging
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from ..config import get_settings
from ..db import get_database
from ..models.resume import ResumeCreate, ResumeListResponse, ResumeNER, ResumeResponse
from ..services.ner import extract_entities
from ..services.parser import ParseResult, parse_resume

logger = logging.getLogger(__name__)
router = APIRouter()


def _doc_to_response(doc: dict) -> ResumeResponse:
    """Convert a MongoDB document to a ResumeResponse."""
    return ResumeResponse(
        id=str(doc["_id"]),
        filename=doc["filename"],
        file_type=doc["file_type"],
        upload_time=doc["upload_time"],
        parsing_method=doc["parsing_method"],
        raw_text=doc["raw_text"],
        ner=ResumeNER(**doc["ner"]) if doc.get("ner") else None,
    )


@router.post("/upload", response_model=ResumeResponse, status_code=201)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume file (PDF, DOCX, PNG, JPG).

    The file is saved to disk, parsed for text, and run through the NER
    pipeline. The result is stored in MongoDB.
    """
    settings = get_settings()
    db = get_database()

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    allowed_extensions = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed_extensions)}",
        )

    # Check for duplicate filename
    existing = await db["resumes"].find_one({"filename": file.filename})
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A resume with filename '{file.filename}' already exists.",
        )

    # Save file to disk
    file_id = str(uuid.uuid4())
    save_filename = f"{file_id}{ext}"
    save_path = os.path.join(settings.upload_dir, save_filename)
    os.makedirs(settings.upload_dir, exist_ok=True)

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)
    logger.info("Saved uploaded file to %s", save_path)

    try:
        # Parse the file
        result: ParseResult = parse_resume(save_path, file.filename)

        # Run NER extraction
        ner_result = extract_entities(result.raw_text)

        # Build document
        now = datetime.now(timezone.utc)
        resume_doc = ResumeCreate(
            filename=file.filename,
            file_type=result.file_type,
            raw_text=result.raw_text,
            parsing_method=result.parsing_method,
            upload_time=now,
            ner=ner_result,
        )

        doc_dict = resume_doc.model_dump()
        doc_dict["_id"] = file_id

        # Insert into MongoDB
        await db["resumes"].insert_one(doc_dict)
        logger.info("Resume '%s' stored with id=%s", file.filename, file_id)

        return _doc_to_response(doc_dict)

    except Exception as exc:
        # Clean up saved file on error
        if os.path.exists(save_path):
            os.remove(save_path)
        logger.error("Failed to process resume '%s': %s", file.filename, exc)
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(exc)}")


@router.get("/", response_model=ResumeListResponse)
async def list_resumes(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
):
    """List all resumes with pagination."""
    db = get_database()
    collection = db["resumes"]

    total = await collection.count_documents({})
    cursor = collection.find({}).sort("upload_time", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)

    return ResumeListResponse(
        total=total,
        skip=skip,
        limit=limit,
        resumes=[_doc_to_response(doc) for doc in docs],
    )


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: str):
    """Get a single resume by ID."""
    db = get_database()
    doc = await db["resumes"].find_one({"_id": resume_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return _doc_to_response(doc)


@router.delete("/{resume_id}", status_code=204)
async def delete_resume(resume_id: str):
    """Delete a resume by ID."""
    db = get_database()
    result = await db["resumes"].delete_one({"_id": resume_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Resume not found.")

    # Also try to delete the uploaded file
    settings = get_settings()
    upload_dir = settings.upload_dir
    for fname in os.listdir(upload_dir):
        if fname.startswith(resume_id):
            os.remove(os.path.join(upload_dir, fname))
            break

    logger.info("Deleted resume id=%s", resume_id)
