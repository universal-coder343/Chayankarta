"""
PII / Demographic Redaction Service — Milestone 5.

Strips personally identifiable and demographic information from resume
text *before* it is embedded or scored, reducing unconscious bias.

Redacted categories
-------------------
- PERSON names          → [CANDIDATE]
- Email addresses       → [EMAIL]
- Phone numbers         → [PHONE]
- Physical addresses    → [ADDRESS]
- Gender pronouns / titles (he/she/Mr/Ms …) → [GENDER_INDICATOR]
- Age / date-of-birth references → [AGE]
- Marital status        → [MARITAL_STATUS]
- Nationality / country of origin → [NATIONALITY]
- Religion / caste      → [RELIGION]
- Photo / LinkedIn / GitHub links → [LINK]
- (Optional) College / institution names → [INSTITUTION]

The *original* text is always preserved separately in MongoDB; only
the redacted copy is used for embedding / scoring.

Usage
-----
>>> from .redactor import redact_pii, RedactionResult
>>> result = redact_pii(raw_text)
>>> embedding_input = result.redacted_text
"""

import logging
import re
from dataclasses import dataclass, field

# Note: spaCy is NOT imported at module level here.
# It is loaded lazily inside _redact_spacy_entities() via `from .ner import get_nlp`
# to avoid triggering the Windows DLL load at import/collection time.

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Compiled regex patterns
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"[\w.+\-]+@[\w\-]+\.[\w.\-]+", re.IGNORECASE)

_PHONE_RE = re.compile(
    r"""
    (?:[\+]?(?:91|1|44|61|49|33|86|81)[\s\-]?)?   # optional country code
    (?:\(?\d{2,4}\)?[\s\-]?){2,4}                  # area + number blocks
    \d{2,4}                                         # final block
    """,
    re.VERBOSE,
)

_URL_RE = re.compile(
    r"https?://\S+|www\.\S+|linkedin\.com/\S*|github\.com/\S*",
    re.IGNORECASE,
)

# Street address patterns (number + street keywords)
_ADDRESS_RE = re.compile(
    r"\d+[\w\s,]*(?:street|st|avenue|ave|road|rd|lane|ln|drive|dr|"
    r"boulevard|blvd|nagar|colony|sector|plot|flat|apartment|apt|house|"
    r"block|layout|phase|wing)\b[\w\s,.-]*",
    re.IGNORECASE,
)

# Date-of-birth / age
_DOB_RE = re.compile(
    r"(?:date\s+of\s+birth|dob|born|age)\s*[:\-]?\s*"
    r"(?:\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4}|\d{1,2}\s+\w+\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})",
    re.IGNORECASE,
)
_AGE_RE = re.compile(
    r"\b(?:aged?|age)\s*[:\-]?\s*\d{1,3}\b",
    re.IGNORECASE,
)

# Gender pronouns and titles
_GENDER_RE = re.compile(
    r"\b(?:he|she|him|her|his|hers|himself|herself|"
    r"mr\.?|mrs\.?|ms\.?|miss|master|sir|madam|"
    r"male|female|man|woman|boy|girl|gentleman|lady)\b",
    re.IGNORECASE,
)

# Marital status
_MARITAL_RE = re.compile(
    r"\b(?:married|unmarried|single|divorced|widowed|separated|"
    r"marital\s+status|relationship\s+status)\b",
    re.IGNORECASE,
)

# Nationality / country of origin indicators
_NATIONALITY_RE = re.compile(
    r"\b(?:nationality|citizen(?:ship)?|country\s+of\s+origin|"
    r"resident\s+of|native\s+of|domicile)\s*[:\-]?\s*\w+",
    re.IGNORECASE,
)

# Religion / caste
_RELIGION_RE = re.compile(
    r"\b(?:religion|religious|faith|caste|community|denomination|"
    r"hindu|muslim|christian|sikh|jain|buddhist|jewish|protestant|catholic|"
    r"brahmin|kshatriya|sc|st|obc|general\s+category)\b",
    re.IGNORECASE,
)

# Common Indian/Western university keywords for optional institution redaction
_INSTITUTION_RE = re.compile(
    r"\b(?:university|institute|college|iit|nit|iiit|iim|bits|school\s+of|"
    r"faculty\s+of|campus|polytechnic|deemed)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Data class for the redaction result
# ---------------------------------------------------------------------------

@dataclass
class RedactionResult:
    """Holds both the original and the redacted resume text."""

    original_text: str
    redacted_text: str
    redacted_items: list[str] = field(default_factory=list)

    @property
    def redaction_count(self) -> int:
        return len(self.redacted_items)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def redact_pii(
    text: str,
    redact_institutions: bool = False,
) -> RedactionResult:
    """
    Redact PII and demographic information from resume text.

    Args:
        text               : Raw resume text.
        redact_institutions: If True, also redact college/university names.

    Returns:
        RedactionResult with original_text, redacted_text, redacted_items.
    """
    original = text
    redacted = text
    items: list[str] = []

    # 1. URLs / links (before email so we don't double-match)
    redacted, found = _apply_pattern(redacted, _URL_RE, "[LINK]")
    items.extend(found)

    # 2. Email
    redacted, found = _apply_pattern(redacted, _EMAIL_RE, "[EMAIL]")
    items.extend(found)

    # 3. Phone
    redacted, found = _apply_pattern(redacted, _PHONE_RE, "[PHONE]")
    items.extend(found)

    # 4. Physical addresses (before spaCy so we don't double-hit GPE)
    redacted, found = _apply_pattern(redacted, _ADDRESS_RE, "[ADDRESS]")
    items.extend(found)

    # 5. Date-of-birth / age
    redacted, found = _apply_pattern(redacted, _DOB_RE, "[AGE]")
    items.extend(found)
    redacted, found = _apply_pattern(redacted, _AGE_RE, "[AGE]")
    items.extend(found)

    # 6. Marital status
    redacted, found = _apply_pattern(redacted, _MARITAL_RE, "[MARITAL_STATUS]")
    items.extend(found)

    # 7. Nationality
    redacted, found = _apply_pattern(redacted, _NATIONALITY_RE, "[NATIONALITY]")
    items.extend(found)

    # 8. Religion / caste
    redacted, found = _apply_pattern(redacted, _RELIGION_RE, "[RELIGION]")
    items.extend(found)

    # 9. Gender indicators
    redacted, found = _apply_pattern(redacted, _GENDER_RE, "[GENDER_INDICATOR]")
    items.extend(found)

    # 10. spaCy NER — names (PERSON) and locations (GPE)
    redacted, found = _redact_spacy_entities(redacted)
    items.extend(found)

    # 11. Institutions (optional)
    if redact_institutions:
        redacted, found = _apply_pattern(redacted, _INSTITUTION_RE, "[INSTITUTION]")
        items.extend(found)

    logger.debug("Redacted %d PII items from resume text.", len(items))

    return RedactionResult(
        original_text=original,
        redacted_text=redacted,
        redacted_items=items,
    )


def detect_bias_indicators(text: str) -> list[str]:
    """
    Return a list of bias indicator categories detected in the text.
    Used for flagging resumes during the fairness audit.
    """
    indicators: list[str] = []

    if _GENDER_RE.search(text):
        indicators.append("gender_indicator")
    if _DOB_RE.search(text) or _AGE_RE.search(text):
        indicators.append("age_indicator")
    if _MARITAL_RE.search(text):
        indicators.append("marital_status")
    if _NATIONALITY_RE.search(text):
        indicators.append("nationality")
    if _RELIGION_RE.search(text):
        indicators.append("religion_caste")

    return indicators


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _apply_pattern(
    text: str,
    pattern: re.Pattern,
    placeholder: str,
) -> tuple[str, list[str]]:
    """Replace all matches of pattern with placeholder. Returns (new_text, found_items)."""
    found = pattern.findall(text)
    new_text = pattern.sub(placeholder, text)
    return new_text, [str(f) for f in found if str(f).strip()]


def _redact_spacy_entities(text: str) -> tuple[str, list[str]]:
    """
    Use spaCy NER to redact PERSON and GPE (location) entities.
    We load the same model used by ner.py (already cached).
    """
    try:
        from .ner import get_nlp
        nlp = get_nlp()
        doc = nlp(text)

        replacements: list[tuple[int, int, str]] = []
        found: list[str] = []

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                replacements.append((ent.start_char, ent.end_char, "[CANDIDATE]"))
                found.append(ent.text)
            elif ent.label_ == "GPE":
                # Only replace short GPE tokens (cities, states) — not long compound nouns
                if len(ent.text.split()) <= 3:
                    replacements.append((ent.start_char, ent.end_char, "[LOCATION]"))
                    found.append(ent.text)

        # Apply replacements in reverse order to preserve character offsets
        new_text = text
        for start, end, placeholder in sorted(replacements, key=lambda x: x[0], reverse=True):
            new_text = new_text[:start] + placeholder + new_text[end:]

        return new_text, found

    except Exception as exc:
        logger.warning("spaCy entity redaction failed: %s", exc)
        return text, []
