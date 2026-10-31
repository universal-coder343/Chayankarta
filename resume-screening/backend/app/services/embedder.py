"""
Embedding service using sentence-transformers.

Model: ``all-MiniLM-L6-v2``  (384-dimensional, fast, good quality)

The model is loaded lazily on first call and cached for the lifetime of
the process (lru_cache).  All encoding is done synchronously in the
calling thread — FastAPI can wrap it in a thread pool if needed (see
``run_in_executor`` pattern in the ranker).

Usage
-----
>>> from .embedder import embed_text, embed_texts, cosine_similarity
>>> vec = embed_text("Machine learning engineer with 5 years experience")
>>> sim = cosine_similarity(vec_a, vec_b)
"""

import logging
from functools import lru_cache

import numpy as np

logger = logging.getLogger(__name__)

_MODEL_NAME = "all-MiniLM-L6-v2"


# ---------------------------------------------------------------------------
# Model loader
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_model():
    """Load and cache the SentenceTransformer model (singleton)."""
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "sentence-transformers is not installed. "
            "Run: pip install sentence-transformers"
        ) from exc

    logger.info("Loading SentenceTransformer model '%s' …", _MODEL_NAME)
    model = SentenceTransformer(_MODEL_NAME)
    logger.info("SentenceTransformer model loaded (dim=%d).", model.get_sentence_embedding_dimension())
    return model


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def embed_text(text: str) -> list[float]:
    """
    Embed a single piece of text.

    The embedding is L2-normalised so that dot-product == cosine similarity.

    Args:
        text: Raw string to encode.

    Returns:
        A list of floats (length 384 for all-MiniLM-L6-v2).
    """
    model = _get_model()
    # normalize_embeddings=True → embeddings are unit-length
    vec: np.ndarray = model.encode(text, normalize_embeddings=True, show_progress_bar=False)
    return vec.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Batch-embed a list of texts (more efficient than calling embed_text in a loop).

    Args:
        texts: List of raw strings.

    Returns:
        List of embedding vectors (each a list[float]).
    """
    if not texts:
        return []
    model = _get_model()
    vecs: np.ndarray = model.encode(texts, normalize_embeddings=True, show_progress_bar=False, batch_size=32)
    return vecs.tolist()


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two normalised embedding vectors.

    Because the vectors are already L2-normalised, this is just a dot product.
    Clipped to [0, 1] to guard against floating-point drift.

    Args:
        vec_a: Normalised embedding vector.
        vec_b: Normalised embedding vector.

    Returns:
        Similarity in [0.0, 1.0].
    """
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    sim = float(np.dot(a, b))
    return max(0.0, min(1.0, sim))
