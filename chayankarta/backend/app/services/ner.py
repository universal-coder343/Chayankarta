"""
NER (Named Entity Recognition) and skills extraction service.

Hybrid pipeline:
1. spaCy NER (en_core_web_sm) — PERSON, ORG, DATE, GPE
2. PhraseMatcher — skills from skills_taxonomy.json (case-insensitive)
3. Regex — email, phone, education, certifications

Note on imports
---------------
spaCy and its sub-modules are imported *lazily* (inside functions) so that
the module can be collected by pytest even when the spaCy DLL cannot be
loaded (e.g. Windows Application Control Policy blocks ujson.dll). All
behaviour at runtime is identical to eager imports.
"""

import json
import logging
import os
import re
from functools import lru_cache

from ..models.resume import ResumeNER

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_PATTERN = re.compile(r"[\+]?[\d\s\-().]{7,15}")

EDUCATION_PATTERNS = re.compile(
    r"\b("
    r"B\.?Tech|B\.?E\.?|B\.?Sc|B\.?S\.?|B\.?A\.?|B\.?Com|BCA|BBA|"
    r"M\.?Tech|M\.?E\.?|M\.?Sc|M\.?S\.?|M\.?A\.?|M\.?Com|MCA|MBA|"
    r"Ph\.?D|Doctorate|"
    r"Bachelor(?:'?s)?|Master(?:'?s)?|Associate(?:'?s)?|Diploma|"
    r"High School|GED|"
    r"Computer Science|Information Technology|Electrical Engineering|"
    r"Mechanical Engineering|Data Science|Mathematics|Statistics|"
    r"Business Administration|Economics|Physics|Chemistry|Biology"
    r")\b",
    re.IGNORECASE,
)

EXPERIENCE_YEAR_PATTERN = re.compile(
    r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)?",
    re.IGNORECASE,
)

SECTION_HEADERS = re.compile(
    r"^(EXPERIENCE|WORK\s*EXPERIENCE|EMPLOYMENT|EDUCATION|SKILLS|"
    r"TECHNICAL\s*SKILLS|CERTIFICATIONS?|CERTIFICATES?|PROJECTS?|"
    r"SUMMARY|OBJECTIVE|PROFILE|ACHIEVEMENTS?|AWARDS?|"
    r"PUBLICATIONS?|LANGUAGES?|INTERESTS?|HOBBIES|REFERENCES?)\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# ---------------------------------------------------------------------------
# spaCy + PhraseMatcher setup
# ---------------------------------------------------------------------------
_TAXONOMY_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "skills_taxonomy.json")


@lru_cache(maxsize=1)
def _load_skills_list() -> list[str]:
    """Load and flatten the skills taxonomy JSON."""
    with open(_TAXONOMY_PATH, "r", encoding="utf-8") as f:
        taxonomy = json.load(f)

    skills: list[str] = []
    for category_skills in taxonomy.values():
        skills.extend(category_skills)

    logger.info("Loaded %d skills from taxonomy", len(skills))
    return skills


@lru_cache(maxsize=1)
def get_nlp():
    """Load the spaCy model and attach the skills PhraseMatcher component."""
    import spacy  # lazy import — avoids DLL load at module level
    from spacy.matcher import PhraseMatcher  # noqa: lazy

    nlp = spacy.load("en_core_web_sm")

    # Build PhraseMatcher with skills taxonomy
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    skills = _load_skills_list()
    patterns = list(nlp.pipe(skills))
    matcher.add("SKILL", patterns)

    # Store matcher on the nlp object for access in extraction
    nlp.meta["_skills_matcher"] = matcher
    logger.info("spaCy model loaded with PhraseMatcher (%d skill patterns)", len(patterns))
    return nlp


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------
def extract_entities(text: str, category: str | None = None) -> ResumeNER:
    """
    Extract named entities, skills, education, experience, and contact info
    from resume text.

    Args:
        text: Raw resume text.
        category: Optional category label (e.g. from Kaggle dataset).

    Returns:
        ResumeNER with all extracted fields.
    """
    from spacy.matcher import PhraseMatcher  # noqa: lazy
    from spacy.tokens import Span  # noqa: lazy

    nlp = get_nlp()
    doc = nlp(text)
    matcher: PhraseMatcher = nlp.meta["_skills_matcher"]

    # --- Skills via PhraseMatcher ---
    matches = matcher(doc)
    skill_spans = [Span(doc, start, end, label="SKILL") for _, start, end in matches]
    skills = sorted(set(span.text for span in skill_spans))

    # --- Contact info via regex ---
    emails = EMAIL_PATTERN.findall(text)
    phones = PHONE_PATTERN.findall(text)
    # Clean phone numbers
    phones = [p.strip() for p in phones if len(re.sub(r"\D", "", p)) >= 7]

    # --- Name: first PERSON entity ---
    name = None
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            break

    # --- Education via regex ---
    education_matches = EDUCATION_PATTERNS.findall(text)
    education = sorted(set(education_matches))

    # --- Experience: extract section text between EXPERIENCE and next header ---
    experience = _extract_section(text, "EXPERIENCE")
    if not experience:
        experience = _extract_section(text, "WORK EXPERIENCE")

    # --- Certifications ---
    certifications = _extract_section(text, "CERTIFICATION")
    if not certifications:
        certifications = _extract_section(text, "CERTIFICATE")

    return ResumeNER(
        name=name,
        email=emails[0] if emails else None,
        phone=phones[0] if phones else None,
        skills=skills,
        education=education,
        experience=experience,
        certifications=certifications,
        category=category,
    )


def _extract_section(text: str, section_name: str) -> list[str]:
    """
    Extract bullet points / lines from a resume section.

    Finds the section header and collects lines until the next section header
    or end of text.
    """
    lines = text.split("\n")
    in_section = False
    section_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if this is a section header
        if SECTION_HEADERS.match(stripped):
            if in_section:
                break  # End of our section
            if section_name.upper() in stripped.upper():
                in_section = True
                continue

        if in_section:
            section_lines.append(stripped)

    return section_lines
