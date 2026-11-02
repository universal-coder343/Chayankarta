"""
Tests for the Fairness Audit service (Milestone 5).

Tests:
- _infer_groups correctly assigns gender/institution/unknown labels
- Disparate impact ratio computed correctly (min/max selection rates)
- 4/5 rule pass/fail logic
- score_delta_redaction is mean absolute difference
- FairnessAuditResponse fields are present and typed correctly
- Audit returns empty metrics when no JD or resumes found
- Audit with only one group returns DI ratio = None (insufficient diversity)
"""

import math
import statistics

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_resume(raw_text: str, skills=None, education=None):
    """Minimal resume document dict."""
    vec = [1.0 / math.sqrt(384)] * 384
    return {
        "_id": "r-test",
        "filename": "test.pdf",
        "raw_text": raw_text,
        "embedding": vec,
        "ner": {
            "name": None,
            "skills": skills or [],
            "education": education or ["B.Tech"],
            "experience": [],
        },
    }


def _make_jd():
    vec = [1.0 / math.sqrt(384)] * 384
    return {
        "_id": "jd-test",
        "title": "Software Engineer",
        "raw_text": "Looking for Python developer.",
        "embedding": vec,
        "ner": {
            "required_skills": ["Python"],
            "preferred_skills": [],
            "min_experience_years": 2,
            "education_requirements": ["Bachelor"],
        },
    }


# ---------------------------------------------------------------------------
# _infer_groups -- pure function, no DB/model needed
# ---------------------------------------------------------------------------

from app.services.fairness import _infer_groups


class TestInferGroups:
    """Unit tests for the group-label inference heuristic."""

    def test_male_pronoun_detected(self):
        docs = [_make_resume("He is a senior engineer. His leadership is excellent.")]
        labels = _infer_groups(docs)
        assert labels[0] == "gender_male_proxy"

    def test_female_pronoun_detected(self):
        docs = [_make_resume("She leads a team of 10. Her background is in ML.")]
        labels = _infer_groups(docs)
        assert labels[0] == "gender_female_proxy"

    def test_mr_title_detected_as_male(self):
        docs = [_make_resume("Mr. Smith has extensive backend experience.")]
        labels = _infer_groups(docs)
        assert labels[0] == "gender_male_proxy"

    def test_ms_title_detected_as_female(self):
        docs = [_make_resume("Ms. Sharma brings 4 years of DevOps experience.")]
        labels = _infer_groups(docs)
        assert labels[0] == "gender_female_proxy"

    def test_tier1_institution_in_education_field(self):
        docs = [_make_resume(
            "Python developer with 5 years experience.",
            education=["B.Tech -- IIT Bombay, 2018"],
        )]
        labels = _infer_groups(docs)
        # No gender pronouns -> falls through to institution tier
        assert labels[0] == "institution_tier1"

    def test_tier2_institution_in_education_field(self):
        docs = [_make_resume(
            "Java developer.",
            education=["B.Tech -- Delhi University, 2020"],
        )]
        labels = _infer_groups(docs)
        assert labels[0] == "institution_tier2"

    def test_unknown_fallback(self):
        docs = [_make_resume("Experienced developer with 5 years of Python.")]
        labels = _infer_groups(docs)
        assert labels[0] == "unknown"

    def test_multiple_docs_independent(self):
        docs = [
            _make_resume("He is a backend engineer."),
            _make_resume("She specializes in frontend development."),
            _make_resume("5 years Python, Django, REST APIs."),
        ]
        labels = _infer_groups(docs)
        assert labels[0] == "gender_male_proxy"
        assert labels[1] == "gender_female_proxy"
        assert labels[2] == "unknown"

    def test_equal_pronouns_not_gender_classified(self):
        """Equal he/she counts -> not classified as either gender."""
        docs = [_make_resume("He said she did great work.")]
        labels = _infer_groups(docs)
        # Equal counts -> not gender-classified; falls to institution/unknown
        assert labels[0] in ("institution_tier1", "institution_tier2", "unknown")


# ---------------------------------------------------------------------------
# Disparate impact ratio logic
# ---------------------------------------------------------------------------

from app.models.ranking import GroupMetrics, FairnessAuditResponse


class TestDisparateImpact:
    """Unit tests for disparate impact ratio computation."""

    def _compute_di(self, rates):
        """Helper: compute DI from a dict of {label: rate}."""
        if len(rates) < 2:
            return None
        max_rate = max(rates.values())
        min_rate = min(rates.values())
        if max_rate == 0:
            return None
        return min_rate / max_rate

    def test_perfect_equality(self):
        di = self._compute_di({"a": 0.5, "b": 0.5})
        assert di == pytest.approx(1.0)
        assert di >= 0.8

    def test_fails_four_fifths(self):
        di = self._compute_di({"majority": 1.0, "minority": 0.2})
        assert di == pytest.approx(0.2)
        assert di < 0.8

    def test_exactly_point_eight_passes(self):
        di = self._compute_di({"a": 0.8, "b": 1.0})
        assert di == pytest.approx(0.8)
        assert di >= 0.8  # passes

    def test_none_when_max_rate_zero(self):
        di = self._compute_di({"a": 0.0, "b": 0.0})
        assert di is None

    def test_none_with_single_group(self):
        di = self._compute_di({"only_group": 0.6})
        assert di is None  # need >= 2 groups


# ---------------------------------------------------------------------------
# Score delta calculation
# ---------------------------------------------------------------------------

class TestScoreDelta:
    """Tests for score_delta_redaction calculation."""

    def test_zero_delta_when_identical(self):
        raw = [60.0, 70.0, 55.0]
        redacted = [60.0, 70.0, 55.0]
        delta = statistics.mean(abs(r - ro) for r, ro in zip(redacted, raw))
        assert delta == pytest.approx(0.0)

    def test_non_zero_delta(self):
        raw = [60.0, 70.0, 80.0]
        redacted = [58.0, 67.0, 75.0]
        delta = statistics.mean(abs(r - ro) for r, ro in zip(redacted, raw))
        assert delta == pytest.approx((2.0 + 3.0 + 5.0) / 3)

    def test_delta_always_non_negative(self):
        """Delta is a mean ABSOLUTE difference."""
        raw = [50.0, 60.0, 70.0]
        redacted = [55.0, 55.0, 65.0]
        delta = statistics.mean(abs(r - ro) for r, ro in zip(redacted, raw))
        assert delta >= 0.0


# ---------------------------------------------------------------------------
# FairnessAuditResponse Pydantic model
# ---------------------------------------------------------------------------

class TestFairnessAuditResponseModel:
    """Unit tests for the FairnessAuditResponse Pydantic model."""

    def test_empty_response_valid(self):
        resp = FairnessAuditResponse(
            threshold=60.0,
            total_candidates=0,
            groups=[],
            summary="No data.",
            redaction_enabled=False,
        )
        assert resp.total_candidates == 0
        assert resp.groups == []
        assert resp.disparate_impact_ratio is None
        assert resp.passes_four_fifths_rule is None
        assert resp.score_delta_redaction is None

    def test_full_response_valid(self):
        groups = [
            GroupMetrics(group_label="gender_male_proxy", count=5,
                         mean_score=72.0, std_score=8.0, selection_rate=0.8),
            GroupMetrics(group_label="gender_female_proxy", count=5,
                         mean_score=65.0, std_score=10.0, selection_rate=0.6),
        ]
        resp = FairnessAuditResponse(
            threshold=60.0,
            total_candidates=10,
            groups=groups,
            disparate_impact_ratio=0.75,
            passes_four_fifths_rule=False,
            score_delta_redaction=3.5,
            redaction_enabled=True,
            summary="DI: 0.75 [FAIL]",
        )
        assert resp.disparate_impact_ratio == pytest.approx(0.75)
        assert resp.passes_four_fifths_rule is False
        assert resp.score_delta_redaction == pytest.approx(3.5)
        assert len(resp.groups) == 2

    def test_passes_four_fifths_true(self):
        resp = FairnessAuditResponse(
            threshold=60.0,
            total_candidates=10,
            groups=[],
            disparate_impact_ratio=0.85,
            passes_four_fifths_rule=True,
            redaction_enabled=True,
            summary="PASS",
        )
        assert resp.passes_four_fifths_rule is True


# ---------------------------------------------------------------------------
# _build_summary helper
# ---------------------------------------------------------------------------

from app.services.fairness import _build_summary


class TestBuildSummary:

    def test_summary_with_di_pass(self):
        groups = [
            GroupMetrics(group_label="a", count=5, mean_score=70.0,
                         std_score=5.0, selection_rate=0.9),
            GroupMetrics(group_label="b", count=5, mean_score=68.0,
                         std_score=5.0, selection_rate=0.8),
        ]
        summary = _build_summary(di_ratio=0.89, passes=True,
                                  score_delta=None, groups=groups)
        assert "PASS" in summary
        assert "0.89" in summary

    def test_summary_with_di_fail_and_delta(self):
        groups = [
            GroupMetrics(group_label="x", count=5, mean_score=70.0,
                         std_score=5.0, selection_rate=1.0),
            GroupMetrics(group_label="y", count=5, mean_score=40.0,
                         std_score=5.0, selection_rate=0.2),
        ]
        summary = _build_summary(di_ratio=0.2, passes=False,
                                  score_delta=4.5, groups=groups)
        assert "FAIL" in summary
        assert "4.5" in summary

    def test_summary_no_di(self):
        """Single-group audit -> DI not computable."""
        groups = [
            GroupMetrics(group_label="unknown", count=10, mean_score=60.0,
                         std_score=8.0, selection_rate=0.5),
        ]
        summary = _build_summary(di_ratio=None, passes=None,
                                  score_delta=None, groups=groups)
        # Should mention insufficient diversity
        assert len(summary) > 0  # non-empty
        assert "unknown" in summary.lower() or "insufficient" in summary.lower()


# ---------------------------------------------------------------------------
# Async integration: compute_fairness_audit with mocked DB + embedder
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fairness_audit_no_jd_returns_empty():
    """compute_fairness_audit returns empty response when no JD in DB."""
    from app.services.fairness import compute_fairness_audit

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

    result = await compute_fairness_audit(db, jd_id=None, threshold=60.0)
    assert result.total_candidates == 0
    assert result.groups == []
    assert result.disparate_impact_ratio is None


@pytest.mark.asyncio
async def test_fairness_audit_no_resumes_returns_empty():
    """compute_fairness_audit returns empty response when no resumes in DB."""
    from app.services.fairness import compute_fairness_audit

    jd = _make_jd()
    db = MagicMock()
    jd_col = AsyncMock()
    jd_col.find_one = AsyncMock(return_value=jd)
    resume_col = AsyncMock()
    cursor = AsyncMock()
    cursor.to_list = AsyncMock(return_value=[])
    resume_col.find = MagicMock(return_value=cursor)

    db.__getitem__ = MagicMock(side_effect=lambda name: {
        "job_descriptions": jd_col,
        "resumes": resume_col,
    }[name])

    result = await compute_fairness_audit(db, jd_id="jd-test", threshold=60.0)
    assert result.total_candidates == 0
    assert result.groups == []


@pytest.mark.asyncio
async def test_fairness_audit_single_group_no_di():
    """
    All 'unknown' group resumes -> DI ratio is None
    (cannot compute disparate impact with < 2 groups).
    """
    from app.services.fairness import compute_fairness_audit

    # No gender/institution proxies -> both 'unknown'
    resumes = [
        _make_resume("5 years Python backend development, REST APIs, SQL."),
        _make_resume("Java developer with 3 years Spring Boot experience."),
    ]
    jd = _make_jd()

    db = MagicMock()
    jd_col = AsyncMock()
    jd_col.find_one = AsyncMock(return_value=jd)
    resume_col = AsyncMock()
    cursor = AsyncMock()
    cursor.to_list = AsyncMock(return_value=resumes)
    resume_col.find = MagicMock(return_value=cursor)
    resume_col.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    db.__getitem__ = MagicMock(side_effect=lambda name: {
        "job_descriptions": jd_col,
        "resumes": resume_col,
    }[name])

    vec = [1.0 / math.sqrt(384)] * 384
    with patch("app.services.fairness.embed_texts", return_value=[vec, vec, vec]):
        result = await compute_fairness_audit(db, jd_id="jd-test", threshold=60.0)

    assert result.total_candidates == 2
    assert result.disparate_impact_ratio is None
    assert result.passes_four_fifths_rule is None


@pytest.mark.asyncio
async def test_fairness_audit_two_groups_di_computed():
    """
    Male-proxy + female-proxy resumes -> DI ratio computed.
    With threshold=0 and both groups scoring >0 -> DI = 1.0 (PASS).
    """
    from app.services.fairness import compute_fairness_audit

    resumes = [
        _make_resume("He is a senior Python developer with 6 years. His code is clean.", ["Python"]),
        _make_resume("She leads an ML team. Her Python expertise is outstanding.", ["Python"]),
    ]
    jd = _make_jd()

    db = MagicMock()
    jd_col = AsyncMock()
    jd_col.find_one = AsyncMock(return_value=jd)
    resume_col = AsyncMock()
    cursor = AsyncMock()
    cursor.to_list = AsyncMock(return_value=resumes)
    resume_col.find = MagicMock(return_value=cursor)
    resume_col.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    db.__getitem__ = MagicMock(side_effect=lambda name: {
        "job_descriptions": jd_col,
        "resumes": resume_col,
    }[name])

    vec = [1.0 / math.sqrt(384)] * 384
    with patch("app.services.fairness.embed_texts", return_value=[vec, vec, vec]):
        result = await compute_fairness_audit(db, jd_id="jd-test", threshold=0.0)

    assert result.total_candidates == 2
    assert len(result.groups) == 2
    # threshold=0 -> everyone selected -> DI = 1.0
    assert result.disparate_impact_ratio is not None
    assert result.disparate_impact_ratio == pytest.approx(1.0)
    assert result.passes_four_fifths_rule is True
