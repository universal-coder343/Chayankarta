# Smart Resume Screening & Candidate Ranking System
**MITS Gwalior — Cornerstone Project 2026-27**

AI-powered resume screening with semantic ranking, PII redaction, and fairness auditing.

---

## Architecture Overview

```
Frontend (React 19 + Vite + Tailwind)
    ↕ REST API
Backend (FastAPI 0.2, Python 3.11+)
    ├── Parsing   : pdfplumber / python-docx / Tesseract OCR
    ├── NLP       : spaCy en_core_web_sm + PhraseMatcher (1000+ skills)
    ├── Ranking   : sentence-transformers (all-MiniLM-L6-v2), hybrid scorer
    ├── Fairness  : PII redactor + disparate impact analysis
    └── DB        : MongoDB (Motor async driver)
```

---

## Quick Start

### 1. Backend

```bash
cd resume-screening/backend

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Copy environment file
cp .env.example .env

# Start the API
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd resume-screening/frontend
npm install
npm run dev        # → http://localhost:5173
```

### 3. Seed Demo Data

After starting the backend:

```bash
# Creates 10 sample resumes + 3 JDs, backfills embeddings, and runs a demo ranking
python scripts/seed_data.py

# Custom API URL
python scripts/seed_data.py --url http://localhost:8000
```

---

## Environment Variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `DATABASE_NAME` | `resume_screening` | Database name |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed frontend origins |
| `LOG_LEVEL` | `INFO` | Logging level |
| `UPLOAD_DIR` | `./uploads` | Directory for uploaded files |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-Transformers model name |
| `WEIGHT_SEMANTIC` | `0.40` | Semantic similarity weight |
| `WEIGHT_SKILL` | `0.35` | Skill overlap weight |
| `WEIGHT_EXPERIENCE` | `0.15` | Experience match weight |
| `WEIGHT_EDUCATION` | `0.10` | Education match weight |
| `ENABLE_REDACTION` | `true` | Enable PII redaction before scoring |
| `REDACT_INSTITUTIONS` | `false` | Also redact college/university names |

---

## API Endpoints

### Phase 1 (Parsing & NER)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/resumes/upload` | Upload a resume (PDF/DOCX/image) |
| `GET` | `/api/resumes/` | List all resumes (paginated) |
| `GET` | `/api/resumes/{id}` | Get single resume |
| `DELETE` | `/api/resumes/{id}` | Delete resume |
| `POST` | `/api/jds/` | Create job description |
| `GET` | `/api/jds/` | List all JDs |
| `GET` | `/api/jds/{id}` | Get single JD |
| `DELETE` | `/api/jds/{id}` | Delete JD |

### Milestone 4 — Semantic Ranking

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/rankings/` | Rank candidates (full request body) |
| `GET` | `/api/rankings/?jd_id=...&top_k=...&min_score=...` | Quick rank via query params |
| `POST` | `/api/rankings/backfill` | Embed all un-embedded documents |

**POST `/api/rankings/` body:**
```json
{
  "jd_id": "uuid-of-job-description",
  "top_k": 10,
  "min_score": 0.0,
  "resume_ids": [],
  "weights": {
    "semantic": 0.40,
    "skill_overlap": 0.35,
    "experience": 0.15,
    "education": 0.10
  }
}
```

**Response per candidate:**
```json
{
  "rank": 1,
  "resume_id": "...",
  "candidate_name": "...",
  "final_score": 78.5,
  "explanation": "Matched 4/5 required skills (80%). Strong semantic alignment.",
  "breakdown": {
    "semantic_score": 0.82,
    "skill_overlap_score": 0.75,
    "experience_score": 1.0,
    "education_score": 1.0,
    "matched_skills": ["Python", "FastAPI", "Docker"],
    "missing_skills": ["Kubernetes"],
    "preferred_matched": ["GraphQL"]
  }
}
```

### Milestone 5 — Fairness & Audit

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/audit/fairness?jd_id=...&threshold=60` | Fairness metrics + disparate impact |
| `GET` | `/api/audit/redact-preview/{resume_id}` | Side-by-side PII redaction preview |

---

## Scoring Formula

The hybrid score (0–100) is a weighted combination of four components:

```
final_score = 100 × (
    0.40 × semantic_similarity   +
    0.35 × skill_overlap          +
    0.15 × experience_match       +
    0.10 × education_match
)
```

### Component Details

| Component | Method | Notes |
|---|---|---|
| **Semantic similarity** | Cosine similarity of `all-MiniLM-L6-v2` embeddings | L2-normalized; range [0,1] |
| **Skill overlap** | `(2 × req_matched + pref_matched) / (2 × req_total + pref_total)` | Required skills weighted 2× preferred |
| **Experience match** | `min(1.0, candidate_years / required_years)` | 0.5 if years unknown |
| **Education match** | Candidate level ÷ required level (5-point scale) | Full score if no requirement |

Weights are configurable via `WEIGHT_*` environment variables or per-request in the API body.

---

## Fairness Method (Milestone 5)
### PII Redaction
Before embedding/scoring, the following are redacted from resume text:

| Category | Replacement |
|---|---|
| Names (spaCy PERSON) | `[CANDIDATE]` |
| Emails | `[EMAIL]` |
| Phones | `[PHONE]` |
| URLs / LinkedIn / GitHub | `[LINK]` |
| Physical addresses | `[ADDRESS]` |
| Gender pronouns / titles (he/she/Mr/Ms) | `[GENDER_INDICATOR]` |
| Date of birth / age | `[AGE]` |
| Marital status | `[MARITAL_STATUS]` |
| Nationality | `[NATIONALITY]` |
| Religion / caste | `[RELIGION]` |
| Location (spaCy GPE) | `[LOCATION]` |
| Institution names *(optional)* | `[INSTITUTION]` |

The **original text is preserved** in MongoDB; only the redacted copy is used for embedding.  
Toggle with `ENABLE_REDACTION=true/false`. Redact institutions with `REDACT_INSTITUTIONS=true`.

### Disparate Impact Analysis

Groups are inferred from **proxy signals** in raw text (before redaction):

- **Gender proxy**: count of he/him/his vs she/her/hers pronouns
- **Institution tier**: Tier-1 (IIT/IIM/NIT/BITS) vs Tier-2 (other college/university)
- **Fallback**: `unknown`

Metrics per group:
- `count`, `mean_score`, `std_score`, `selection_rate` (fraction above threshold)

**Disparate Impact Ratio** = min(selection_rate) / max(selection_rate)  
Values ≥ 0.80 pass the EEOC **4/5 rule**.

**Score delta** = mean |redacted_score − raw_score| — quantifies how much redaction changed ranking.

---

## Running Tests

```bash
cd resume-screening/backend

# Unit tests (no DB, no model needed — uses mocks)
python -m pytest tests/test_embedder.py tests/test_scorer.py tests/test_redactor.py -v

# Endpoint tests
python -m pytest tests/test_ranking_endpoints.py -v

# All tests
python -m pytest -v
```

---

## Known Limitations & Design Notes

1. **Group inference uses proxies, not ground truth.** Gender is inferred from pronouns, not self-reported data. Results should be treated as indicative, not definitive.

2. **Embedding model is loaded at startup.** First startup takes ~5–10s to download `all-MiniLM-L6-v2` (~90MB). Subsequent starts use the local cache.

3. **Redaction is pre-embedding only.** NER data (name, email) already stored in MongoDB is **not** modified — only the text fed to the embedding model is redacted. The `ner.name` field is still used for display in the rankings UI.

4. **Experience extraction is text-regex-based.** It extracts the *maximum* year figure from raw text. Multi-role experience timelines are not yet summed.

5. **Fairness audit is not a legal compliance tool.** It is a transparency/monitoring instrument for developers and recruiters. Always involve a qualified HR professional for hiring decisions.

6. **Docker Compose** support is planned for Phase 3. The existing `docker-compose.yml` runs Phase 1 only.
