"""
PII Redactor — STUB for Phase 2 bias mitigation.

In Phase 2, this module will redact personally identifiable information
(name, gender indicators, age, ethnicity cues) from resume text before
scoring, to reduce unconscious bias in candidate ranking.
"""

import logging

logger = logging.getLogger(__name__)


def redact_pii(text: str) -> str:
    """
    Redact personally identifiable information from text.

    TODO (Phase 2):
    - Redact candidate names (replace with [CANDIDATE])
    - Remove gender pronouns and indicators
    - Redact age / date-of-birth references
    - Remove photo references
    - Optionally redact university names (for blind screening)

    Currently returns text unchanged.
    """
    logger.debug("redact_pii called — returning text unchanged (stub)")
    # Phase 2: implement PII redaction here
    return text


def detect_bias_indicators(text: str) -> list[str]:
    """
    Detect potential bias indicators in text.

    TODO (Phase 2):
    - Detect gendered language
    - Detect age-related information
    - Flag ethnicity / nationality mentions
    - Return list of detected bias flags

    Currently returns empty list.
    """
    logger.debug("detect_bias_indicators called — returning empty list (stub)")
    # Phase 2: implement bias detection here
    return []
