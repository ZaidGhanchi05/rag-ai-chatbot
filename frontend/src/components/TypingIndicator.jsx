/**
 * TypingIndicator component
 * Animated three-dot indicator shown while the AI is "thinking".
 */
export default function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="avatar avatar--ai">🧠</div>
      <div className="bubble bubble--ai">
        <div className="typing-dots">
          <span />
          <span />
          <span />
        </div>
      </div>
    </div>
  );
}
