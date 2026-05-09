"""
api.py
─────────────────────────────────────────────────────────────────────────────
FastAPI application — entry point for the RAG chatbot backend.

Endpoints:
  GET  /health              — health check
  POST /upload              — upload + index PDFs
  POST /query               — semantic query → RAG response
  GET  /documents           — list all indexed documents
  DELETE /documents/{doc_id}— remove a document from the index

Architecture:
  PDF → PyPDF text extraction → overlapping chunking →
  sentence-transformers embedding → FAISS index + sklearn TF-IDF retrieval
"""

import json
import os
import uuid
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pypdf import PdfReader
from dotenv import load_dotenv

from vector_store import get_vector_store
from retrieval import hybrid_retrieve
from llm import stream_answer

# ── Bootstrap ─────────────────────────────────────────────────────────────────
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s  —  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Config from env ───────────────────────────────────────────────────────────
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./data/uploads"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
TOP_K = int(os.getenv("TOP_K", "5"))

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="RAG AI Chatbot",
    description="Production-ready Retrieval-Augmented Generation API "
                "(FAISS + sentence-transformers + sklearn TF-IDF)",
    version="1.0.0",
)

# Allow all origins during development — tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic models ───────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    top_k: int = TOP_K


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float
    matched_chunks: list[dict[str, Any]]
    low_confidence: bool = False
    retrieval_method: str = ""


# ── PDF helpers ───────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: Path) -> list[dict[str, Any]]:
    """
    Extract text from every page of a PDF using PyPDF.

    Returns:
        List of {"text": str, "page": int} dicts (one per non-empty page).
    """
    reader = PdfReader(str(file_path))
    pages = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append({"text": text, "page": page_num})
    return pages


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping windows.

    Overlap preserves sentence context at chunk boundaries — critical for
    accurate retrieval when an answer spans two chunks.

    Args:
        text       : Full text string to split.
        chunk_size : Maximum characters per chunk.
        overlap    : Characters shared between consecutive chunks.

    Returns:
        List of non-empty text chunks.
    """
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        # Slide window forward, keeping `overlap` chars for context continuity
        start += chunk_size - overlap
    return chunks


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Utility"])
def health_check() -> dict:
    """Simple health check — returns OK if server is running."""
    store = get_vector_store()
    return {
        "status": "ok",
        "version": "1.0.0",
        "total_vectors": store.index.ntotal,
        "total_documents": len(store.get_all_documents()),
    }


@app.post("/upload", tags=["Documents"])
async def upload_pdfs(files: list[UploadFile] = File(...)) -> dict:
    """
    Upload one or more PDF files.

    For each PDF:
      1. Save to disk
      2. Extract text page-by-page (PyPDF)
      3. Split into overlapping chunks
      4. Embed with sentence-transformers
      5. Index in FAISS
      6. Persist index to disk immediately

    Returns a summary of each indexed document.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    store = get_vector_store()
    uploaded: list[dict] = []

    for file in files:
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"'{file.filename}' is not a PDF file.",
            )

        # ── Save to disk ──────────────────────────────────────────────────────
        doc_id = str(uuid.uuid4())
        save_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"
        raw = await file.read()
        save_path.write_bytes(raw)
        logger.info(f"Saved upload: {file.filename} → {save_path}")

        # ── Extract text ──────────────────────────────────────────────────────
        try:
            pages = extract_text_from_pdf(save_path)
        except Exception as exc:
            logger.error(f"PDF extraction failed for '{file.filename}': {exc}")
            raise HTTPException(
                status_code=422,
                detail=f"Could not read '{file.filename}': {exc}",
            )

        if not pages:
            logger.warning(f"No extractable text in '{file.filename}' — skipping.")
            continue

        # ── Chunk + embed + index ─────────────────────────────────────────────
        all_chunks: list[str] = []
        all_meta: list[dict] = []
        for page in pages:
            for chunk in chunk_text(page["text"]):
                all_chunks.append(chunk)
                all_meta.append(
                    {
                        "text": chunk,
                        "doc_id": doc_id,
                        "filename": file.filename,
                        "page": page["page"],
                    }
                )

        store.add_documents(all_chunks, all_meta)
        store.save()          # persist immediately so progress survives restart

        logger.info(
            f"Indexed {len(all_chunks)} chunks from '{file.filename}' "
            f"({len(pages)} pages)"
        )
        uploaded.append(
            {
                "doc_id": doc_id,
                "filename": file.filename,
                "pages": len(pages),
                "chunks": len(all_chunks),
            }
        )

    return {
        "uploaded": uploaded,
        "total_vectors": store.index.ntotal,
    }


@app.post("/query", response_model=QueryResponse, tags=["Retrieval"])
def query_documents(request: QueryRequest) -> QueryResponse:
    """
    Accept a natural-language query and return a RAG response.

    Uses hybrid retrieval:
      - FAISS semantic search (sentence-transformers embeddings)
      - sklearn TF-IDF re-ranking (keyword relevance)

    Response includes answer text, source PDFs, confidence score,
    and the individual matched chunks for UI display.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    logger.info(f"Query: {request.query[:100]!r}")
    result = hybrid_retrieve(request.query, top_k=request.top_k)
    return QueryResponse(**result)


class StreamQueryRequest(BaseModel):
    query: str
    top_k: int = TOP_K


@app.post("/query/stream", tags=["Retrieval"])
def query_documents_stream(request: StreamQueryRequest):
    """
    Stream a RAG answer token-by-token using Server-Sent Events (SSE).

    First emits a JSON metadata event with sources/confidence/chunks,
    then streams the LLM answer text, finally sends a [DONE] sentinel.

    Frontend should consume this with the EventSource or fetch + ReadableStream API.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    logger.info(f"Stream query: {request.query[:100]!r}")

    def event_generator():
        # Step 1: retrieve context (fast, sync)
        result = hybrid_retrieve(request.query, top_k=request.top_k)

        # Step 2: emit metadata as first SSE event so the UI can show sources
        # immediately before the answer starts streaming
        meta = {
            "type": "meta",
            "sources": result["sources"],
            "confidence": result["confidence"],
            "matched_chunks": result["matched_chunks"],
            "low_confidence": result["low_confidence"],
            "retrieval_method": result["retrieval_method"],
        }
        yield f"data: {json.dumps(meta)}\n\n"

        # Step 3: stream LLM tokens
        for token in stream_answer(
            request.query,
            result["matched_chunks"],
            result["low_confidence"],
        ):
            payload = json.dumps({"type": "token", "text": token})
            yield f"data: {payload}\n\n"

        # Step 4: signal completion
        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering
        },
    )


@app.get("/documents", tags=["Documents"])
def list_documents() -> dict:
    """List all documents currently in the vector store."""
    store = get_vector_store()
    return {
        "documents": store.get_all_documents(),
        "total_vectors": store.index.ntotal,
    }


@app.delete("/documents/{doc_id}", tags=["Documents"])
def delete_document(doc_id: str) -> dict:
    """
    Remove all chunks belonging to a document from the vector store.
    Rebuilds the FAISS index (IndexFlatL2 does not support in-place deletion).
    """
    store = get_vector_store()
    removed = store.remove_document(doc_id)
    if removed == 0:
        raise HTTPException(status_code=404, detail="Document not found.")
    store.save()
    logger.info(f"Deleted doc_id={doc_id!r}, removed {removed} chunks.")
    return {
        "removed_chunks": removed,
        "total_vectors": store.index.ntotal,
    }
