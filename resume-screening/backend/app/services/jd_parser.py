"""
Job Description parser — extracts required/preferred skills,
experience requirements, and education from JD text.
"""

import logging
import re

from ..models.job_description import JobDescriptionNER
from .ner import get_nlp, EDUCATION_PATTERNS, EXPERIENCE_YEAR_PATTERN

logger = logging.getLogger(__name__)

# Patterns to distinguish required vs preferred
REQUIRED_KEYWORDS = re.compile(
    r"\b(required|must\s+have|mandatory|essential|minimum|need)\b",
    re.IGNORECASE,
)
PREFERRED_KEYWORDS = re.compile(
    r"\b(preferred|nice\s+to\s+have|bonus|desired|optional|plus|advantageous)\b",
    re.IGNORECASE,
)


def parse_job_description(text: str) -> JobDescriptionNER:
    """
    Extract structured requirements from a job description.

    Uses the same skills PhraseMatcher as the resume NER, plus regex for
    experience years and education requirements.

    Args:
        text: Raw job description text.

    Returns:
        JobDescriptionNER with extracted fields.
    """
    nlp = get_nlp()
    from spacy.matcher import PhraseMatcher
    matcher: PhraseMatcher = nlp.meta["_skills_matcher"]

    doc = nlp(text)

    # --- Skills via PhraseMatcher ---
    matches = matcher(doc)
    all_skills = sorted(set(doc[start:end].text for _, start, end in matches))

    # --- Classify skills as required vs preferred using sentence context ---
    required_skills: list[str] = []
    preferred_skills: list[str] = []

    for skill in all_skills:
        # Find sentences containing this skill
        skill_lower = skill.lower()
        classified = False
        for sent in doc.sents:
            if skill_lower in sent.text.lower():
                sent_text = sent.text
                if PREFERRED_KEYWORDS.search(sent_text):
                    preferred_skills.append(skill)
                    classified = True
                    break
                elif REQUIRED_KEYWORDS.search(sent_text):
                    required_skills.append(skill)
                    classified = True
                    break

        if not classified:
            # Default: treat as required
            required_skills.append(skill)

    # --- Experience years ---
    exp_matches = EXPERIENCE_YEAR_PATTERN.findall(text)
    min_experience = None
    if exp_matches:
        # Take the smallest mentioned year requirement
        years = [int(y) for y in exp_matches if y.isdigit()]
        if years:
            min_experience = min(years)

    # --- Education ---
    education_matches = EDUCATION_PATTERNS.findall(text)
    education = sorted(set(education_matches))

    logger.info(
        "JD parsed: %d required skills, %d preferred skills, min_exp=%s",
        len(required_skills),
        len(preferred_skills),
        min_experience,
    )

    return JobDescriptionNER(
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        min_experience_years=min_experience,
        education_requirements=education,
    )
