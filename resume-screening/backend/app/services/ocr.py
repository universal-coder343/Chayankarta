"""
OCR service for scanned PDFs and image files.
Uses pytesseract for text extraction and pdf2image for PDF-to-image conversion.
"""

import logging

from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)


def parse_image(filepath: str) -> str:
    """
    Extract text from an image file (PNG, JPG, TIFF, etc.) using Tesseract OCR.

    Preprocessing: convert to grayscale for better OCR accuracy.
    """
    logger.info("Running OCR on image: %s", filepath)
    try:
        img = Image.open(filepath)
        # Convert to grayscale for better OCR accuracy
        img = img.convert("L")
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as exc:
        logger.error("OCR failed on image '%s': %s", filepath, exc)
        raise


def parse_scanned_pdf(filepath: str) -> str:
    """
    Extract text from a scanned PDF by converting each page to an image,
    then running OCR on each page.

    Requires poppler-utils to be installed (for pdf2image).
    """
    logger.info("Running OCR on scanned PDF: %s", filepath)
    try:
        from pdf2image import convert_from_path

        # Convert PDF pages to images
        images = convert_from_path(filepath, dpi=300)
        text_parts: list[str] = []

        for i, page_img in enumerate(images):
            # Convert to grayscale
            page_img = page_img.convert("L")
            page_text = pytesseract.image_to_string(page_img)
            text_parts.append(page_text.strip())
            logger.debug("OCR page %d: %d chars", i + 1, len(page_text))

        full_text = "\n".join(text_parts).strip()
        logger.info("Scanned PDF OCR complete: %d pages, %d chars", len(images), len(full_text))
        return full_text

    except ImportError:
        logger.error("pdf2image is not installed. Install it with: pip install pdf2image")
        raise
    except Exception as exc:
        logger.error("OCR failed on scanned PDF '%s': %s", filepath, exc)
        raise
