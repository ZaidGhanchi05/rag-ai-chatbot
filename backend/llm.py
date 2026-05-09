"""
llm.py
─────────────────────────────────────────────────────────────────────────────
Groq LLM integration for synthesizing answers from retrieved document chunks.

Two modes:
  1. Stream mode  – yields token strings via a generator (for SSE endpoint)
  2. Sync mode    – returns a complete answer string (for non-streaming endpoint)

Fallback:
  If GROQ_API_KEY is not set, both functions gracefully fall back to returning
  the raw retrieved chunks formatted as a readable answer.

Model used: llama3-8b-8192 (fast, free-tier friendly on Groq)
"""

import os
import logging
from typing import Generator, Any

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# System prompt that instructs the LLM to behave as a document QA assistant
_SYSTEM_PROMPT = """You are an expert document assistant. Your job is to answer the user's question \
accurately and concisely using ONLY the provided document context.

Rules:
- Answer ONLY from the provided context — do not use any outside knowledge.
- If the context does not contain enough information, say so clearly.
- Keep answers focused, factual, and well-structured.
- Cite which document/source the information comes from when possible.
- Use markdown formatting (bold, bullet points) where it improves readability.
- Do NOT repeat the question in your answer.
"""


def _build_context_block(matched_chunks: list[dict[str, Any]]) -> str:
    """Format retrieved chunks into a numbered context block for the prompt."""
    parts = []
    for i, chunk in enumerate(matched_chunks, start=1):
        source = chunk.get("source", "Unknown")
        page = chunk.get("page")
        text = chunk.get("text", "")
        page_str = f", Page {page}" if page else ""
        parts.append(f"[Context {i} — {source}{page_str}]\n{text}")
    return "\n\n".join(parts)


def _fallback_answer(matched_chunks: list[dict[str, Any]], low_confidence: bool) -> str:
    """Return raw chunks formatted nicely when no LLM is available."""
    if low_confidence or not matched_chunks:
        top = matched_chunks[0]["text"] if matched_chunks else "No relevant content found."
        return (
            "⚠️ I couldn't find highly relevant information for your query "
            "in the uploaded documents.\n\nClosest match found:\n\n" + top
        )
    parts = []
    seen: set[str] = set()
    for chunk in matched_chunks[:3]:
        src = chunk.get("source", "Document")
        parts.append(f"**[Source: {src}]**\n{chunk['text']}")
        seen.add(src)
        if len(parts) >= 2 and len(seen) >= 2:
            break
    return "\n\n---\n\n".join(parts)


# ── Synchronous answer generation ─────────────────────────────────────────────

def generate_answer(
    query: str,
    matched_chunks: list[dict[str, Any]],
    low_confidence: bool = False,
) -> str:
    """
    Generate a complete answer string using Groq LLM.

    Falls back to formatted raw chunks if GROQ_API_KEY is not set.

    Args:
        query          : Original user question.
        matched_chunks : Retrieved context chunks from hybrid_retrieve().
        low_confidence : Whether retrieval confidence was below threshold.

    Returns:
        Answer string (markdown-formatted).
    """
    if not GROQ_API_KEY:
        logger.info("GROQ_API_KEY not set — using fallback chunk answer.")
        return _fallback_answer(matched_chunks, low_confidence)

    if low_confidence or not matched_chunks:
        return _fallback_answer(matched_chunks, low_confidence)

    try:
        from groq import Groq  # lazy import — only needed when key is available
        client = Groq(api_key=GROQ_API_KEY)

        context = _build_context_block(matched_chunks)
        user_message = f"Context:\n{context}\n\nQuestion: {query}"

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,      # low temperature for factual QA
            max_tokens=1024,
        )
        answer = response.choices[0].message.content or ""
        logger.info(f"Groq answer generated ({len(answer)} chars)")
        return answer

    except Exception as exc:
        logger.error(f"Groq API call failed: {exc}")
        # Graceful degradation — never crash the endpoint
        return _fallback_answer(matched_chunks, low_confidence)


# ── Streaming answer generation ────────────────────────────────────────────────

def stream_answer(
    query: str,
    matched_chunks: list[dict[str, Any]],
    low_confidence: bool = False,
) -> Generator[str, None, None]:
    """
    Stream an LLM answer token-by-token via a generator.

    If GROQ_API_KEY is not set, yields the full fallback answer in one chunk.

    Usage (in FastAPI):
        return StreamingResponse(stream_answer(...), media_type="text/event-stream")

    Yields:
        Raw token strings (each is a fragment of the final answer).
    """
    if not GROQ_API_KEY or low_confidence or not matched_chunks:
        # Yield the fallback in one shot — frontend handles it gracefully
        yield _fallback_answer(matched_chunks, low_confidence)
        return

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        context = _build_context_block(matched_chunks)
        user_message = f"Context:\n{context}\n\nQuestion: {query}"

        stream = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            max_tokens=1024,
            stream=True,   # ← key: Groq streaming mode
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    except Exception as exc:
        logger.error(f"Groq streaming failed: {exc}")
        yield _fallback_answer(matched_chunks, low_confidence)
