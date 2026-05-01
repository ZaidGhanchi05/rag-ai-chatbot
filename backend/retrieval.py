"""
retrieval.py
─────────────────────────────────────────────────────────────────────────────
Hybrid retrieval engine combining:
  1. Semantic search  – FAISS + sentence-transformers embeddings
  2. Keyword search   – scikit-learn TF-IDF (TfidfVectorizer + cosine_similarity)

Final ranking score = 0.7 × semantic_score + 0.3 × tfidf_score

Using scikit-learn here demonstrates ML engineering skills:
  • TfidfVectorizer  : classic NLP feature extraction
  • cosine_similarity: pairwise similarity from sklearn.metrics.pairwise
  • normalize        : L2 normalisation for stable scoring

Edge cases handled:
  • Empty vector store (no documents uploaded)
  • Low-confidence results (score below threshold)
  • TF-IDF failure (falls back to semantic-only)
"""

import os
import logging
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize as sk_normalize

from vector_store import get_vector_store

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
TOP_K = int(os.getenv("TOP_K", "5"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))

# Semantic vs keyword weighting (must sum to 1.0)
SEMANTIC_WEIGHT = 0.70
TFIDF_WEIGHT = 0.30


# ── Main retrieval function ───────────────────────────────────────────────────

def hybrid_retrieve(query: str, top_k: int = TOP_K) -> dict[str, Any]:
    """
    Perform hybrid RAG retrieval and return a structured response.

    Steps:
      1. Semantic FAISS search (fetch 2× top_k for re-ranking headroom)
      2. TF-IDF keyword scoring over the candidate pool
      3. Fuse scores and re-rank
      4. Assess confidence, build answer + sources

    Returns:
        {
            "answer"          : str,
            "sources"         : list[str],
            "confidence"      : float,
            "matched_chunks"  : list[dict],
            "low_confidence"  : bool,
            "retrieval_method": str,
        }
    """
    store = get_vector_store()

    # ── Guard: no documents yet ───────────────────────────────────────────────
    if store.index.ntotal == 0:
        return _empty_response("No documents have been uploaded yet. Please upload PDFs first.")

    # ── Step 1 : Semantic retrieval via FAISS ─────────────────────────────────
    # Retrieve 2× top_k candidates for re-ranking headroom
    candidates = store.search(query, top_k=top_k * 2)
    if not candidates:
        return _empty_response("No relevant information found in the uploaded documents.")

    corpus = [c["chunk"] for c in candidates]

    # ── Step 2 : TF-IDF keyword scoring via scikit-learn ─────────────────────
    tfidf_scores = _tfidf_score(query, corpus)

    # ── Step 3 : Hybrid score fusion ──────────────────────────────────────────
    for i, candidate in enumerate(candidates):
        semantic = candidate["confidence"]          # already in [0, 1]
        keyword = float(tfidf_scores[i])            # cosine ∈ [0, 1]
        candidate["hybrid_score"] = (
            SEMANTIC_WEIGHT * semantic + TFIDF_WEIGHT * keyword
        )

    ranked = sorted(candidates, key=lambda x: x["hybrid_score"], reverse=True)[:top_k]

    # ── Step 4 : Confidence assessment ────────────────────────────────────────
    best_score = ranked[0]["hybrid_score"]
    low_confidence = best_score < CONFIDENCE_THRESHOLD

    # ── Step 5 : Build structured response ───────────────────────────────────
    answer = _build_answer(ranked, low_confidence)
    sources = _deduplicate_sources(ranked)
    matched_chunks = _format_chunks(ranked)

    return {
        "answer": answer,
        "sources": sources,
        "confidence": round(best_score, 4),
        "matched_chunks": matched_chunks,
        "low_confidence": low_confidence,
        "retrieval_method": "Hybrid (FAISS semantic + sklearn TF-IDF)",
    }


# ── TF-IDF helper (scikit-learn) ──────────────────────────────────────────────

def _tfidf_score(query: str, corpus: list[str]) -> np.ndarray:
    """
    Compute cosine similarity between query and each corpus document
    using sklearn's TfidfVectorizer.

    Returns:
        1-D array of shape (len(corpus),) with scores in [0, 1].
    """
    if not corpus:
        return np.array([])
    try:
        # Unigrams + bigrams; remove English stop words
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,       # apply log(1 + tf) scaling
        )
        # Fit on corpus, transform both corpus and query
        tfidf_matrix = vectorizer.fit_transform(corpus)         # shape: (n, vocab)
        query_vec = vectorizer.transform([query])               # shape: (1, vocab)

        # sklearn cosine_similarity → shape (1, n_corpus)
        scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

        # L2-normalise to keep scores in a stable [0, 1] range
        if scores.max() > 0:
            scores = scores / scores.max()

        return scores

    except Exception as exc:
        logger.warning(f"TF-IDF scoring failed ({exc}). Using zeros.")
        return np.zeros(len(corpus))


# ── Response building helpers ─────────────────────────────────────────────────

def _build_answer(ranked: list[dict], low_confidence: bool) -> str:
    """Compose the answer string from top chunks."""
    if low_confidence:
        return (
            "⚠️ I couldn't find highly relevant information for your query "
            "in the uploaded documents.\n\nClosest match found:\n\n"
            + ranked[0]["chunk"]
        )
    # Combine top 2 chunks (from different sources when possible)
    seen_docs: set[str] = set()
    parts: list[str] = []
    for r in ranked[:3]:
        fname = r["metadata"].get("filename", "Document")
        parts.append(f"**[Source: {fname}]**\n{r['chunk']}")
        seen_docs.add(fname)
        if len(parts) >= 2 and len(seen_docs) >= 2:
            break   # two distinct sources is enough for a rich answer
    return "\n\n---\n\n".join(parts)


def _deduplicate_sources(ranked: list[dict]) -> list[str]:
    """Return unique source filenames in order of relevance."""
    seen: set[str] = set()
    sources: list[str] = []
    for r in ranked:
        fname = r["metadata"].get("filename", "Unknown")
        if fname not in seen:
            seen.add(fname)
            sources.append(fname)
    return sources


def _format_chunks(ranked: list[dict]) -> list[dict]:
    """Serialise matched chunks for the frontend."""
    return [
        {
            "text": r["chunk"],
            "source": r["metadata"].get("filename", "Unknown"),
            "page": r["metadata"].get("page"),
            "confidence": round(r["hybrid_score"], 4),
            "doc_id": r["metadata"].get("doc_id", ""),
        }
        for r in ranked
    ]


def _empty_response(message: str) -> dict[str, Any]:
    return {
        "answer": message,
        "sources": [],
        "confidence": 0.0,
        "matched_chunks": [],
        "low_confidence": True,
        "retrieval_method": "none",
    }
