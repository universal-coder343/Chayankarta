# Chayankarta (चयनकर्ता)

> AI-powered resume screening & candidate ranking system, jo recruiters ko sahi candidate tak jaldi pahunchata hai.

*Chayankarta* means "selector" in Hindi: it parses resumes, extracts skills, matches them against a job description, and ranks candidates.

Cornerstone Project, Madhav Institute of Technology & Science (MITS), Gwalior. Academic Session 2026-27.

---

## Features

**Done**
- Recruiter dashboard (React)
- Hybrid resume parsing: `pdfplumber`, `python-docx`, Tesseract OCR for scanned files
- NER-based skill extraction (spaCy) over a 1000+ skill taxonomy
- Job Description (JD) engine
- Async REST API (FastAPI) with pytest suite

**In progress / planned**
- Sentence-BERT embeddings + hybrid ranking score (`/api/rankings`)
- PII / demographic redaction and fairness audit
- Recruiter candidate comparison view
- Docker Compose deployment

---

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, Pydantic v2, MongoDB (Motor) |
| Frontend | React 19, Vite, Tailwind CSS |
| NLP | spaCy (PhraseMatcher / EntityRuler), Sentence-BERT (planned) |
| Parsing / OCR | pdfplumber, python-docx, Tesseract, pdf2image |
| Testing | pytest |

---

## Project Structure

```
chayankarta/
├── backend/     # FastAPI app, parsing, NER, ranking
├── frontend/    # React + Vite recruiter dashboard
└── README.md
```

> Adjust folder names above to match the actual repo layout.

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB (local or Atlas)
- Tesseract OCR installed and on PATH

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env            # set MONGODB_URI etc.

```

API docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

### Tests
```bash
cd backend
pytest
```

---

## How It Works

1. Recruiter uploads resumes (PDF / DOCX / scanned) and a job description.
2. Parser extracts text (OCR fallback for scans).
3. spaCy NER pulls skills, education, experience.
4. JD engine extracts required skills.
5. Ranking engine scores each candidate against the JD.
6. Dashboard shows ranked candidates.

---

## Team

- Vivek Kumar
- Yash Phulre

**Mentor:** Ms. Kumud Dixit

---

## License

Academic project. Add a license of your choice (e.g. MIT) if you plan to open-source it.
