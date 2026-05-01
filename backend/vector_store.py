"""
vector_store.py
─────────────────────────────────────────────────────────────────────────────
FAISS-based vector store with full persistence support.

Design decisions:
  - IndexFlatL2  : exact nearest-neighbour search; ideal for < 500k vectors
  - Parallel metadata list : mirrors FAISS index positions 1-to-1
  - save / load  : writes index.faiss + metadata.pkl so nothing is
                   re-computed when the server restarts
"""

import os
import pickle
import logging
from typing import Any

import faiss
import numpy as np

from embedding import get_embedding, get_embeddings, EMBEDDING_DIM

logger = logging.getLogger(__name__)

INDEX_DIR = os.getenv("INDEX_DIR", "./data/index")


class VectorStore:
    """
    Wraps a FAISS IndexFlatL2 with a parallel metadata list.

    Each position i in self.metadata corresponds to FAISS vector i,
    storing: text, doc_id, filename, page number.
    """

    def __init__(self, dimension: int = EMBEDDING_DIM) -> None:
        self.dimension = dimension
        # IndexFlatL2 = exact brute-force L2 search (no approximation)
        self.index = faiss.IndexFlatL2(dimension)
        # Parallel metadata list (same order as FAISS internal vectors)
        self.metadata: list[dict[str, Any]] = []
        logger.info(f"VectorStore ready  (dim={dimension})")

    # ── Indexing ──────────────────────────────────────────────────────────────

    def add_documents(
        self,
        chunks: list[str],
        metadata: list[dict[str, Any]],
    ) -> None:
        """
        Embed text chunks and add them to the FAISS index.

        Args:
            chunks   : Raw text strings (one per chunk).
            metadata : Parallel list of dicts with keys:
                       text, doc_id, filename, page.
        """
        if not chunks:
            return
        embeddings = get_embeddings(chunks)
        # FAISS requires contiguous float32 array
        embeddings = np.array(embeddings, dtype=np.float32)
        self.index.add(embeddings)
        self.metadata.extend(metadata)
        logger.info(
            f"Added {len(chunks)} chunks  |  total vectors: {self.index.ntotal}"
        )

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def search(
        self, query: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Perform vector similarity search.

        Returns list of dicts with keys:
            chunk, distance, confidence, metadata
        where confidence = 1 / (1 + L2_distance)  (range 0–1, higher = better)
        """
        if self.index.ntotal == 0:
            return []

        query_vec = get_embedding(query)
        query_vec = np.array([query_vec], dtype=np.float32)

        actual_k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_vec, actual_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:        # FAISS marks empty slots as -1
                continue
            meta = self.metadata[idx]
            results.append(
                {
                    "chunk": meta.get("text", ""),
                    "distance": float(dist),
                    # Normalise L2 distance → confidence score in [0, 1]
                    "confidence": float(1.0 / (1.0 + dist)),
                    "metadata": {k: v for k, v in meta.items() if k != "text"},
                }
            )
        return results

    # ── Document management ───────────────────────────────────────────────────

    def remove_document(self, doc_id: str) -> int:
        """
        Remove all chunks belonging to doc_id.
        FAISS IndexFlatL2 doesn't support in-place deletion,
        so we rebuild the index from the remaining vectors.
        """
        keep_idx = [
            i for i, m in enumerate(self.metadata) if m.get("doc_id") != doc_id
        ]
        removed = len(self.metadata) - len(keep_idx)
        if removed == 0:
            return 0

        kept_meta = [self.metadata[i] for i in keep_idx]
        kept_texts = [m["text"] for m in kept_meta]

        # Rebuild
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        if kept_texts:
            self.add_documents(kept_texts, kept_meta)

        logger.info(f"Removed {removed} chunks for doc_id={doc_id!r}")
        return removed

    def get_all_documents(self) -> list[dict[str, Any]]:
        """Return one summary dict per unique document."""
        seen: dict[str, dict] = {}
        for m in self.metadata:
            doc_id = m.get("doc_id", "")
            if doc_id and doc_id not in seen:
                seen[doc_id] = {
                    "doc_id": doc_id,
                    "filename": m.get("filename", "Unknown"),
                    "chunk_count": 0,
                }
            if doc_id in seen:
                seen[doc_id]["chunk_count"] += 1
        return list(seen.values())

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, directory: str = INDEX_DIR) -> None:
        """Persist the FAISS index + metadata to disk."""
        os.makedirs(directory, exist_ok=True)
        faiss.write_index(self.index, os.path.join(directory, "index.faiss"))
        with open(os.path.join(directory, "metadata.pkl"), "wb") as f:
            pickle.dump(self.metadata, f)
        logger.info(f"VectorStore saved  ({self.index.ntotal} vectors → {directory})")

    def load(self, directory: str = INDEX_DIR) -> bool:
        """
        Load FAISS index + metadata from disk.
        Returns True if loaded successfully, False if no saved data exists.
        """
        index_path = os.path.join(directory, "index.faiss")
        meta_path = os.path.join(directory, "metadata.pkl")
        if os.path.exists(index_path) and os.path.exists(meta_path):
            self.index = faiss.read_index(index_path)
            with open(meta_path, "rb") as f:
                self.metadata = pickle.load(f)
            logger.info(
                f"VectorStore loaded  ({self.index.ntotal} vectors ← {directory})"
            )
            return True
        logger.info("No saved VectorStore found — starting fresh.")
        return False


# ── Module-level singleton ────────────────────────────────────────────────────
_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Return (and lazily initialise) the global VectorStore singleton."""
    global _store
    if _store is None:
        _store = VectorStore()
        _store.load()   # restore persisted data if available
    return _store
