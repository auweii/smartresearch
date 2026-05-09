import axios from "axios";

// Use env if available, otherwise fallback to local backend
const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Create axios instance
export const api = axios.create({
  baseURL: `${API_BASE}/api`,
});

// --------------------------------------------------
// API FUNCTIONS (clean + reusable)
// --------------------------------------------------

// Upload PDF
export const uploadPaper = (file, config = {}) => {
  const formData = new FormData();
  formData.append("file", file);

  return api.post("/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    ...config,
  });
};

// Get all papers
export const getPapers = () => {
  return api.get("/docs");
};

// Delete paper
export const deletePaper = (id) => {
  return api.delete(`/docs/${id}`);
};

// Get full text
export const getPaperText = (id) => {
  return api.get(`/text/${id}`);
};

// Get metadata
export const getPaperMeta = (id) => {
  return api.get(`/meta/${id}`);
};

// Cluster
export const getClusters = () => {
  return api.get("/clustered");
};

// Search (basic)
export const searchPapers = (query, topk = 10) => {
  return api.post("/search", {
    q: query,
    topk,
  });
};

// Semantic search
export const semanticSearch = (query, topk = 10) => {
  return api.post("/semantic_search", {
    q: query,
    topk,
  });
};

// Hybrid search (BEST)
export const hybridSearch = (query, topk = 10) => {
  return api.post("/hybrid_search", {
    q: query,
    topk,
  });
};

// Export PDF
export const exportPDF = (payload = {}) => {
  return api.post("/export", payload, {
    responseType: "blob",
  });
};

export const keywordSearch = (query, topk = 10) => {
  return api.post("/search", {
    q: query,
    topk,
  });
};
