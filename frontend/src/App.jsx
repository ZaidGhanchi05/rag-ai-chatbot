import { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import { useChat } from "./hooks/useChat";
import { useDocuments } from "./hooks/useDocuments";
import "./index.css";

/**
 * App — root component
 * Wires together sidebar (documents) and chat window (messages).
 */
export default function App() {
  const { messages, isLoading, sendMessage, clearChat } = useChat();
  const { documents, totalVectors, fetchDocuments, removeDocument } = useDocuments();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleUploaded = () => {
    fetchDocuments();
  };

  return (
    <div className="app-shell">
      {/* Mobile sidebar toggle */}
      <button
        className="mobile-sidebar-btn"
        onClick={() => setSidebarOpen((o) => !o)}
        title="Toggle sidebar"
      >
        {sidebarOpen ? "✕" : "☰"}
      </button>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-[9] md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Left sidebar */}
      <Sidebar
        documents={documents}
        totalVectors={totalVectors}
        onUploaded={handleUploaded}
        onDeleteDoc={removeDocument}
        sidebarOpen={sidebarOpen}
      />

      {/* Main chat area */}
      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        onSend={sendMessage}
        onClear={clearChat}
      />
    </div>
  );
}
