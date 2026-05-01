import UploadZone from "./UploadZone";

/**
 * Sidebar component
 * Left panel with upload zone and list of indexed documents.
 */
export default function Sidebar({ documents, totalVectors, onUploaded, onDeleteDoc, sidebarOpen }) {
  return (
    <aside className={`sidebar ${sidebarOpen ? "sidebar--open" : ""}`}>
      {/* Header */}
      <div className="sidebar-header">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">RAG Assistant</h1>
            <p className="text-xs text-slate-500">Powered by FAISS + sklearn</p>
          </div>
        </div>
        {/* Vector count badge */}
        {totalVectors > 0 && (
          <div className="vector-badge">
            <span className="text-xs text-cyan-400">{totalVectors.toLocaleString()} vectors</span>
          </div>
        )}
      </div>

      {/* Upload zone */}
      <div className="sidebar-section">
        <h2 className="sidebar-section-title">📤 Upload PDFs</h2>
        <UploadZone onUploaded={onUploaded} />
      </div>

      {/* Document list */}
      <div className="sidebar-section flex-1 overflow-hidden flex flex-col">
        <h2 className="sidebar-section-title">
          📄 Documents
          {documents.length > 0 && (
            <span className="ml-2 px-1.5 py-0.5 text-xs bg-violet-500/20 text-violet-300 rounded-full">
              {documents.length}
            </span>
          )}
        </h2>

        <div className="doc-list">
          {documents.length === 0 ? (
            <div className="empty-docs">
              <p className="text-slate-500 text-sm text-center py-6">
                No documents uploaded yet
              </p>
            </div>
          ) : (
            documents.map((doc) => (
              <div key={doc.doc_id} className="doc-item">
                <div className="doc-icon">📝</div>
                <div className="doc-info">
                  <p className="doc-name" title={doc.filename}>
                    {doc.filename}
                  </p>
                  <p className="doc-meta">{doc.chunk_count} chunks indexed</p>
                </div>
                <button
                  className="doc-delete-btn"
                  onClick={() => onDeleteDoc(doc.doc_id)}
                  title="Remove document"
                >
                  ✕
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        <p className="text-xs text-slate-600 text-center">
          sentence-transformers · FAISS · sklearn
        </p>
      </div>
    </aside>
  );
}
