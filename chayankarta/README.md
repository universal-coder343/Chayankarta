# Chayankarta · चयनकर्ता — AI Candidate Ranking System
**MITS Gwalior â€” Cornerstone Project 2026-27**

AI-powered resume screening with semantic ranking, PII redaction, and fairness auditing.

---

## Architecture Overview

```
Frontend (React 19 + Vite + Tailwind)
    â†• REST API
Backend (FastAPI, Python 3.11)
    â”œâ”€â”€ Parsing   : pdfplumber / python-docx / Tesseract OCR (image + scanned PDF)
    â”œâ”€â”€ NLP       : spaCy en_core_web_sm + PhraseMatcher (1000+ skills)
    â”œâ”€â”€ Ranking   : sentence-transformers (all-MiniLM-L6-v2), hybrid scorer
    â”œâ”€â”€ Fairness  : PII redactor + disparate impact analysis
    â””â”€â”€ DB        : MongoDB 7 (Motor async driver)
Infrastructure
    â””â”€â”€ Docker Compose (api + frontend + mongo)
```

---

## Quick Start â€” Docker (Recommended)

> **Requires Docker Desktop 4.x+ with the Linux engine running.**

```bash
cd chayankarta

# Build and start all services
docker compose up --build

# Detached (background)
docker compose up --build -d
```

| Service   | URL                        |
|-----------|----------------------------|
| API       | http://localhost:8000      |
| Swagger   | http://localhost:8000/docs |
| Frontend  | http://localhost:5173      |
| MongoDB   | localhost:27017            |

> **First start:** The HuggingFace embedding model (`all-MiniLM-L6-v2`, ~90 MB) is
> downloaded once and cached in the `hf_cache` Docker volume. Subsequent starts use
> the local cache instantly (`TRANSFORMERS_OFFLINE=1` is set).

---

## Quick Start â€” Local (Without Docker)

### 1. Backend

```bash
cd chayankarta/backend

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
cd chayankarta/frontend
npm install
npm run dev        # â†’ http://localhost:5173
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
| `DATABASE_NAME` | `chayankarta` | Database name |
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
| `TRANSFORMERS_OFFLINE` | `1` | Use cached HF model only (no network) |
| `HF_DATASETS_OFFLINE` | `1` | Use cached HF datasets only (no network) |

---

## API Endpoints

### Resume & Job Description (Phase 1)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/resumes/upload` | Upload a resume (PDF / DOCX / image) |
| `GET` | `/api/resumes/` | List all resumes (paginated) |
| `GET` | `/api/resumes/{id}` | Get single resume |
| `DELETE` | `/api/resumes/{id}` | Delete resume |
| `POST` | `/api/jds/` | Create job description |
| `GET` | `/api/jds/` | List all JDs |
| `GET` | `/api/jds/{id}` | Get single JD |
| `DELETE` | `/api/jds/{id}` | Delete JD |

### Semantic Ranking (Milestone 4)

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

### Fairness & Audit (Milestone 5)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/audit/fairness?jd_id=...&threshold=60` | Fairness metrics + disparate impact |
| `GET` | `/api/audit/redact-preview/{resume_id}` | Side-by-side PII redaction preview |

---

## Scoring Formula

The hybrid score (0â€“100) is a weighted combination of four components:

```
final_score = 100 Ã— (
    0.40 Ã— semantic_similarity   +
    0.35 Ã— skill_overlap          +
    0.15 Ã— experience_match       +
    0.10 Ã— education_match
)
```

### Component Details

| Component | Method | Notes |
|---|---|---|
| **Semantic similarity** | Cosine similarity of `all-MiniLM-L6-v2` embeddings | L2-normalized; range [0,1] |
| **Skill overlap** | `(2 Ã— req_matched + pref_matched) / (2 Ã— req_total + pref_total)` | Required skills weighted 2Ã— preferred |
| **Experience match** | `min(1.0, candidate_years / required_years)` | 0.5 if years unknown |
| **Education match** | Candidate level Ã· required level (5-point scale) | Full score if no requirement |

Weights are configurable via `WEIGHT_*` environment variables or per-request in the API body.

---

## OCR â€” Image & Scanned PDF Support

Resumes uploaded as images (JPG, PNG, TIFF) or scanned PDFs are processed with
Tesseract OCR. The pipeline applies the following preprocessing for accuracy:

1. **Transparency flattening** â€” RGBA/PNG images are pasted on a white background
2. **Grayscale conversion**
3. **Upscaling** â€” images narrower than 1800 px are resized with LANCZOS
4. **Sharpening** â€” `ImageFilter.SHARPEN`
5. **Contrast boost** â€” `ImageEnhance.Contrast(2.0)`
6. **Noise reduction** â€” `ImageFilter.MedianFilter(size=3)`
7. **Tesseract config** â€” `--oem 3 --psm 6 -l eng` (LSTM engine, uniform text block, English)

> **Tip:** For best extraction quality, upload resumes as **PDF** (text-based) or **DOCX**.
> Image OCR is inherently less accurate on low-quality scans.

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
Values â‰¥ 0.80 pass the EEOC **4/5 rule**.

**Score delta** = mean |redacted_score âˆ’ raw_score| â€” quantifies how much redaction changed ranking.

---

## Running Tests

```bash
cd chayankarta/backend

# Unit tests (no DB, no model needed â€” uses mocks)
python -m pytest tests/test_embedder.py tests/test_scorer.py tests/test_redactor.py -v

# Endpoint tests
python -m pytest tests/test_ranking_endpoints.py -v

# All tests
python -m pytest -v
```

---

## Docker Troubleshooting

| Symptom | Fix |
|---|---|
| `500 Internal Server Error` on `/_ping` | Docker Desktop engine crashed â€” restart Docker Desktop or run `wsl --shutdown` then relaunch |
| `docker-desktop` WSL distro not found | Docker is using the Virtualization Framework backend (not WSL2) â€” use **Settings â†’ Troubleshoot â†’ Reset to factory defaults** |
| VM disk I/O errors in `vm/init.log` | Virtual disk corrupted â€” factory reset required |
| HuggingFace DNS warnings on startup | Normal on first boot; model loads from cache after retry. Set `TRANSFORMERS_OFFLINE=1` to skip network entirely |
| `pip install` exit code 2 | Install torch CPU wheel before `sentence-transformers` â€” handled in Dockerfile automatically |

---

## Known Limitations & Design Notes

1. **Group inference uses proxies, not ground truth.** Gender is inferred from pronouns,
   not self-reported data. Results should be treated as indicative, not definitive.

2. **Embedding model is loaded at startup.** First startup downloads `all-MiniLM-L6-v2`
   (~90 MB) into the `hf_cache` volume. Subsequent starts use cache instantly.

3. **Redaction is pre-embedding only.** NER data (name, email) already stored in MongoDB
   is **not** modified â€” only the text fed to the embedding model is redacted.
   The `ner.name` field is still used for display in the rankings UI.

4. **Experience extraction is text-regex-based.** Extracts the maximum year figure from
   raw text. Multi-role experience timelines are not yet summed.

5. **Fairness audit is not a legal compliance tool.** It is a transparency/monitoring
   instrument for developers and recruiters. Always involve a qualified HR professional
   for hiring decisions.

6. **OneDrive + Git conflict.** If your project lives inside OneDrive, run all `git`
   commands in your own terminal (not via an IDE shell) to avoid `index.lock` permission
   errors caused by OneDrive's real-time sync. Consider excluding the `.git` folder from
   OneDrive sync.
