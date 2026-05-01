import ConfidenceBar from "./ConfidenceBar";
import SourcesPanel from "./SourcesPanel";

/**
 * ChatBubble component
 * Renders a single chat message — either user or assistant.
 *
 * AI bubbles include:
 *  - Confidence progress bar
 *  - Source PDF tags
 *  - Collapsible "Sources used" panel with matched chunks
 *  - Typing cursor while message is being streamed
 */
export default function ChatBubble({ message }) {
  const isUser = message.role === "user";
  const isError = message.isError;

  return (
    <div className={`chat-row ${isUser ? "chat-row--user" : "chat-row--ai"}`}>
      {/* Avatar */}
      {!isUser && (
        <div className={`avatar avatar--ai ${isError ? "avatar--error" : ""}`}>
          {isError ? "⚠️" : "🧠"}
        </div>
      )}

      <div className={`bubble-wrapper ${isUser ? "items-end" : "items-start"}`}>
        {/* Message bubble */}
        <div
          className={`bubble ${isUser ? "bubble--user" : isError ? "bubble--error" : "bubble--ai"}`}
        >
          {/* Render content with line breaks preserved */}
          <div className="bubble-text">
            {message.content.split("\n").map((line, i) => {
              // Render horizontal rules from markdown ---
              if (line.trim() === "---") {
                return <hr key={i} className="my-2 border-white/10" />;
              }
              // Render bold markers **text**
              const parts = line.split(/(\*\*.*?\*\*)/g);
              return (
                <p key={i} className={i > 0 ? "mt-1" : ""}>
                  {parts.map((part, j) =>
                    part.startsWith("**") && part.endsWith("**") ? (
                      <strong key={j} className="text-violet-300">
                        {part.slice(2, -2)}
                      </strong>
                    ) : (
                      part
                    )
                  )}
                </p>
              );
            })}
            {/* Blinking cursor while typing */}
            {message.typing && <span className="typing-cursor" />}
          </div>
        </div>

        {/* AI-only extras — only show when typing is done */}
        {!isUser && !message.typing && !isError && (
          <div className="bubble-extras">
            {/* Source PDF tags */}
            {message.sources?.length > 0 && (
              <div className="source-tags">
                {message.sources.map((src, i) => (
                  <span key={i} className="source-tag">
                    📄 {src}
                  </span>
                ))}
              </div>
            )}

            {/* Confidence bar */}
            {message.confidence !== null && message.confidence !== undefined && (
              <ConfidenceBar confidence={message.confidence} />
            )}

            {/* Collapsible sources panel */}
            <SourcesPanel
              sources={message.sources}
              matchedChunks={message.matched_chunks}
              retrievalMethod={message.retrieval_method}
            />
          </div>
        )}

        {/* Timestamp */}
        <span className="bubble-time">
          {message.timestamp?.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>

      {/* User avatar */}
      {isUser && <div className="avatar avatar--user">👤</div>}
    </div>
  );
}
