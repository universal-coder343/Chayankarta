"""
FastAPI application entry point.
Configures lifespan (Mongo + spaCy), CORS, logging, health check, and routers.
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
    logger.info("Starting up Smart Resume Screening API ...")

    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)

    # Connect to MongoDB
    await connect_db()

    # Pre-load spaCy model (so the first request isn't slow)
    from .services.ner import get_nlp  # noqa: lazy import to avoid circular deps
    get_nlp()
    logger.info("spaCy NLP model loaded.")

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
    title="Smart Resume Screening API",
    description="AI-powered resume screening and candidate ranking system — Phase 1",
    version="0.1.0",
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

# Routers
app.include_router(resumes.router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(jds.router, prefix="/api/jds", tags=["Job Descriptions"])


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
    }
