import { useState } from "react";
import ConfidenceBar from "./ConfidenceBar";

/**
 * SourcesPanel component
 * Collapsible panel showing the retrieved chunks that produced the AI answer.
 * Each chunk shows the source PDF, page number, and confidence.
 */
export default function SourcesPanel({ sources, matchedChunks, retrievalMethod }) {
  const [open, setOpen] = useState(false);

  if (!sources?.length && !matchedChunks?.length) return null;

  return (
    <div className="sources-panel">
      <button
        className="sources-toggle"
        onClick={() => setOpen((o) => !o)}
      >
        <span className="flex items-center gap-1.5">
          <span>🧠</span>
          <span>Sources used</span>
          {sources.length > 0 && (
            <span className="sources-badge">{sources.length}</span>
          )}
        </span>
        <span className={`sources-chevron ${open ? "open" : ""}`}>▾</span>
      </button>

      {open && (
        <div className="sources-body">
          {/* Retrieval method tag */}
          {retrievalMethod && (
            <p className="text-xs text-slate-500 mb-3">
              Method: <span className="text-violet-400">{retrievalMethod}</span>
            </p>
          )}

          {matchedChunks.map((chunk, idx) => (
            <div key={idx} className="chunk-card">
              {/* Chunk header */}
              <div className="chunk-header">
                <div className="flex items-center gap-1.5">
                  <span className="chunk-icon">📄</span>
                  <span className="chunk-source">{chunk.source}</span>
                  {chunk.page && (
                    <span className="chunk-page">p. {chunk.page}</span>
                  )}
                </div>
                <span className="chunk-idx">#{idx + 1}</span>
              </div>

              {/* Confidence bar */}
              <ConfidenceBar confidence={chunk.confidence} />

              {/* Chunk text */}
              <p className="chunk-text">{chunk.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
