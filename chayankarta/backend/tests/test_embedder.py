"""
Tests for the embedding service (Milestone 4).

Tests:
- embed_text returns correct shape (384-dim for all-MiniLM-L6-v2)
- embed_text is deterministic (same text → same vector)
- cosine_similarity of identical vectors = 1.0
- cosine_similarity of zero-ish vectors clipped to 0.0
- embed_texts batch is equivalent to per-item embed_text
"""

import pytest
import numpy as np


# We mock the sentence-transformers model to avoid loading the real model in CI.
# Individual integration tests can use @pytest.mark.integration to skip mocking.


class _FakeModel:
    """Deterministic fake SentenceTransformer for unit tests."""

    DIM = 384

    def get_sentence_embedding_dimension(self):
        return self.DIM

    def encode(self, sentences, normalize_embeddings=True, show_progress_bar=False, batch_size=32):
        import hashlib
        if isinstance(sentences, str):
            sentences = [sentences]
        vecs = []
        for s in sentences:
            seed = int(hashlib.md5(s.encode()).hexdigest(), 16) % (2**31)
            rng = np.random.default_rng(seed)
            v = rng.standard_normal(self.DIM).astype(np.float32)
            if normalize_embeddings:
                norm = np.linalg.norm(v)
                if norm > 0:
                    v = v / norm
            vecs.append(v)
        return np.array(vecs) if len(vecs) > 1 else vecs[0]


@pytest.fixture(autouse=True)
def patch_model(monkeypatch):
    """Replace the real SentenceTransformer with the fake one for all tests here."""
    import app.services.embedder as embedder_mod
    # The session-scoped conftest fixture may have already replaced _get_model
    # with a plain lambda (no lru_cache), so cache_clear() might not exist.
    if hasattr(embedder_mod._get_model, "cache_clear"):
        embedder_mod._get_model.cache_clear()
    monkeypatch.setattr(embedder_mod, "_get_model", lambda: _FakeModel())


def test_embed_text_shape():
    from app.services.embedder import embed_text
    vec = embed_text("Hello world")
    assert isinstance(vec, list)
    assert len(vec) == 384


def test_embed_text_deterministic():
    from app.services.embedder import embed_text
    text = "Python developer with 5 years of experience"
    v1 = embed_text(text)
    v2 = embed_text(text)
    assert v1 == v2, "embed_text must return identical vectors for the same input"


def test_embed_text_different_texts():
    from app.services.embedder import embed_text
    v1 = embed_text("Machine learning engineer")
    v2 = embed_text("Accountant with finance background")
    # Different texts should produce different vectors
    assert v1 != v2


def test_cosine_similarity_identical():
    from app.services.embedder import cosine_similarity, embed_text
    vec = embed_text("test text")
    sim = cosine_similarity(vec, vec)
    assert abs(sim - 1.0) < 1e-4, f"cosine_similarity(v, v) should be ~1.0, got {sim}"


def test_cosine_similarity_range():
    from app.services.embedder import cosine_similarity, embed_text
    v1 = embed_text("software engineer python")
    v2 = embed_text("nurse healthcare hospital")
    sim = cosine_similarity(v1, v2)
    assert 0.0 <= sim <= 1.0


def test_cosine_similarity_clipped():
    from app.services.embedder import cosine_similarity
    # Force a case that might produce slightly negative dot product
    a = [1.0, 0.0]
    b = [-1.0, 0.0]
    sim = cosine_similarity(a, b)
    assert sim == 0.0, "cosine_similarity should clip negative values to 0.0"


def test_embed_texts_batch_matches_single():
    from app.services.embedder import embed_text, embed_texts
    texts = ["Python developer", "Java developer", "Data scientist"]
    batch = embed_texts(texts)
    singles = [embed_text(t) for t in texts]
    assert len(batch) == len(texts)
    for b, s in zip(batch, singles):
        assert b == s, "Batch embedding should match per-item embedding"


def test_embed_texts_empty():
    from app.services.embedder import embed_texts
    result = embed_texts([])
    assert result == []
