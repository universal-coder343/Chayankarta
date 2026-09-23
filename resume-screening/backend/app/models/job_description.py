"""
Pydantic v2 models for the Job Description entity.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JobDescriptionNER(BaseModel):
    """Extracted requirements from a job description."""

    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_experience_years: Optional[int] = None
    education_requirements: list[str] = Field(default_factory=list)


class JobDescriptionBase(BaseModel):
    """Fields common to all JD representations."""

    title: str
    company: Optional[str] = None
    raw_text: str


class JobDescriptionCreate(JobDescriptionBase):
    """Schema used when creating a new JD document."""

    created_time: datetime = Field(default_factory=lambda: datetime.now())
    ner: Optional[JobDescriptionNER] = None


class JobDescriptionInDB(JobDescriptionBase):
    """Full JD document as stored in MongoDB."""

    id: str = Field(alias="_id")
    created_time: datetime
    ner: Optional[JobDescriptionNER] = None

    model_config = {"populate_by_name": True}


class JobDescriptionResponse(BaseModel):
    """API response for a single job description."""

    id: str
    title: str
    company: Optional[str] = None
    raw_text: str
    created_time: datetime
    ner: Optional[JobDescriptionNER] = None


class JobDescriptionListResponse(BaseModel):
    """API response for listing job descriptions."""

    total: int
    skip: int
    limit: int
    job_descriptions: list[JobDescriptionResponse]
