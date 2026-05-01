import { useEffect, useRef } from "react";
import ChatBubble from "./ChatBubble";
import TypingIndicator from "./TypingIndicator";
import ChatInput from "./ChatInput";

/**
 * ChatWindow component
 * Scrollable message list + input bar.
 */
export default function ChatWindow({ messages, isLoading, onSend, onClear }) {
  const bottomRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className="chat-window">
      {/* Top bar */}
      <div className="chat-topbar">
        <div className="flex items-center gap-2">
          <span className="status-dot" />
          <span className="text-sm text-slate-300 font-medium">RAG AI Chat</span>
        </div>
        <button
          className="clear-btn"
          onClick={onClear}
          title="Clear conversation"
        >
          🗑 Clear
        </button>
      </div>

      {/* Messages */}
      <div className="messages-area">
        {messages.map((msg) => (
          <ChatBubble key={msg.id} message={msg} />
        ))}
        {isLoading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={onSend} disabled={isLoading} />
    </div>
  );
}
