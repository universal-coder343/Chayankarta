"""
Resume parser — detects file type and delegates to the appropriate extractor.
Supports text PDFs (pdfplumber), DOCX (python-docx), and images/scanned PDFs (OCR).
"""

import logging
import os
from dataclasses import dataclass

import pdfplumber
from docx import Document

from .ocr import parse_image, parse_scanned_pdf

logger = logging.getLogger(__name__)

# If pdfplumber extracts fewer characters than this, fall back to OCR
_MIN_TEXT_LENGTH = 50


@dataclass
class ParseResult:
    """Result of parsing a resume file."""

    raw_text: str
    parsing_method: str  # "pdfplumber", "python-docx", "ocr"
    file_type: str  # "pdf", "docx", "image"


def detect_file_type(filename: str) -> str:
    """Return a normalized file-type string based on extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        return "pdf"
    elif ext in (".docx", ".doc"):
        return "docx"
    elif ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
        return "image"
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def parse_resume(filepath: str, filename: str) -> ParseResult:
    """
    Parse a resume file and extract raw text.

    Dispatches to the right extractor based on file type.
    For PDFs, automatically falls back to OCR if extracted text is too short
    (indicating a scanned/image-based PDF).
    """
    file_type = detect_file_type(filename)
    logger.info("Parsing file '%s' (type=%s)", filename, file_type)

    if file_type == "pdf":
        return _parse_pdf(filepath)
    elif file_type == "docx":
        return _parse_docx(filepath)
    elif file_type == "image":
        return _parse_image_file(filepath)
    else:
        raise ValueError(f"Cannot parse file type: {file_type}")


def _parse_pdf(filepath: str) -> ParseResult:
    """Extract text from a PDF using pdfplumber, falling back to OCR."""
    text_parts: list[str] = []
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
    except Exception as exc:
        logger.warning("pdfplumber failed on '%s': %s — trying OCR", filepath, exc)
        return _parse_scanned_pdf_fallback(filepath)

    raw_text = "\n".join(text_parts).strip()

    # If we got very little text, it's probably a scanned PDF
    if len(raw_text) < _MIN_TEXT_LENGTH:
        logger.info("PDF text too short (%d chars) — falling back to OCR", len(raw_text))
        return _parse_scanned_pdf_fallback(filepath)

    logger.info("PDF parsed successfully via pdfplumber (%d chars)", len(raw_text))
    return ParseResult(raw_text=raw_text, parsing_method="pdfplumber", file_type="pdf")


def _parse_scanned_pdf_fallback(filepath: str) -> ParseResult:
    """OCR fallback for scanned PDFs."""
    raw_text = parse_scanned_pdf(filepath)
    return ParseResult(raw_text=raw_text, parsing_method="ocr", file_type="pdf")


def _parse_docx(filepath: str) -> ParseResult:
    """Extract text from a DOCX file using python-docx."""
    doc = Document(filepath)
    parts: list[str] = []

    # Extract paragraphs
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            parts.append(text)

    # Extract table contents
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                parts.append(row_text)

    raw_text = "\n".join(parts).strip()
    logger.info("DOCX parsed successfully (%d chars)", len(raw_text))
    return ParseResult(raw_text=raw_text, parsing_method="python-docx", file_type="docx")


def _parse_image_file(filepath: str) -> ParseResult:
    """Extract text from an image file using OCR."""
    raw_text = parse_image(filepath)
    logger.info("Image parsed via OCR (%d chars)", len(raw_text))
    return ParseResult(raw_text=raw_text, parsing_method="ocr", file_type="image")
