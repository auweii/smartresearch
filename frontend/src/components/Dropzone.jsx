import { useState, useCallback } from "react";
import axios from "axios";
import { createPortal } from "react-dom";
import { Worker, Viewer } from "@react-pdf-viewer/core";
import "@react-pdf-viewer/core/lib/styles/index.css";

export default function Dropzone({ onFiles = () => {} }) {
  const [uploads, setUploads] = useState([]);
  const [preview, setPreview] = useState(null);

  const uploadFile = async (upload) => {
    const formData = new FormData();
    formData.append("file", upload.file);
    try {
      await axios.post("http://127.0.0.1:8000/api/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploads((prev) =>
            prev.map((u) =>
              u.id === upload.id
                ? {
                    ...u,
                    progress: percent,
                    status: percent < 100 ? "uploading" : "processing",
                  }
                : u
            )
          );
        },
      });
      setUploads((prev) =>
        prev.map((u) =>
          u.id === upload.id
            ? { ...u, progress: 100, status: "completed" }
            : u
        )
      );
    } catch (err) {
      console.error("Upload failed:", err);
      setUploads((prev) =>
        prev.map((u) =>
          u.id === upload.id ? { ...u, status: "failed" } : u
        )
      );
    }
  };

  const handleFiles = useCallback(
    (files) => {
      if (!files || files.length === 0) return;
      const newUploads = Array.from(files).map((file) => ({
        id: crypto.randomUUID(),
        name: file.name,
        file,
        progress: 0,
        status: "uploading",
        url: URL.createObjectURL(file),
      }));
      setUploads((prev) => [...prev, ...newUploads]);
      onFiles(files);
      newUploads.forEach(uploadFile);
    },
    [onFiles]
  );

  const handleDrop = (e) => {
    e.preventDefault();
    handleFiles(e.dataTransfer?.files);
  };

  const handleSelect = (e) => handleFiles(e.target?.files);

  const removeFile = (id) => {
    // revoke the blob URL here — only when truly removing a file
    setUploads((prev) => {
      const file = prev.find((u) => u.id === id);
      if (file?.url) URL.revokeObjectURL(file.url);
      return prev.filter((u) => u.id !== id);
    });
  };

  const openPreview = (file) => {
    if (file.status === "completed") {
      setPreview({ name: file.name, url: file.url });
    }
  };

  // 🔒 don’t revoke the blob here
  const closePreview = () => setPreview(null);

  return (
    <div className="flex flex-col items-center gap-4 relative">
      {/* Drop area */}
      <div
        className="border-2 border-dashed border-bronze-400/70 rounded-2xl p-12 text-center cursor-pointer hover:bg-bronze-50 transition-colors duration-150 w-full"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => document.getElementById("pdfInput").click()}
      >
        <input
          id="pdfInput"
          type="file"
          accept="application/pdf"
          multiple
          className="hidden"
          onChange={handleSelect}
        />
        <div className="flex flex-col items-center gap-3 text-bronze-700">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            className="w-12 h-12"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 16.5V3m0 0l3.75 3.75M12 3L8.25 6.75M3 21h18"
            />
          </svg>
          <p className="font-semibold text-lg">Select or Drop Files</p>
          <p className="text-sm text-neutral-500">
            PDF only. Click or drag to upload.
          </p>
        </div>
      </div>

      {/* Uploaded list */}
      {uploads.length > 0 && (
        <div className="w-full">
          {uploads.map((u) => (
            <div
              key={u.id}
              className="flex items-center justify-between gap-3 py-3 border-b last:border-none"
            >
              <div className="flex flex-col flex-1">
                <div className="flex items-center justify-between">
                  <button
                    onClick={() => openPreview(u)}
                    className="font-medium text-sm text-neutral-800 truncate text-left hover:underline hover:text-bronze-700"
                    title="Open PDF preview"
                  >
                    📄 {u.name}
                  </button>

                  {u.status === "completed" ? (
                    <span className="text-green-600 text-xs font-semibold">
                      Completed
                    </span>
                  ) : u.status === "failed" ? (
                    <span className="text-red-600 text-xs font-semibold">
                      Failed
                    </span>
                  ) : u.status === "processing" ? (
                    <span className="text-amber-600 text-xs font-semibold">
                      Processing…
                    </span>
                  ) : (
                    <span className="text-bronze-600 text-xs font-semibold">
                      {u.progress}%
                    </span>
                  )}
                </div>

                <div className="w-full bg-neutral-200 rounded-full h-2 mt-1 overflow-hidden">
                  <div
                    className={`h-2 transition-all duration-200 ${
                      u.status === "completed"
                        ? "bg-green-500"
                        : u.status === "failed"
                        ? "bg-red-500"
                        : u.status === "processing"
                        ? "bg-amber-500"
                        : "bg-bronze-500"
                    }`}
                    style={{ width: `${u.progress}%` }}
                  ></div>
                </div>
              </div>

              <button
                onClick={() => removeFile(u.id)}
                className="ml-2 text-neutral-500 hover:text-red-600 font-bold text-lg"
                title="Remove file"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* PDF Modal */}
      {preview &&
        createPortal(
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-[9999]">
            <div className="bg-white w-11/12 max-w-5xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden">
              <div className="flex justify-between items-center p-3 border-b bg-bronze-600 text-white shrink-0">
                <h2 className="font-semibold truncate">{preview.name}</h2>
                <button
                  onClick={closePreview}
                  className="text-white hover:text-red-300 text-xl font-bold"
                >
                  ×
                </button>
              </div>

              <div className="flex-1 overflow-y-auto bg-neutral-50 p-2">
                <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js">
                  <Viewer fileUrl={preview.url} />
                </Worker>
              </div>
            </div>
          </div>,
          document.body
        )}
    </div>
  );
}
