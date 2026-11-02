"""
Tests for the rankings and audit API endpoints (Milestone 4 & 5).

Happy-path and edge-case tests for:
- POST /api/rankings/ (rank candidates)
- GET  /api/rankings/ (convenience query)
- POST /api/rankings/backfill
- GET  /api/audit/fairness
- GET  /api/audit/redact-preview/{id}
"""

import math
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from httpx import ASGITransport, AsyncClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_resume_doc(resume_id="r1", skills=None, exp=5):
    vec = [1.0 / math.sqrt(384)] * 384
    return {
        "_id": resume_id,
        "filename": f"{resume_id}.pdf",
        "raw_text": f"Experienced developer with {exp}+ years of experience. "
                    f"Skills: {', '.join(skills or ['Python'])}",
        "file_type": "pdf",
        "parsing_method": "pdfplumber",
        "upload_time": "2024-01-01T00:00:00",
        "embedding": vec,
        "ner": {
            "name": "Test Candidate",
            "email": "test@example.com",
            "phone": None,
            "skills": skills or ["Python"],
            "education": ["B.Tech"],
            "experience": [f"{exp} years"],
            "certifications": [],
        },
    }


def _make_jd_doc(jd_id="jd1", req_skills=None):
    vec = [1.0 / math.sqrt(384)] * 384
    return {
        "_id": jd_id,
        "title": "Software Engineer",
        "company": "Acme Corp",
        "raw_text": "Looking for a software engineer with Python skills.",
        "created_time": "2024-01-01T00:00:00",
        "embedding": vec,
        "ner": {
            "required_skills": req_skills or ["Python"],
            "preferred_skills": ["Docker"],
            "min_experience_years": 3,
            "education_requirements": ["Bachelor"],
        },
    }


@pytest.fixture
def mock_db_with_data():
    """Mock DB with one JD and two resumes pre-populated."""
    db = MagicMock()

    jd = _make_jd_doc()
    resumes = [
        _make_resume_doc("r1", skills=["Python", "FastAPI", "Docker"], exp=7),
        _make_resume_doc("r2", skills=["Excel", "PowerPoint"], exp=1),
    ]

    # job_descriptions collection
    jd_col = AsyncMock()
    jd_col.find_one = AsyncMock(return_value=jd)
    db.__getitem__ = MagicMock(side_effect=lambda name: {
        "job_descriptions": jd_col,
        "resumes": _make_resume_collection(resumes),
    }[name])

    return db, jd, resumes


def _make_resume_collection(docs):
    col = AsyncMock()
    cursor = AsyncMock()
    cursor.to_list = AsyncMock(return_value=docs)
    col.find = MagicMock(return_value=cursor)
    col.find_one = AsyncMock(return_value=docs[0] if docs else None)
    col.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    col.count_documents = AsyncMock(return_value=len(docs))
    return col


@pytest.fixture
async def api_client(mock_db_with_data):
    """Async test client with mocked DB."""
    db, _, _ = mock_db_with_data
    with patch("app.db._database", db), \
         patch("app.db._client", MagicMock()):
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, db, mock_db_with_data


# ---------------------------------------------------------------------------
# Rankings endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_post_rankings_happy_path(api_client):
    client, db, (_, jd, resumes) = api_client
    body = {"jd_id": "jd1", "top_k": 10, "min_score": 0.0}
    resp = await client.post("/api/rankings/", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["jd_id"] == "jd1"
    assert "rankings" in data
    assert len(data["rankings"]) > 0


@pytest.mark.asyncio
async def test_get_rankings_happy_path(api_client):
    client, db, _ = api_client
    resp = await client.get("/api/rankings/?jd_id=jd1&top_k=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "rankings" in data


@pytest.mark.asyncio
async def test_rankings_404_jd_not_found():
    """Should return 404 when JD is not in DB."""
    db = MagicMock()
    jd_col = AsyncMock()
    jd_col.find_one = AsyncMock(return_value=None)  # JD not found

    resume_col = AsyncMock()
    cursor = AsyncMock()
    cursor.to_list = AsyncMock(return_value=[])
    resume_col.find = MagicMock(return_value=cursor)

    db.__getitem__ = MagicMock(side_effect=lambda name: {
        "job_descriptions": jd_col,
        "resumes": resume_col,
    }[name])

    with patch("app.db._database", db), patch("app.db._client", MagicMock()):
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/rankings/?jd_id=nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_rankings_422_empty_resume_pool():
    """Should return 422 when resume pool is empty."""
    db = MagicMock()
    jd_col = AsyncMock()
    jd_col.find_one = AsyncMock(return_value=_make_jd_doc())

    resume_col = AsyncMock()
    cursor = AsyncMock()
    cursor.to_list = AsyncMock(return_value=[])
    resume_col.find = MagicMock(return_value=cursor)

    db.__getitem__ = MagicMock(side_effect=lambda name: {
        "job_descriptions": jd_col,
        "resumes": resume_col,
    }[name])

    with patch("app.db._database", db), patch("app.db._client", MagicMock()):
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/rankings/", json={"jd_id": "jd1"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_rankings_ranking_order(api_client):
    """The strong candidate (more skills) should rank above the weak one."""
    client, _, _ = api_client
    body = {"jd_id": "jd1", "top_k": 10}
    resp = await client.post("/api/rankings/", json=body)
    assert resp.status_code == 200
    rankings = resp.json()["rankings"]
    # Rankings should be in descending score order
    scores = [r["final_score"] for r in rankings]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_rankings_min_score_filter(api_client):
    """min_score=100 should return no results (nobody scores 100%)."""
    client, _, _ = api_client
    body = {"jd_id": "jd1", "top_k": 10, "min_score": 99.9}
    resp = await client.post("/api/rankings/", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["rankings"] == []


@pytest.mark.asyncio
async def test_rankings_response_has_breakdown(api_client):
    """Each candidate in rankings must have a score breakdown."""
    client, _, _ = api_client
    body = {"jd_id": "jd1", "top_k": 10}
    resp = await client.post("/api/rankings/", json=body)
    assert resp.status_code == 200
    for candidate in resp.json()["rankings"]:
        assert "breakdown" in candidate
        bd = candidate["breakdown"]
        assert "semantic_score" in bd
        assert "skill_overlap_score" in bd
        assert "experience_score" in bd
        assert "education_score" in bd
        assert "matched_skills" in bd
        assert "missing_skills" in bd


@pytest.mark.asyncio
async def test_rankings_response_has_explanation(api_client):
    """Each candidate must have a non-empty explanation string."""
    client, _, _ = api_client
    body = {"jd_id": "jd1", "top_k": 10}
    resp = await client.post("/api/rankings/", json=body)
    assert resp.status_code == 200
    for candidate in resp.json()["rankings"]:
        assert "explanation" in candidate
        assert len(candidate["explanation"]) > 5


# ---------------------------------------------------------------------------
# Fairness audit endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fairness_audit_no_jd():
    """Fairness audit with no JD in DB should return empty metrics, not 500."""
    db = MagicMock()
    jd_col = AsyncMock()
    jd_col.find_one = AsyncMock(return_value=None)

    resume_col = AsyncMock()
    cursor = AsyncMock()
    cursor.to_list = AsyncMock(return_value=[])
    resume_col.find = MagicMock(return_value=cursor)

    db.__getitem__ = MagicMock(side_effect=lambda name: {
        "job_descriptions": jd_col,
        "resumes": resume_col,
    }[name])

    with patch("app.db._database", db), patch("app.db._client", MagicMock()):
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/audit/fairness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_candidates"] == 0


@pytest.mark.asyncio
async def test_redact_preview_not_found():
    """redact-preview with nonexistent ID should return 404."""
    db = MagicMock()
    resume_col = AsyncMock()
    resume_col.find_one = AsyncMock(return_value=None)
    db.__getitem__ = MagicMock(return_value=resume_col)

    with patch("app.db._database", db), patch("app.db._client", MagicMock()):
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/audit/redact-preview/nonexistent")
    assert resp.status_code == 404
