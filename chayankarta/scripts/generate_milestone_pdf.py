"""
Generate a professional Project Milestone & Roadmap PDF Report.
Uses ReportLab with custom styling matching the project's aesthetic.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas that performs a two-pass render to print 'Page X of Y'."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#7d7369"))

        # Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(
                54,
                11 * 72 - 36,
                "Chayankarta - AI Candidate Ranking System â€” Milestone Report",
            )
            self.setStrokeColor(colors.HexColor("#dcc1b8"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)

        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 54, 36, footer_text)
        self.drawString(
            54,
            36,
            "Confidential & Proprietary â€” College Capstone Project Milestone Documentation",
        )
        self.setStrokeColor(colors.HexColor("#dcc1b8"))
        self.setLineWidth(0.5)
        self.line(54, 48, 8.5 * 72 - 54, 48)

        self.restoreState()


def build_pdf(filename="Milestone_Report_Phase_1.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom Palette
    c_primary = colors.HexColor("#9a401d")      # Terracotta
    c_secondary = colors.HexColor("#904d00")    # Warm Amber/Brown
    c_dark = colors.HexColor("#1e1b17")         # Espresso Black
    c_muted = colors.HexColor("#56423c")        # Warm Grey
    c_card_bg = colors.HexColor("#faf2eb")      # Cream Surface
    c_border = colors.HexColor("#dcc1b8")       # Border tint
    c_green = colors.HexColor("#10b981")        # Emerald
    c_green_bg = colors.HexColor("#ecfdf5")     # Light Green

    # Typography Styles
    style_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=c_primary,
        spaceAfter=4,
    )

    style_subtitle = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=c_muted,
        spaceAfter=14,
    )

    style_h1 = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    style_h2 = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=c_secondary,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    style_body = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=c_dark,
        spaceAfter=6,
    )

    style_body_bold = ParagraphStyle(
        "BodyBold",
        parent=style_body,
        fontName="Helvetica-Bold",
    )

    style_table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=c_dark,
    )

    style_table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.white,
    )

    style_tag_done = ParagraphStyle(
        "TagDone",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#065f46"),
        alignment=1,
    )

    style_tag_next = ParagraphStyle(
        "TagNext",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#9a401d"),
        alignment=1,
    )

    story = []

    # ---------------------------------------------------------
    # COVER / HEADER BLOCK
    # ---------------------------------------------------------
    story.append(Paragraph("PROJECT MILESTONE & ROADMAP REPORT", style_title))
    story.append(
        Paragraph(
            "Chayankarta - AI Candidate Ranking System â€” Phase 1 & Roadmap",
            style_subtitle,
        )
    )

    # Metadata Strip Table
    now_str = datetime.now().strftime("%B %d, %Y")
    meta_data = [
        [
            Paragraph("<b>Project Phase:</b> Phase 1 Completed", style_table_cell),
            Paragraph("<b>Target Scope:</b> Weeks 1â€“4 Delivered", style_table_cell),
            Paragraph(f"<b>Generated:</b> {now_str}", style_table_cell),
            Paragraph("<b>Status:</b> On Schedule (100% Phase 1)", style_table_cell),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[120, 130, 120, 134])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), c_card_bg),
                ("BOX", (0, 0), (-1, -1), 1, c_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # 1. EXECUTIVE SUMMARY
    # ---------------------------------------------------------
    story.append(Paragraph("1. Executive Summary & Project Objectives", style_h1))
    story.append(
        Paragraph(
            "The <b>Chayankarta (चयनकर्ता) — AI Candidate Ranking System</b> is an intelligent, automated recruitment platform engineered to streamline talent acquisition. The end-to-end architecture ingests multi-format resumes, performs layout-preserving text extraction, identifies named entities and technical competencies via NLP, computes semantic embeddings using Sentence-BERT, calculates cosine similarity ranking against job descriptions, and applies algorithmic fairness audits to eliminate hiring biases.",
            style_body,
        )
    )
    story.append(
        Paragraph(
            "<b>Current Status:</b> Phase 1 (Weeks 1â€“4) has been <b>fully executed, tested, and verified</b>. The underlying microservice architecture, asynchronous persistence layer, hybrid OCR parsing pipeline, spaCy NER skills extractor, and responsive workstation UI are completely operational.",
            style_body,
        )
    )
    story.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # 2. COMPLETED WORK (PHASE 1 - WEEKS 1 TO 4)
    # ---------------------------------------------------------
    story.append(Paragraph("2. Detailed Work Completed (Phase 1)", style_h1))

    completed_items = [
        (
            "Component 1: Project Skeleton & Configuration",
            "Configured clean repository root with .gitignore, multi-stage backend Dockerfile, docker-compose.yml for MongoDB and API orchestration, pydantic-settings environment loader, and CORS-enabled FastAPI lifespan.",
        ),
        (
            "Component 2: Pydantic v2 Models & Schema Architecture",
            "Designed strongly-typed data schemas in `app/models/resume.py` and `app/models/job_description.py` encapsulating raw text, parsing metadata, contact info (emails, phones, URLs, location), work experience, education, and 6-domain categorized skills.",
        ),
        (
            "Component 3: Hybrid Document Parsing & OCR Pipeline",
            "Constructed resilient multi-format document parser in `app/services/parser.py`. Automatically routes native PDFs to pdfplumber, Word documents to python-docx, and flat/scanned image files (PNG, JPG, scanned PDFs) to Tesseract OCR via pdf2image when extracted text density is under 50 characters.",
        ),
        (
            "Component 4: NER & Skills Taxonomy Extraction Engine",
            "Engineered spaCy NLP pipeline (`en_core_web_sm`) in `app/services/ner.py` featuring PhraseMatcher and EntityRuler against a curated taxonomy (`skills_taxonomy.json`) containing 1000+ technical skills categorized into 6 domains: Languages, Frameworks, Databases, DevOps/Cloud, Tools/Platforms, and Methodologies. Integrated regex matchers for candidate emails, phone numbers, and profile URLs.",
        ),
        (
            "Component 5: Job Description Extraction Engine",
            "Created `app/services/jd_parser.py` and router `app/routers/jds.py` which analyze raw job description text to segment required vs. preferred skills, minimum/maximum experience year constraints, and degree qualifications.",
        ),
        (
            "Component 6: Asynchronous REST API Endpoints",
            "Implemented FastAPI routers for resume upload, retrieval, pagination, and deletion (`/api/resumes`), job descriptions management (`/api/jds`), and system liveness verification (`/health`).",
        ),
        (
            "Component 7: Dataset & Sample Synthesis Scripts",
            "Authored `scripts/create_samples.py` to programmatically generate realistic multi-format resumes across PDF, DOCX, and scanned image formats. Provided `scripts/download_dataset.py` for downloading large-scale public resume datasets.",
        ),
        (
            "Component 8: Modern React Workstation Frontend",
            "Built responsive Single Page Application using React 19 and Vite 8 following the custom warm terracotta design system. Key UI capabilities: drag-and-drop file upload with format pills, real-time KPI metrics bar (resumes count, skills count, avg density), search with instant keyword filtering, format tabs, ranked candidate dossiers with match index dials, detailed NER & raw text inspector modal, and functional CSV export.",
        ),
        (
            "Component 9: Test Suite & Build Verification",
            "Created comprehensive pytest suite (`backend/tests`) testing API health checks, multi-format parser edge cases, and NER skills categorization. Verified zero-error production build (`npm run build` in 244ms).",
        ),
    ]

    for title, desc in completed_items:
        story.append(Paragraph(f"â€¢ <b>{title}:</b> {desc}", style_body))

    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # 3. ARCHITECTURE & TECHNOLOGY MATRIX
    # ---------------------------------------------------------
    story.append(Paragraph("3. System Architecture & Technology Matrix", style_h1))

    tech_table_data = [
        [
            Paragraph("Subsystem Layer", style_table_header),
            Paragraph("Technology Stack", style_table_header),
            Paragraph("Phase 1 Role", style_table_header),
            Paragraph("Status", style_table_header),
        ],
        [
            Paragraph("Backend API", style_table_cell),
            Paragraph("Python 3.11 + FastAPI + Uvicorn", style_table_cell),
            Paragraph("Asynchronous REST routing, lifespan, file streaming", style_table_cell),
            Paragraph("COMPLETED", style_tag_done),
        ],
        [
            Paragraph("Database Layer", style_table_cell),
            Paragraph("MongoDB 7.0 + Motor Async Driver", style_table_cell),
            Paragraph("NoSQL persistence for parsed resumes & JDs", style_table_cell),
            Paragraph("COMPLETED", style_tag_done),
        ],
        [
            Paragraph("Native Document Parsing", style_table_cell),
            Paragraph("pdfplumber + python-docx", style_table_cell),
            Paragraph("Digital layout decoding & clean text extraction", style_table_cell),
            Paragraph("COMPLETED", style_tag_done),
        ],
        [
            Paragraph("Optical Character Rec.", style_table_cell),
            Paragraph("pytesseract + pdf2image + Pillow", style_table_cell),
            Paragraph("Automated fallback OCR for scanned documents", style_table_cell),
            Paragraph("COMPLETED", style_tag_done),
        ],
        [
            Paragraph("NLP & Skills NER", style_table_cell),
            Paragraph("spaCy (en_core_web_sm) + PhraseMatcher", style_table_cell),
            Paragraph("Entity extraction + 1000+ skills taxonomy", style_table_cell),
            Paragraph("COMPLETED", style_tag_done),
        ],
        [
            Paragraph("Frontend Workstation", style_table_cell),
            Paragraph("React 19 + Vite 8 + Tailwind CSS", style_table_cell),
            Paragraph("Terracotta themed recruiter workstation & dossiers", style_table_cell),
            Paragraph("COMPLETED", style_tag_done),
        ],
        [
            Paragraph("Semantic Embeddings", style_table_cell),
            Paragraph("Sentence-BERT (all-MiniLM-L6-v2)", style_table_cell),
            Paragraph("Dense vector embedding generation", style_table_cell),
            Paragraph("PHASE 2", style_tag_next),
        ],
        [
            Paragraph("Similarity & Ranking", style_table_cell),
            Paragraph("Cosine Similarity + Weighted Scoring", style_table_cell),
            Paragraph("Candidate ranking against Job Requirements", style_table_cell),
            Paragraph("PHASE 2", style_tag_next),
        ],
        [
            Paragraph("Fairness & De-biasing", style_table_cell),
            Paragraph("PII Redactor + Demographic Parity Audit", style_table_cell),
            Paragraph("Equal opportunity & demographic bias mitigation", style_table_cell),
            Paragraph("PHASE 3", style_tag_next),
        ],
    ]

    t_tech = Table(tech_table_data, colWidths=[110, 150, 180, 64])
    t_tech.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                ("BOX", (0, 0), (-1, -1), 1, c_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_card_bg]),
            ]
        )
    )
    story.append(t_tech)
    story.append(Spacer(1, 12))

    # ---------------------------------------------------------
    # 4. WHAT IS LEFT (FUTURE ROADMAP - PHASES 2, 3, 4)
    # ---------------------------------------------------------
    story.append(Paragraph("4. Remaining Work & Development Roadmap", style_h1))
    story.append(
        Paragraph(
            "With the solid foundational architecture established in Phase 1, the remaining work is organized into three sequential phases representing Weeks 5 through 12 of the academic project lifecycle:",
            style_body,
        )
    )

    roadmap_phases = [
        (
            "Phase 2 (Weeks 5â€“7): Semantic Embeddings & Candidate Ranking Algorithm",
            [
                "<b>Sentence-BERT Integration:</b> Load `sentence-transformers` (`all-MiniLM-L6-v2`) to compute 384-dimensional dense semantic vectors for both candidate profiles and job descriptions.",
                "<b>Hybrid Similarity Model:</b> Implement cosine similarity matching combined with rule-based weighted scoring: <i>Score = w1*(Semantic Sim) + w2*(Must-Have Skills %) + w3*(Experience Fit %)</i>.",
                "<b>Candidate Scoring & Ranking Service:</b> Expose `/api/rankings` endpoint returning ranked candidate lists, score breakdowns, and missing skill gap analysis.",
                "<b>Vector Caching:</b> Cache precomputed resume embeddings in MongoDB/NumPy arrays to ensure sub-100ms ranking latency.",
            ],
        ),
        (
            "Phase 3 (Weeks 8â€“10): Algorithmic Fairness, Bias Auditing & Explainable AI",
            [
                "<b>PII & Demographic Redaction:</b> Complete `app/services/redactor.py` to anonymize gender, ethnicity proxies, candidate names, addresses, and graduation dates prior to ranking.",
                "<b>Demographic Parity Audit:</b> Implement fairness evaluation metrics (Disparate Impact Ratio, Four-Fifths Rule compliance) across simulated demographic subgroups.",
                "<b>Explainable AI (XAI) Badges:</b> Provide transparent explanations for why each candidate received their ranking (e.g. key contributing skills, experience qualification factors).",
            ],
        ),
        (
            "Phase 4 (Weeks 11â€“12): Recruiter Analytics Dashboard & Final Capstone Deployment",
            [
                "<b>Recruiter Comparison Matrix:</b> Interactive side-by-side comparison modal allowing recruiters to evaluate multiple short-listed candidates against the same job description.",
                "<b>Full Docker Compose Stack:</b> Containerize frontend with Nginx, backend with Uvicorn, and MongoDB with persistent data volumes.",
                "<b>Documentation & Final Presentation:</b> Complete college project report, IEEE-format research paper draft, presentation slides, and live demonstration sandbox.",
            ],
        ),
    ]

    for p_title, p_bullets in roadmap_phases:
        story.append(Paragraph(p_title, style_h2))
        for bullet in p_bullets:
            story.append(Paragraph(f"â€¢ {bullet}", style_body))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # 5. TIMELINE & MILESTONE SCHEDULE
    # ---------------------------------------------------------
    story.append(Paragraph("5. Overall Project Schedule & Deliverables", style_h1))

    schedule_data = [
        [
            Paragraph("Phase / Milestone", style_table_header),
            Paragraph("Weeks", style_table_header),
            Paragraph("Target Key Deliverables", style_table_header),
            Paragraph("Status", style_table_header),
        ],
        [
            Paragraph("Phase 1: Ingestion, OCR & NER", style_table_cell),
            Paragraph("Weeks 1â€“4", style_table_cell),
            Paragraph("Parser, OCR, spaCy NER, MongoDB, React Workstation UI", style_table_cell),
            Paragraph("100% COMPLETE", style_tag_done),
        ],
        [
            Paragraph("Phase 2: Embeddings & Ranking", style_table_cell),
            Paragraph("Weeks 5â€“7", style_table_cell),
            Paragraph("Sentence-BERT, Cosine Matching, Weighted Scoring Engine", style_table_cell),
            Paragraph("PLANNED NEXT", style_tag_next),
        ],
        [
            Paragraph("Phase 3: Bias Mitigation & XAI", style_table_cell),
            Paragraph("Weeks 8â€“10", style_table_cell),
            Paragraph("PII Redaction, Demographic Parity, Explainable AI Badges", style_table_cell),
            Paragraph("UPCOMING", style_tag_next),
        ],
        [
            Paragraph("Phase 4: Dashboard & Final Release", style_table_cell),
            Paragraph("Weeks 11â€“12", style_table_cell),
            Paragraph("Side-by-side Recruiter UI, Docker deployment, Project Report", style_table_cell),
            Paragraph("UPCOMING", style_tag_next),
        ],
    ]

    t_sched = Table(schedule_data, colWidths=[130, 60, 220, 94])
    t_sched.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), c_secondary),
                ("BOX", (0, 0), (-1, -1), 1, c_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_card_bg]),
            ]
        )
    )
    story.append(t_sched)
    story.append(Spacer(1, 14))

    # Sign-off block
    story.append(
        Paragraph(
            "<b>Summary & Next Steps:</b> Phase 1 has established an end-to-end operational baseline. The codebase is cleanly decoupled and prepared for Phase 2 Sentence-BERT vectorization and ranking algorithms.",
            style_body,
        )
    )

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated milestone report: {filename}")


if __name__ == "__main__":
    out_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Milestone_Report_Phase_1.pdf",
    )
    build_pdf(out_path)
