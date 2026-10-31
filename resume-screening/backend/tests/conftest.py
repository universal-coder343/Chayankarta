"""
Pytest configuration and shared fixtures for the test suite.
"""

import hashlib
import os
import sys
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Configure pytest-asyncio to auto mode (no need to mark each test)
pytest_plugins = ("pytest_asyncio",)


# ---------------------------------------------------------------------------
# Fake embedding model — deterministic, no sentence-transformers required
# ---------------------------------------------------------------------------

class _FakeModel:
    """
    Drop-in replacement for SentenceTransformer(all-MiniLM-L6-v2).

    * Returns deterministic 384-dim unit-length vectors (seeded by MD5 of text)
    * Accepts the same kwargs as the real model's encode() method
    * Works for both single strings and lists (batch)
    """

    DIM = 384

    def get_sentence_embedding_dimension(self):
        return self.DIM

    def encode(self, sentences, normalize_embeddings=True,
               show_progress_bar=False, batch_size=32):
        if isinstance(sentences, str):
            sentences = [sentences]
        vecs = []
        for s in sentences:
            seed = int(hashlib.md5(s.encode()).hexdigest(), 16) % (2 ** 31)
            rng = np.random.default_rng(seed)
            v = rng.standard_normal(self.DIM).astype(np.float32)
            if normalize_embeddings:
                norm = np.linalg.norm(v)
                if norm > 0:
                    v = v / norm
            vecs.append(v)
        result = np.array(vecs)
        return result if len(vecs) > 1 else result[0]


@pytest.fixture(autouse=True, scope="session")
def patch_sentence_transformers():
    """
    Replace the real SentenceTransformer with _FakeModel for the entire test
    session.  This means:
    - sentence-transformers does NOT need to be installed.
    - Tests run fast (no model download / GPU init).
    - Embeddings are deterministic across runs.

    Tests that need custom embedding behaviour (e.g. test_embedder.py) can
    override _get_model locally via monkeypatch — the local patch wins because
    lru_cache is cleared before each override.
    """
    import app.services.embedder as embedder_mod
    _fake = _FakeModel()
    embedder_mod._get_model.cache_clear()
    with patch.object(embedder_mod, "_get_model", new=lambda: _fake):
        yield
    embedder_mod._get_model.cache_clear()


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use the default event loop policy."""
    return asyncio.DefaultEventLoopPolicy()


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
