"""
embedding.py
─────────────────────────────────────────────────────────────────────────────
Handles all text-to-vector conversion using the sentence-transformers library.
Model: all-MiniLM-L6-v2  →  384-dimensional dense vectors

Uses a singleton pattern so the model is loaded only once per process.
"""

import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ── Singleton model handle ────────────────────────────────────────────────────
_model: SentenceTransformer | None = None

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # fixed output dimension for this model


def get_model() -> SentenceTransformer:
    """
    Lazy-load the sentence-transformer model (singleton).
    First call downloads / loads from cache; subsequent calls return instantly.
    """
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Embedding model loaded successfully.")
    return _model


def get_embedding(text: str) -> np.ndarray:
    """
    Encode a single text string into a 384-d float32 numpy vector.

    Args:
        text: Raw string to embed.

    Returns:
        np.ndarray of shape (384,)
    """
    model = get_model()
    return model.encode(text, convert_to_numpy=True, normalize_embeddings=True)


def get_embeddings(texts: list[str]) -> np.ndarray:
    """
    Batch encode a list of text strings.
    Normalised embeddings improve cosine similarity comparisons.

    Args:
        texts: List of strings to embed.

    Returns:
        np.ndarray of shape (len(texts), 384)
    """
    model = get_model()
    show_bar = len(texts) > 20  # only show progress bar for large batches
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=show_bar,
        batch_size=32,
    )
    return embeddings
