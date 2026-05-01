import { useState, useCallback, useRef } from "react";
import { uploadPDFs } from "../services/api";

/**
 * UploadZone component
 * Drag-and-drop + click-to-browse PDF uploader with progress feedback.
 */
export default function UploadZone({ onUploaded }) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // { type: 'success'|'error', msg }
  const fileInputRef = useRef(null);

  const handleFiles = useCallback(
    async (files) => {
      const pdfs = Array.from(files).filter((f) => f.name.toLowerCase().endsWith(".pdf"));
      if (!pdfs.length) {
        setUploadStatus({ type: "error", msg: "Please upload PDF files only." });
        return;
      }
      setUploading(true);
      setUploadStatus(null);
      try {
        const result = await uploadPDFs(pdfs);
        const names = result.uploaded.map((d) => d.filename).join(", ");
        setUploadStatus({
          type: "success",
          msg: `✓ Indexed: ${names}`,
        });
        onUploaded?.();
      } catch (err) {
        setUploadStatus({ type: "error", msg: err.message });
      } finally {
        setUploading(false);
      }
    },
    [onUploaded]
  );

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const onDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  return (
    <div className="mb-4">
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={() => setIsDragging(false)}
        onClick={() => !uploading && fileInputRef.current?.click()}
        className={`upload-zone ${isDragging ? "upload-zone--active" : ""} ${uploading ? "uploading" : ""}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />

        {uploading ? (
          <div className="flex flex-col items-center gap-2">
            <div className="upload-spinner" />
            <span className="text-sm text-violet-300">Processing PDFs…</span>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 pointer-events-none">
            <div className="upload-icon">📂</div>
            <p className="text-sm font-medium text-slate-300">
              Drop PDFs here
            </p>
            <p className="text-xs text-slate-500">or click to browse</p>
          </div>
        )}
      </div>

      {uploadStatus && (
        <p
          className={`mt-2 text-xs px-2 py-1 rounded ${
            uploadStatus.type === "success"
              ? "text-cyan-400 bg-cyan-400/10"
              : "text-red-400 bg-red-400/10"
          }`}
        >
          {uploadStatus.msg}
        </p>
      )}
    </div>
  );
}
