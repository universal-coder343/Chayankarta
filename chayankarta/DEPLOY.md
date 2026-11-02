# 🚀 Deploying Chayankarta to Railway

Step-by-step guide to deploy the full stack (FastAPI + React + MongoDB) on [Railway](https://railway.app).

---

## Prerequisites

- [x] GitHub repo with latest code pushed
- [ ] Railway account ([sign up free](https://railway.app) — $5/month hobby plan needed for deployments)

---

## Step 1 — Create a Railway Project

1. Go to [railway.app/new](https://railway.app/new)
2. Click **"New Project"** → **"Empty Project"**
3. Name it `chayankarta`

---

## Step 2 — Add MongoDB

1. Inside the project, click **"+ New"** → **"Database"** → **"MongoDB"**
2. Railway provisions a MongoDB instance with persistent storage
3. Click the MongoDB service → **"Variables"** tab
4. Note the `MONGO_URL` variable — you'll reference this in the backend

---

## Step 3 — Add the Backend Service

1. Click **"+ New"** → **"GitHub Repo"** → select your repository
2. Railway will ask which directory — set:
   - **Root Directory**: `chayankarta/backend`
3. Railway auto-detects the `Dockerfile` and starts building
4. Go to **Settings** tab:
   - **Service Name**: `api`
   - **Health Check Path**: `/health`
   - **Restart Policy**: On Failure (3 retries)
5. Go to **Variables** tab and add:

   | Variable | Value |
   |---|---|
   | `MONGODB_URL` | `${{MongoDB.MONGO_URL}}` (click "Add Reference") |
   | `DATABASE_NAME` | `chayankarta` |
   | `CORS_ORIGINS` | `["https://${{RAILWAY_PUBLIC_DOMAIN}}"]` |
   | `RAILWAY_PUBLIC_DOMAIN` | *(auto-set by Railway)* |
   | `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` |
   | `WEIGHT_SEMANTIC` | `0.40` |
   | `WEIGHT_SKILL` | `0.35` |
   | `WEIGHT_EXPERIENCE` | `0.15` |
   | `WEIGHT_EDUCATION` | `0.10` |
   | `ENABLE_REDACTION` | `true` |
   | `REDACT_INSTITUTIONS` | `false` |
   | `LOG_LEVEL` | `INFO` |

6. Go to **Networking** tab:
   - Click **"Generate Domain"** to get a public URL (e.g., `api-production-xxxx.up.railway.app`)
   - **Or** add a custom domain

> [!IMPORTANT]
> The first deploy will take 5–10 minutes because it installs PyTorch, spaCy, and the sentence-transformers model.

---

## Step 4 — Add the Frontend Service

1. Click **"+ New"** → **"GitHub Repo"** → select the **same repository**
2. Set:
   - **Root Directory**: `chayankarta/frontend`
3. Railway auto-detects the `Dockerfile`
4. Go to **Settings** tab:
   - **Service Name**: `frontend`
5. Go to **Variables** tab and add:

   | Variable | Value |
   |---|---|
   | `BACKEND_URL` | `http://api.railway.internal:${{api.PORT}}` |

   > This uses Railway's **private networking** — the frontend nginx proxies `/api` to the backend over the internal network. No public exposure of the API needed!

6. Go to **Networking** tab:
   - Click **"Generate Domain"** — this is your app's public URL
   - **Or** add a custom domain (e.g., `chayankarta.yourdomain.com`)

---

## Step 5 — Deploy!

Railway auto-deploys when you push to the linked branch. To trigger manually:
1. Click each service → **"Deploy"** button
2. Or push a commit to your GitHub repo

---

## Step 6 — Verify

1. Open the **frontend** public URL in your browser
2. You should see the Chayankarta recruiter dashboard
3. Check the backend health: visit `https://<frontend-url>/health`
4. Try uploading a resume to verify end-to-end functionality

---

## Architecture on Railway

```
┌─────────────────────────────────────────────────────────────┐
│                    Railway Project                          │
│                                                             │
│  ┌──────────────┐     private      ┌──────────────────┐    │
│  │   Frontend   │────networking───▶│    Backend (API)  │    │
│  │  nginx:alpine│   /api proxy     │    FastAPI + ML   │    │
│  │   port:3000  │                  │    port:8000      │    │
│  └──────┬───────┘                  └────────┬─────────┘    │
│         │                                    │              │
│         │ public                    private   │              │
│         │ domain                   networking │              │
│         ▼                                    ▼              │
│    Users (HTTPS)                    ┌──────────────┐        │
│                                     │   MongoDB 7  │        │
│                                     │  persistent  │        │
│                                     │   volume     │        │
│                                     └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## Costs

Railway's **Hobby Plan** ($5/month) includes:
- 8 GB RAM, 8 vCPU (shared across services)
- 100 GB network egress
- Sufficient for an academic project demo

> [!TIP]
> The free Trial plan gives you a one-time $5 credit to test deployments, but services sleep after the credit runs out.

---

## Local Docker Testing

Before deploying to Railway, test locally:

```bash
cd chayankarta
docker compose up --build
```

Then open http://localhost:3000 — the frontend nginx proxies API calls to the backend.

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Backend build fails (PyTorch) | Check Railway build logs. CPU-only PyTorch needs the custom index URL (already in Dockerfile) |
| Frontend shows "502 Bad Gateway" | `BACKEND_URL` is wrong. It must use Railway's internal DNS: `http://api.railway.internal:<port>` |
| MongoDB connection refused | Check that `MONGODB_URL` references the MongoDB service variable (use Railway's variable references) |
| Model download fails at startup | Set `TRANSFORMERS_OFFLINE=0` for first deploy so HuggingFace can download the model, then set it back to `1` |
| CORS errors in browser | Make sure `CORS_ORIGINS` in backend includes the frontend's public domain |

