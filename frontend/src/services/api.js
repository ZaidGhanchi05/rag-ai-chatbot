// API service layer
// All calls to the FastAPI backend go through here
// Supports both regular (sync) queries and real SSE streaming via /query/stream

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Upload one or more PDF files to the backend for indexing.
 * @param {File[]} files
 * @returns {Promise<object>} { uploaded: [...], total_vectors: number }
 */
export async function uploadPDFs(files) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const res = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed (${res.status})`);
  }
  return res.json();
}

/**
 * Send a query and receive a RAG response.
 * @param {string} query
 * @param {number} topK
 * @returns {Promise<object>} { answer, sources, confidence, matched_chunks, ... }
 */
export async function sendQuery(query, topK = 5) {
  const res = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: topK }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Query failed (${res.status})`);
  }
  return res.json();
}

/**
 * Fetch the list of documents currently in the vector store.
 * @returns {Promise<object>} { documents: [...], total_vectors: number }
 */
export async function getDocuments() {
  const res = await fetch(`${BASE_URL}/documents`);
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

/**
 * Delete a document from the vector store by its ID.
 * @param {string} docId
 * @returns {Promise<object>}
 */
export async function deleteDocument(docId) {
  const res = await fetch(`${BASE_URL}/documents/${docId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Delete failed");
  }
  return res.json();
}

/**
 * Health check
 */
export async function healthCheck() {
  const res = await fetch(`${BASE_URL}/health`);
  return res.json();
}

/**
 * Stream a RAG answer via SSE from /query/stream.
 *
 * @param {string}   query     - User question
 * @param {number}   topK      - Number of chunks to retrieve
 * @param {object}   callbacks
 * @param {function} callbacks.onMeta   - Called once with { sources, confidence, matched_chunks, ... }
 * @param {function} callbacks.onToken  - Called for each streamed text token
 * @param {function} callbacks.onDone   - Called when the stream is finished
 * @param {function} callbacks.onError  - Called if an error occurs
 */
export async function streamQuery(query, topK = 5, { onMeta, onToken, onDone, onError } = {}) {
  try {
    const res = await fetch(`${BASE_URL}/query/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: topK }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Stream query failed (${res.status})`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE lines end with \n\n; process complete events from the buffer
      const parts = buffer.split("\n\n");
      buffer = parts.pop(); // keep any incomplete trailing chunk

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) continue;
        const jsonStr = line.slice(5).trim();
        try {
          const event = JSON.parse(jsonStr);
          if (event.type === "meta" && onMeta) onMeta(event);
          else if (event.type === "token" && onToken) onToken(event.text);
          else if (event.type === "done" && onDone) onDone();
        } catch {
          // malformed event — skip silently
        }
      }
    }
  } catch (err) {
    if (onError) onError(err);
  }
}
