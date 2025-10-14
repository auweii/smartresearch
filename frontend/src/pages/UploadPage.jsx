import { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import Card from "../components/Card";
import Dropzone from "../components/Dropzone";

export default function UploadPage() {
  const [files, setFiles] = useState([]);
  const navigate = useNavigate();

  // Fetch existing stored docs on load so they persist between refreshes
  useEffect(() => {
    async function fetchDocs() {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/docs");
        if (!res.ok) return;
        const data = await res.json();
        setFiles(data);
      } catch (err) {
        console.error("Failed to fetch stored docs:", err);
      }
    }
    fetchDocs();
  }, []);

  // Trigger backend move endpoint
  const handleMoveToStorage = async () => {
    try {
      await axios.post("http://127.0.0.1:8000/api/move_to_storage");
      navigate("/papers");
    } catch (err) {
      console.error("Failed to move files:", err);
    }
  };

  return (
    <div className="relative flex flex-col items-center justify-center min-h-[calc(100vh-56px)] bg-gradient-to-b from-bronze-100/60 to-bronze-50 text-bronze-800 p-8">
      {/* Subtle background grid */}
      <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.04] pointer-events-none" />

      {/* Floating upload icon */}
      <div className="animate-pulse-slow mb-3 z-10">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth="1.8"
          stroke="#8B5E3C"
          className="w-10 h-10 drop-shadow-sm"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
          />
        </svg>
      </div>

      {/* Heading */}
      <div className="text-center space-y-2 z-10 mb-6">
        <h1 className="text-5xl font-extrabold tracking-tight drop-shadow-sm">
          Upload Research Papers
        </h1>
        <p className="text-neutral-600 text-sm">
          Drag & drop PDFs or click below to start processing your documents.
        </p>
      </div>

      {/* Upload Card */}
      <Card className="p-12 w-full max-w-5xl text-center shadow-[0_8px_30px_rgba(139,94,60,0.12)] bg-gradient-to-b from-white/90 to-bronze-50/40 backdrop-blur-md ring-1 ring-bronze-200 rounded-3xl overflow-hidden z-10">
        <Dropzone onFiles={setFiles} />
      </Card>

      {/* Footer */}
      <div className="text-sm text-neutral-500 mt-6 flex flex-col items-center gap-3">
        <button
          onClick={handleMoveToStorage}
          disabled={files.length === 0}
          className={`px-6 py-2 font-semibold rounded-full transition-all duration-200 shadow-sm ${
            files.length > 0
              ? "bg-bronze-600 text-white hover:bg-bronze-700"
              : "bg-neutral-200 text-neutral-500 cursor-not-allowed"
          }`}
        >
          Go to All Papers
        </button>

        <p>
          {files.length > 0
            ? `${files.length} file${files.length > 1 ? "s" : ""} ready.`
            : "No files uploaded yet."}
        </p>
      </div>
    </div>
  );
}

