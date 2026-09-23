"""
Pytest configuration and shared fixtures for the test suite.
"""

import os
import sys
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db():
    """
    Mock MongoDB database.
    Returns an AsyncMock that simulates motor's AsyncIOMotorDatabase.
    """
    db = AsyncMock()

    # Mock collections
    db["resumes"] = AsyncMock()
    db["job_descriptions"] = AsyncMock()

    # Make command() work for health check
    db.command = AsyncMock(return_value={"ok": 1})

    return db


@pytest.fixture
async def async_client(mock_db):
    """
    Create an httpx AsyncClient for testing FastAPI endpoints.
    Patches the database to use mock_db.
    """
    with patch("app.db._database", mock_db), \
         patch("app.db._client", MagicMock()):
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


# ---------------------------------------------------------------------------
# Sample text fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_resume_text() -> str:
    """A realistic resume text snippet for NER testing."""
    return """\
John Doe
john.doe@example.com | +1-555-0101 | San Francisco, CA

SUMMARY
Software Engineer with 5+ years of experience in Python, JavaScript, and React.

SKILLS
Python, JavaScript, TypeScript, React, Django, FastAPI, PostgreSQL, MongoDB,
Docker, Kubernetes, AWS, Git, CI/CD, Agile, Scrum

EXPERIENCE
Senior Software Engineer — TechCorp Inc.
Jan 2021 – Present
- Built microservices architecture using FastAPI and Docker
- Deployed to AWS EKS using Kubernetes

Software Engineer — WebStart LLC
Jun 2018 – Dec 2020
- Full-stack development with React and Django

EDUCATION
B.S. in Computer Science — University of Texas at Austin, 2018

CERTIFICATIONS
AWS Certified Solutions Architect
"""


@pytest.fixture
def sample_jd_text() -> str:
    """A realistic job description text for JD parser testing."""
    return """\
Full-Stack Developer

Required Skills:
- 3+ years of experience in full-stack development
- Strong proficiency in JavaScript, TypeScript, and React
- Backend experience with Python and Django or FastAPI
- Experience with PostgreSQL or MongoDB
- Familiarity with Docker and CI/CD pipelines
- Bachelor's degree in Computer Science

Nice to Have:
- Experience with Kubernetes and AWS
- Knowledge of GraphQL
"""
