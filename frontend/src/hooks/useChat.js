import { useState, useCallback } from "react";
import { sendQuery } from "../services/api";

/**
 * useChat hook
 * Manages the conversation history and handles sending messages.
 * Implements a word-by-word typing animation to simulate streaming.
 */
export function useChat() {
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hello! I'm your RAG AI assistant. Upload PDFs using the sidebar, then ask me anything about their content.",
      sources: [],
      confidence: null,
      matched_chunks: [],
      low_confidence: false,
      retrieval_method: "",
      timestamp: new Date(),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = useCallback(async (query) => {
    if (!query.trim() || isLoading) return;

    // Add user message immediately
    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user",
      content: query,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setError(null);

    try {
      const data = await sendQuery(query);

      // Add placeholder AI message that we'll "type" into
      const aiMsgId = `ai-${Date.now()}`;
      const fullContent = data.answer;

      setMessages((prev) => [
        ...prev,
        {
          id: aiMsgId,
          role: "assistant",
          content: "",           // starts empty — filled by typing animation
          fullContent,
          sources: data.sources || [],
          confidence: data.confidence,
          matched_chunks: data.matched_chunks || [],
          low_confidence: data.low_confidence,
          retrieval_method: data.retrieval_method,
          timestamp: new Date(),
          typing: true,
        },
      ]);

      // Word-by-word reveal animation (simulates streaming)
      const words = fullContent.split(" ");
      let built = "";
      for (let i = 0; i < words.length; i++) {
        built += (i > 0 ? " " : "") + words[i];
        const current = built;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsgId ? { ...m, content: current } : m
          )
        );
        // Variable delay for a natural feel
        await sleep(i < 3 ? 60 : 30);
      }

      // Mark typing as done
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMsgId ? { ...m, typing: false } : m
        )
      );
    } catch (err) {
      setError(err.message || "Something went wrong.");
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: `❌ Error: ${err.message}`,
          sources: [],
          confidence: null,
          matched_chunks: [],
          timestamp: new Date(),
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  const clearChat = useCallback(() => {
    setMessages((prev) => [prev[0]]); // keep welcome message
    setError(null);
  }, []);

  return { messages, isLoading, error, sendMessage, clearChat };
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
