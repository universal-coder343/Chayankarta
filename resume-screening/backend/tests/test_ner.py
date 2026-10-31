"""
Tests for the NER and skills extraction service.
"""

import importlib.util
import pytest

from app.services.ner import extract_entities, EMAIL_PATTERN, PHONE_PATTERN

# Skip tests that require the spaCy model when spaCy (or its native DLLs)
# cannot be loaded.  On this machine the Windows Application Control Policy
# blocks torch_python.dll which thinc (spaCy's backend) tries to load.
spacy_available: bool = False
try:
    import spacy  # noqa: F401
    spacy_available = True
except Exception:
    pass

_skip_no_spacy = pytest.mark.skipif(
    not spacy_available,
    reason="spaCy (or its native DLLs) not available in this environment",
)

class TestRegexPatterns:
    """Tests for regex extractors."""

    def test_email_extraction(self):
        emails = EMAIL_PATTERN.findall("Contact me at john@example.com or jane.doe@company.co.uk")
        assert "john@example.com" in emails
        assert "jane.doe@company.co.uk" in emails

    def test_phone_extraction(self):
        phones = PHONE_PATTERN.findall("Call +1-555-0101 or (555) 123-4567")
        # Filter to valid-length phone numbers
        cleaned = [p.strip() for p in phones if len(p.strip().replace(" ", "").replace("-", "")) >= 7]
        assert len(cleaned) >= 1

    def test_no_email_in_plain_text(self):
        emails = EMAIL_PATTERN.findall("Hello world, no email here.")
        assert len(emails) == 0


class TestEntityExtraction:
    """Tests for the full NER pipeline (require spaCy + en_core_web_sm)."""

    @_skip_no_spacy
    def test_extracts_skills(self, sample_resume_text):
        """Should extract known skills from the taxonomy."""
        result = extract_entities(sample_resume_text)
        skills_lower = [s.lower() for s in result.skills]

        assert "python" in skills_lower
        assert "react" in skills_lower
        assert "docker" in skills_lower
        assert "aws" in skills_lower

    @_skip_no_spacy
    def test_extracts_email(self, sample_resume_text):
        """Should extract the email address."""
        result = extract_entities(sample_resume_text)
        assert result.email == "john.doe@example.com"

    @_skip_no_spacy
    def test_extracts_phone(self, sample_resume_text):
        """Should extract the phone number."""
        result = extract_entities(sample_resume_text)
        assert result.phone is not None
        assert "555" in result.phone

    @_skip_no_spacy
    def test_extracts_education(self, sample_resume_text):
        """Should detect education keywords."""
        result = extract_entities(sample_resume_text)
        education_lower = [e.lower() for e in result.education]
        # Should find B.S. or Computer Science
        assert any("computer science" in e or "b.s" in e for e in education_lower)

    @_skip_no_spacy
    def test_skills_case_insensitive(self):
        """PhraseMatcher should match skills regardless of case."""
        text = "I know PYTHON, javascript, and reAcT very well."
        result = extract_entities(text)
        skills_lower = [s.lower() for s in result.skills]
        assert "python" in skills_lower
        assert "javascript" in skills_lower
        assert "react" in skills_lower

    @_skip_no_spacy
    def test_category_passthrough(self, sample_resume_text):
        """Category from Kaggle dataset should be passed through."""
        result = extract_entities(sample_resume_text, category="Information-Technology")
        assert result.category == "Information-Technology"

    @_skip_no_spacy
    def test_empty_text(self):
        """Should handle empty text without errors."""
        result = extract_entities("")
        assert result.skills == []
        assert result.email is None
        assert result.name is None


class TestJDParser:
    """Tests for the job description parser (require spaCy + en_core_web_sm)."""

    @_skip_no_spacy
    def test_extracts_required_skills(self, sample_jd_text):
        from app.services.jd_parser import parse_job_description

        result = parse_job_description(sample_jd_text)
        all_skills = result.required_skills + result.preferred_skills
        skills_lower = [s.lower() for s in all_skills]

        assert "javascript" in skills_lower
        assert "react" in skills_lower
        assert "python" in skills_lower

    @_skip_no_spacy
    def test_classifies_preferred_skills(self, sample_jd_text):
        from app.services.jd_parser import parse_job_description

        result = parse_job_description(sample_jd_text)
        preferred_lower = [s.lower() for s in result.preferred_skills]

        # Kubernetes and AWS are listed under "Nice to Have"
        assert "kubernetes" in preferred_lower or "aws" in preferred_lower

    @_skip_no_spacy
    def test_extracts_experience_years(self, sample_jd_text):
        from app.services.jd_parser import parse_job_description

        result = parse_job_description(sample_jd_text)
        assert result.min_experience_years == 3

    @_skip_no_spacy
    def test_extracts_education(self, sample_jd_text):
        from app.services.jd_parser import parse_job_description

        result = parse_job_description(sample_jd_text)
        edu_lower = [e.lower() for e in result.education_requirements]
        assert any("computer science" in e or "bachelor" in e for e in edu_lower)
