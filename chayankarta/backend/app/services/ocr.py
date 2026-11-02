"""
OCR service for scanned PDFs and image files.
Uses pytesseract for text extraction and pdf2image for PDF-to-image conversion.
"""

import logging

from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

logger = logging.getLogger(__name__)

# Tesseract config: single block of text (PSM 6), English only
# OEM 3 = default (LSTM + legacy), PSM 6 = uniform block of text
_TESS_CONFIG = "--oem 3 --psm 6 -l eng"


def _preprocess_image(img: Image.Image) -> Image.Image:
    """
    Preprocess an image for better Tesseract OCR accuracy.

    Steps:
    1. Convert to RGBA then paste on white background (removes transparency artefacts)
    2. Convert to grayscale
    3. Scale up small images (Tesseract works best at ~300 DPI / 2000+ px wide)
    4. Sharpen + boost contrast
    5. Apply a mild median filter to reduce noise
    """
    # Flatten transparency onto white background
    if img.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[3])
        img = background

    # Convert to grayscale
    img = img.convert("L")

    # Upscale if the image is small — Tesseract accuracy degrades below ~1500 px wide
    min_width = 1800
    if img.width < min_width:
        scale = min_width / img.width
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.LANCZOS)
        logger.debug("Upscaled image to %s for OCR", new_size)

    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)

    # Boost contrast
    img = ImageEnhance.Contrast(img).enhance(2.0)

    # Mild median filter to reduce salt-and-pepper noise
    img = img.filter(ImageFilter.MedianFilter(size=3))

    return img


def parse_image(filepath: str) -> str:
    """
    Extract text from an image file (PNG, JPG, TIFF, etc.) using Tesseract OCR.

    Applies multi-step preprocessing (grayscale, upscale, sharpen, contrast)
    before passing to Tesseract for best accuracy on resume scans.
    """
    logger.info("Running OCR on image: %s", filepath)
    try:
        img = Image.open(filepath)
        img = _preprocess_image(img)
        text = pytesseract.image_to_string(img, config=_TESS_CONFIG)
        result = text.strip()
        logger.info("Image OCR complete: %d chars extracted", len(result))
        return result
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

        # Convert PDF pages to images at 300 DPI
        images = convert_from_path(filepath, dpi=300)
        text_parts: list[str] = []

        for i, page_img in enumerate(images):
            page_img = _preprocess_image(page_img)
            page_text = pytesseract.image_to_string(page_img, config=_TESS_CONFIG)
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
