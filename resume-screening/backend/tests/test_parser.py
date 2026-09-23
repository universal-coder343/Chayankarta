"""
Tests for the resume parsing services (parser.py, ocr.py).
"""

import os
import tempfile
import textwrap

import pytest


class TestDetectFileType:
    """Tests for parser.detect_file_type()."""

    def test_pdf(self):
        from app.services.parser import detect_file_type
        assert detect_file_type("resume.pdf") == "pdf"

    def test_docx(self):
        from app.services.parser import detect_file_type
        assert detect_file_type("resume.docx") == "docx"

    def test_doc(self):
        from app.services.parser import detect_file_type
        assert detect_file_type("resume.doc") == "docx"

    def test_png(self):
        from app.services.parser import detect_file_type
        assert detect_file_type("resume.png") == "image"

    def test_jpg(self):
        from app.services.parser import detect_file_type
        assert detect_file_type("resume.jpg") == "image"

    def test_unsupported(self):
        from app.services.parser import detect_file_type
        with pytest.raises(ValueError, match="Unsupported file type"):
            detect_file_type("resume.xyz")


class TestDocxParsing:
    """Tests for DOCX parsing."""

    def test_parse_simple_docx(self):
        """Parse a simple DOCX and verify text extraction."""
        from docx import Document as DocxDocument
        from app.services.parser import parse_resume

        # Create a temp DOCX
        doc = DocxDocument()
        doc.add_paragraph("John Doe")
        doc.add_paragraph("Software Engineer")
        doc.add_paragraph("Skills: Python, JavaScript, React")

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            doc.save(f.name)
            temp_path = f.name

        try:
            result = parse_resume(temp_path, "test_resume.docx")
            assert result.file_type == "docx"
            assert result.parsing_method == "python-docx"
            assert "John Doe" in result.raw_text
            assert "Python" in result.raw_text
        finally:
            os.unlink(temp_path)


class TestPdfParsing:
    """Tests for PDF parsing (requires reportlab for fixture generation)."""

    @pytest.fixture
    def simple_pdf(self, tmp_path):
        """Create a simple text-based PDF for testing."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
        except ImportError:
            pytest.skip("reportlab not installed")

        filepath = str(tmp_path / "test_resume.pdf")
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("Jane Smith", styles["Heading1"]),
            Paragraph("Data Scientist with Python and Machine Learning experience", styles["Normal"]),
            Paragraph("Skills: Python, TensorFlow, Pandas, SQL", styles["Normal"]),
        ]
        doc.build(story)
        return filepath

    def test_parse_text_pdf(self, simple_pdf):
        """Parse a text-based PDF and verify extraction."""
        from app.services.parser import parse_resume

        result = parse_resume(simple_pdf, "test_resume.pdf")
        assert result.file_type == "pdf"
        assert result.parsing_method == "pdfplumber"
        assert "Jane Smith" in result.raw_text
        assert "Python" in result.raw_text
