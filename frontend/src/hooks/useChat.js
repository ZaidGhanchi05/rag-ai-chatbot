import { useState, useCallback } from "react";
import { streamQuery } from "../services/api";

/**
 * useChat hook
 * Manages conversation history and handles sending messages.
 *
 * Uses REAL server-sent event (SSE) streaming from the backend:
 *  1. Sends query to /query/stream
 *  2. Receives a "meta" event immediately (sources, confidence, chunks)
 *  3. Receives token events one-by-one as Groq generates the answer
 *  4. Receives "done" event when streaming is complete
 *
 * This gives a genuine ChatGPT-like streaming experience.
 */
export function useChat() {
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hello! I'm your RAG AI assistant powered by Groq LLM. Upload PDFs using the sidebar, then ask me anything about their content.",
      sources: [],
      confidence: null,
      matched_chunks: [],
      low_confidence: false,
      retrieval_method: "",
      timestamp: new Date(),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = useCallback(
    async (query) => {
      if (!query.trim() || isLoading) return;

      // ── Add user message immediately ──────────────────────────────────────
      const userMsg = {
        id: `user-${Date.now()}`,
        role: "user",
        content: query,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      // ── Create empty AI message placeholder ───────────────────────────────
      const aiMsgId = `ai-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        {
          id: aiMsgId,
          role: "assistant",
          content: "",
          sources: [],
          confidence: null,
          matched_chunks: [],
          low_confidence: false,
          retrieval_method: "",
          timestamp: new Date(),
          typing: true,   // shows the blinking cursor / typing indicator
        },
      ]);

      // ── Stream via SSE ────────────────────────────────────────────────────
      await streamQuery(query, 5, {
        // Metadata arrives first — populate sources/confidence before text
        onMeta: (meta) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMsgId
                ? {
                    ...m,
                    sources: meta.sources || [],
                    confidence: meta.confidence,
                    matched_chunks: meta.matched_chunks || [],
                    low_confidence: meta.low_confidence,
                    retrieval_method: meta.retrieval_method,
                  }
                : m
            )
          );
        },

        // Each token appended to the message content in real time
        onToken: (token) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMsgId ? { ...m, content: m.content + token } : m
            )
          );
        },

        // Stream finished — remove typing cursor
        onDone: () => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMsgId ? { ...m, typing: false } : m
            )
          );
          setIsLoading(false);
        },

        // Error — replace the empty placeholder with an error message
        onError: (err) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMsgId
                ? {
                    ...m,
                    content: `❌ Error: ${err.message || "Something went wrong."}`,
                    typing: false,
                    isError: true,
                  }
                : m
            )
          );
          setIsLoading(false);
        },
      });
    },
    [isLoading]
  );

  const clearChat = useCallback(() => {
    setMessages((prev) => [prev[0]]); // keep welcome message
  }, []);

  return { messages, isLoading, sendMessage, clearChat };
}
