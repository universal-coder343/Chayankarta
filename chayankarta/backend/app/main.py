"""
FastAPI application entry point.
Configures lifespan (Mongo + spaCy + embedder), CORS, logging, health check, and routers.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import connect_db, close_db, get_database
from .routers import resumes, jds
from .routers import ranking as ranking_router
from .routers import audit as audit_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown tasks."""
    # ---- Startup ----
    logger.info("Starting up Chayankarta API (Phase 2) ...")

    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)

    # Connect to MongoDB
    await connect_db()

    # Pre-load spaCy model (so the first request isn't slow).
    # Wrapped in try/except because on some machines (e.g. Windows with an
    # Application Control Policy) the underlying PyTorch/thinc DLL is blocked.
    # The server still starts successfully; spaCy is loaded lazily on first use.
    try:
        from .services.ner import get_nlp  # noqa: lazy import
        get_nlp()
        logger.info("spaCy NLP model loaded.")
    except Exception as exc:
        logger.warning(
            "Could not pre-load spaCy model (NER will be attempted on first request): %s",
            exc,
        )

    # Pre-load sentence-transformers embedding model
    try:
        from .services.embedder import _get_model  # noqa: lazy import
        _get_model()
        logger.info("SentenceTransformer embedding model loaded.")
    except Exception as exc:
        logger.warning("Could not pre-load embedding model: %s", exc)

    logger.info("Startup complete.")
    yield

    # ---- Shutdown ----
    logger.info("Shutting down ...")
    await close_db()
    logger.info("Shutdown complete.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Chayankarta API",
    description=(
        "Chayankarta — AI-powered candidate screening and ranking. "
        "चयनकर्ता · Phase 2: Semantic Ranking + Fairness Audit"
    ),
    version="0.2.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers — Phase 1
app.include_router(resumes.router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(jds.router, prefix="/api/jds", tags=["Job Descriptions"])

# Routers — Phase 2 (Milestones 4 & 5)
app.include_router(ranking_router.router, prefix="/api/rankings", tags=["Rankings"])
app.include_router(audit_router.router, prefix="/api/audit", tags=["Fairness Audit"])


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    """Return service health status including database connectivity."""
    db_status = "disconnected"
    try:
        db = get_database()
        await db.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "error"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "db": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "0.2.0",
        "features": {
            "semantic_ranking": True,
            "pii_redaction": settings.enable_redaction,
            "fairness_audit": True,
        },
    }
