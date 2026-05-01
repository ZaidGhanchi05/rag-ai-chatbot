import { useState, useEffect, useCallback } from "react";
import { getDocuments, deleteDocument } from "../services/api";

/**
 * useDocuments hook
 * Manages the list of uploaded documents from the backend.
 */
export function useDocuments() {
  const [documents, setDocuments] = useState([]);
  const [totalVectors, setTotalVectors] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getDocuments();
      setDocuments(data.documents || []);
      setTotalVectors(data.total_vectors || 0);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const removeDocument = useCallback(
    async (docId) => {
      try {
        await deleteDocument(docId);
        await fetchDocuments();
      } catch (err) {
        setError(err.message);
      }
    },
    [fetchDocuments]
  );

  return { documents, totalVectors, loading, error, fetchDocuments, removeDocument };
}
