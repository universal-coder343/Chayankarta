"""
MongoDB connection management using motor async driver.
Handles connection lifecycle via FastAPI lifespan and index creation.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from .config import get_settings

logger = logging.getLogger(__name__)

# Global references — set during lifespan
_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    """Initialize the MongoDB connection and create indexes."""
    global _client, _database
    settings = get_settings()
    logger.info("Connecting to MongoDB at %s ...", settings.mongodb_url)
    _client = AsyncIOMotorClient(settings.mongodb_url)
    _database = _client[settings.database_name]

    # Verify connectivity
    await _client.admin.command("ping")
    logger.info("MongoDB connected — database: %s", settings.database_name)

    # Create indexes
    await create_indexes()


async def close_db() -> None:
    """Close the MongoDB connection."""
    global _client, _database
    if _client:
        _client.close()
        logger.info("MongoDB connection closed.")
    _client = None
    _database = None


async def create_indexes() -> None:
    """Create indexes for all collections."""
    db = get_database()

    # --- resumes collection ---
    resumes = db["resumes"]
    await resumes.create_index([("upload_time", DESCENDING)], name="idx_upload_time")
    await resumes.create_index([("ner.skills", ASCENDING)], name="idx_ner_skills")
    await resumes.create_index([("filename", ASCENDING)], unique=True, name="idx_filename_unique")
    logger.info("Indexes created for 'resumes' collection.")

    # --- job_descriptions collection ---
    jds = db["job_descriptions"]
    await jds.create_index([("created_time", DESCENDING)], name="idx_created_time")
    logger.info("Indexes created for 'job_descriptions' collection.")


def get_database() -> AsyncIOMotorDatabase:
    """Dependency: returns the active database handle."""
    if _database is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return _database
