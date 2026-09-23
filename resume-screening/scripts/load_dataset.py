"""
Load the Kaggle Resume Dataset CSV into MongoDB.

Reads the CSV, cleans it, runs NER extraction on each resume,
and inserts the results into the 'resumes' collection.

Prerequisites:
    - MongoDB must be running (locally or via docker-compose)
    - Dataset CSV must exist in data/raw/ (run download_dataset.py first)
    - Python packages: pandas, pymongo, spacy

Usage:
    python scripts/load_dataset.py [--csv-path data/raw/Resume/Resume.csv]
                                   [--mongodb-url mongodb://localhost:27017]
                                   [--db-name resume_screening]
                                   [--batch-size 50]
"""

import argparse
import html
import logging
import os
import re
import sys
import uuid
from datetime import datetime, timezone

import pandas as pd
from pymongo import MongoClient

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.ner import extract_entities

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Clean and normalize resume text."""
    if not isinstance(text, str):
        return ""

    # Decode HTML entities
    text = html.unescape(text)

    # Remove HTML tags (the dataset has Resume_html column, but Resume_str may also contain fragments)
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def load_dataset(
    csv_path: str = "data/raw/Resume/Resume.csv",
    mongodb_url: str = "mongodb://localhost:27017",
    db_name: str = "resume_screening",
    batch_size: int = 50,
) -> None:
    """Load the resume CSV into MongoDB with NER extraction."""

    # --- Read CSV ---
    if not os.path.exists(csv_path):
        logger.error("CSV not found at '%s'. Run download_dataset.py first.", csv_path)
        sys.exit(1)

    logger.info("Reading CSV from '%s' ...", csv_path)
    df = pd.read_csv(csv_path)
    logger.info("Read %d rows. Columns: %s", len(df), list(df.columns))

    # --- Clean ---
    initial_count = len(df)

    # Drop rows with null Resume_str
    df = df.dropna(subset=["Resume_str"])
    logger.info("Dropped %d rows with null Resume_str", initial_count - len(df))

    # Drop duplicate resumes
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["Resume_str"])
    logger.info("Dropped %d duplicate resumes", before_dedup - len(df))

    # Clean text
    df["Resume_str"] = df["Resume_str"].apply(clean_text)

    # Drop very short resumes (likely garbage)
    df = df[df["Resume_str"].str.len() >= 100]
    logger.info("After cleaning: %d resumes remaining", len(df))

    # --- Connect to MongoDB ---
    logger.info("Connecting to MongoDB at '%s' ...", mongodb_url)
    client = MongoClient(mongodb_url)
    db = client[db_name]
    collection = db["resumes"]

    # --- Insert ---
    inserted = 0
    skipped = 0
    errors = 0

    for i, (_, row) in enumerate(df.iterrows()):
        try:
            resume_text = row["Resume_str"]
            category = row.get("Category", None)

            # Check if already loaded (by category + first 200 chars as a rough dedup)
            # In production you'd use a proper hash
            existing = collection.find_one({
                "raw_text": {"$regex": f"^{re.escape(resume_text[:100])}"}
            })
            if existing:
                skipped += 1
                continue

            # Run NER
            ner_result = extract_entities(resume_text, category=category)

            doc = {
                "_id": str(uuid.uuid4()),
                "filename": f"kaggle_resume_{row.get('ID', i)}.csv",
                "file_type": "csv",
                "raw_text": resume_text,
                "parsing_method": "kaggle_csv",
                "upload_time": datetime.now(timezone.utc),
                "ner": ner_result.model_dump(),
            }

            collection.insert_one(doc)
            inserted += 1

            if (inserted) % batch_size == 0:
                logger.info("Progress: %d/%d inserted, %d skipped", inserted, len(df), skipped)

        except Exception as exc:
            errors += 1
            logger.warning("Error processing row %d: %s", i, exc)
            continue

    logger.info(
        "Loading complete: %d inserted, %d skipped, %d errors (total rows: %d)",
        inserted,
        skipped,
        errors,
        len(df),
    )
    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Kaggle Resume Dataset into MongoDB")
    parser.add_argument("--csv-path", default="data/raw/Resume/Resume.csv", help="Path to CSV")
    parser.add_argument("--mongodb-url", default="mongodb://localhost:27017", help="MongoDB URL")
    parser.add_argument("--db-name", default="resume_screening", help="Database name")
    parser.add_argument("--batch-size", type=int, default=50, help="Progress log interval")
    args = parser.parse_args()

    load_dataset(args.csv_path, args.mongodb_url, args.db_name, args.batch_size)
