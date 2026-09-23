"""
Pydantic v2 models for the Resume entity.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ResumeNER(BaseModel):
    """Named-entity extraction results from a resume."""

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    category: Optional[str] = None  # Kaggle dataset label, if available


class ResumeBase(BaseModel):
    """Fields common to all resume representations."""

    filename: str
    file_type: str  # "pdf", "docx", "image"
    raw_text: str
    parsing_method: str  # "pdfplumber", "python-docx", "ocr"


class ResumeCreate(ResumeBase):
    """Schema used when creating a new resume document."""

    upload_time: datetime = Field(default_factory=lambda: datetime.now())
    ner: Optional[ResumeNER] = None


class ResumeInDB(ResumeBase):
    """Full resume document as stored in MongoDB."""

    id: str = Field(alias="_id")
    upload_time: datetime
    ner: Optional[ResumeNER] = None

    # Phase 2 placeholders — not populated yet
    embedding: Optional[list[float]] = None
    similarity_score: Optional[float] = None
    bias_flags: Optional[list[str]] = None

    model_config = {"populate_by_name": True}


class ResumeResponse(BaseModel):
    """API response for a single resume."""

    id: str
    filename: str
    file_type: str
    upload_time: datetime
    parsing_method: str
    raw_text: str
    ner: Optional[ResumeNER] = None


class ResumeListResponse(BaseModel):
    """API response for listing resumes (paginated)."""

    total: int
    skip: int
    limit: int
    resumes: list[ResumeResponse]
