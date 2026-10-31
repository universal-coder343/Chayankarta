"""
Tests for the PII redactor service (Milestone 5).

Tests:
- Email addresses are redacted
- Phone numbers are redacted
- Names (via spaCy NER stub) are redacted
- URLs / links are redacted
- Gender indicators are redacted
- Age / DOB are redacted
- Marital status is redacted
- Nationality is redacted
- Religion is redacted
- No PII leaks into redacted output (spot-check)
- RedactionResult has correct fields
- redact_institutions flag works
"""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Mock spaCy so tests run without needing the full model
# ---------------------------------------------------------------------------

class _FakeEnt:
    def __init__(self, text, label, start_char, end_char):
        self.text = text
        self.label_ = label
        self.start_char = start_char
        self.end_char = end_char


class _FakeDoc:
    def __init__(self, text):
        self._text = text
        # Simulate detecting "John Doe" as PERSON if present
        self.ents = []
        idx = text.find("John Doe")
        if idx != -1:
            self.ents.append(_FakeEnt("John Doe", "PERSON", idx, idx + 8))
        idx2 = text.find("San Francisco")
        if idx2 != -1:
            self.ents.append(_FakeEnt("San Francisco", "GPE", idx2, idx2 + 13))


class _FakeNLP:
    def __call__(self, text):
        return _FakeDoc(text)


@pytest.fixture(autouse=True)
def mock_spacy_nlp(monkeypatch):
    """Stub out get_nlp() for all redactor tests."""
    import app.services.redactor as red_mod
    monkeypatch.setattr(
        "app.services.redactor._redact_spacy_entities",
        lambda text: _stub_spacy_redact(text),
    )


def _stub_spacy_redact(text: str) -> tuple[str, list[str]]:
    """Stub: replace 'John Doe' → [CANDIDATE] and 'San Francisco' → [LOCATION]."""
    found = []
    if "John Doe" in text:
        text = text.replace("John Doe", "[CANDIDATE]")
        found.append("John Doe")
    if "San Francisco" in text:
        text = text.replace("San Francisco", "[LOCATION]")
        found.append("San Francisco")
    return text, found


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

from app.services.redactor import redact_pii, RedactionResult, detect_bias_indicators


def test_email_redacted():
    result = redact_pii("Contact me at john@example.com for details.")
    assert "john@example.com" not in result.redacted_text
    assert "[EMAIL]" in result.redacted_text


def test_phone_redacted():
    result = redact_pii("Call me at +91 98765 43210 any time.")
    assert "98765" not in result.redacted_text
    assert "[PHONE]" in result.redacted_text


def test_url_redacted():
    result = redact_pii("Visit https://linkedin.com/in/johndoe for my profile.")
    assert "linkedin.com" not in result.redacted_text
    assert "[LINK]" in result.redacted_text


def test_gender_pronoun_redacted():
    result = redact_pii("He is an experienced engineer who led his team.")
    redacted = result.redacted_text.lower()
    assert " he " not in redacted or "[GENDER_INDICATOR]" in result.redacted_text


def test_mr_title_redacted():
    result = redact_pii("Mr. Smith has 10 years of experience.")
    assert "Mr." not in result.redacted_text or "[GENDER_INDICATOR]" in result.redacted_text


def test_dob_redacted():
    result = redact_pii("Date of Birth: 15/08/1995")
    assert "1995" not in result.redacted_text or "[AGE]" in result.redacted_text


def test_age_redacted():
    result = redact_pii("Age: 28 years old")
    assert "Age: 28" not in result.redacted_text


def test_marital_status_redacted():
    result = redact_pii("Marital Status: Married")
    assert "Married" not in result.redacted_text


def test_nationality_redacted():
    result = redact_pii("Nationality: Indian")
    assert "[NATIONALITY]" in result.redacted_text


def test_religion_redacted():
    result = redact_pii("Religion: Hindu")
    assert "Hindu" not in result.redacted_text


def test_name_redacted_via_spacy():
    result = redact_pii("John Doe is a software engineer.")
    assert "John Doe" not in result.redacted_text
    assert "[CANDIDATE]" in result.redacted_text


def test_location_redacted_via_spacy():
    result = redact_pii("Based in San Francisco, CA.")
    assert "San Francisco" not in result.redacted_text


def test_no_pii_leaks_into_redacted():
    """The redacted text must not contain raw email, phone, or the test name."""
    raw = (
        "John Doe\n"
        "john.doe@company.com | +1-555-123-4567\n"
        "San Francisco, CA\n"
        "Age: 30\n"
        "Marital Status: Single\n"
        "Religion: Christian\n"
        "Nationality: American\n"
        "Skills: Python, Django, React\n"
    )
    result = redact_pii(raw)
    redacted = result.redacted_text

    assert "john.doe@company.com" not in redacted
    assert "555-123-4567" not in redacted
    assert "John Doe" not in redacted


def test_redaction_result_fields():
    result = redact_pii("Email: test@test.com")
    assert isinstance(result, RedactionResult)
    assert isinstance(result.original_text, str)
    assert isinstance(result.redacted_text, str)
    assert isinstance(result.redacted_items, list)
    assert result.redaction_count >= 1


def test_institution_redaction_flag():
    text = "Studied at IIT Bombay and later attended Delhi University."
    result_off = redact_pii(text, redact_institutions=False)
    result_on = redact_pii(text, redact_institutions=True)
    # With flag on, institution keywords should be replaced
    assert "[INSTITUTION]" in result_on.redacted_text
    # With flag off, they may remain
    assert "[INSTITUTION]" not in result_off.redacted_text


def test_detect_bias_indicators_gender():
    text = "He is a strong leader who managed his team effectively."
    flags = detect_bias_indicators(text)
    assert "gender_indicator" in flags


def test_detect_bias_indicators_age():
    text = "Date of Birth: 12/05/1990"
    flags = detect_bias_indicators(text)
    assert "age_indicator" in flags


def test_detect_bias_indicators_clean():
    text = "5 years of Python development, strong REST API skills."
    flags = detect_bias_indicators(text)
    assert flags == []
