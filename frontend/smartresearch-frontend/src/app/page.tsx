"use client";

import axios from "axios";
import React, { useCallback, useMemo, useState } from "react";

type FileRow = {
  id: string;          // local temp id
  name: string;
  size: number;
  status: "waiting" | "uploading" | "done" | "error";
  progress: number;    // 0-100
  server?: UploadedFile; // set after upload
};

type UploadedFile = {
  file_id: string;
  old_name: string;
  new_name: string;
  title: string | null;
  authors: string | null;
  year: number | null;
  size_bytes: number;
};

type JobStatus = {
  job_id: string;
  state: "QUEUED" | "PROCESSING" | "DONE" | "ERROR";
  stage: string;
  overall_progress: number;
  message?: string;
};

const BACKEND = process.env.NEXT_PUBLIC_BACKEND!;

export default function Home() {
  const [rows, setRows] = useState<FileRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [job, setJob] = useState<JobStatus | null>(null);

  // add files into the queue
  const addFiles = useCallback((files: FileList | null) => {
    if (!files) return;
    const next: FileRow[] = Array.from(files).map((f) => ({
      id: crypto.randomUUID(),
      name: f.name,
      size: f.size,
      status: "waiting",
      progress: 0,
      server: undefined,
    }));
    setRows((r) => [...r, ...next]);
  }, []);

  // single-file uploader so we can show per-file progress
  const uploadOne = useCallback(async (file: File, rowId: string) => {
    setRows((r) =>
      r.map((x) => (x.id === rowId ? { ...x, status: "uploading", progress: 1 } : x))
    );

    try {
      const form = new FormData();
      form.append("files", file, file.name); // backend /files accepts list, one works too

      const res = await axios.post<UploadedFile[]>(
        `${BACKEND}/files`,
        form,
        {
          onUploadProgress: (e) => {
            if (!e.total) return;
            const pct = Math.max(1, Math.round((e.loaded * 100) / e.total));
            setRows((r) => r.map((x) => (x.id === rowId ? { ...x, progress: pct } : x)));
          },
          headers: { "ngrok-skip-browser-warning": "any" },
        }
      );

      const uploaded = res.data[0]; // one file at a time
      setRows((r) =>
        r.map((x) =>
          x.id === rowId ? { ...x, status: "done", progress: 100, server: uploaded } : x
        )
      );
    } catch (err) {
      console.error(err);
      setRows((r) =>
        r.map((x) => (x.id === rowId ? { ...x, status: "error", progress: 0 } : x))
      );
    }
  }, []);

  const handlePick = (e: React.ChangeEvent<HTMLInputElement>) => {
    addFiles(e.target.files);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    addFiles(e.dataTransfer.files);
  };

  const startUploads = async () => {
    if (busy) return;
    setBusy(true);
    // upload sequentially to keep UI stable (you can parallelize later)
    for (const row of rows) {
      if (row.status === "waiting") {
        const file = await pickFromFileSystem(row.name); // find from input? we don't track the File object here
      }
    }
    setBusy(false);
  };

  // Because we don’t hold the original File objects per row,
  // we’ll upload immediately when they’re added:
  const startNow = useCallback(async (files: FileList | null) => {
    if (!files) return;
    const added: FileRow[] = Array.from(files).map((f) => ({
      id: crypto.randomUUID(),
      name: f.name,
      size: f.size,
      status: "waiting",
      progress: 0,
    })) as FileRow[];
    setRows((r) => [...r, ...added]);
    // immediately upload each
    for (let i = 0; i < files.length; i++) {
      await uploadOne(files[i], added[i].id);
    }
  }, [uploadOne]);

  // helper to style status text
  const prettyStatus = (s: FileRow["status"]) =>
    s === "waiting" ? "Waiting" : s === "uploading" ? "Uploading…" : s === "done" ? "Completed" : "Failed";

  // files that actually uploaded:
  const uploaded = useMemo(
    () => rows.filter((r) => r.status === "done" && r.server),
    [rows]
  );

  const processDocuments = async () => {
    if (!uploaded.length) return;
    setBusy(true);
    setJob({ job_id: "pending", state: "PROCESSING", stage: "starting", overall_progress: 1 });

    try {
      const file_ids = uploaded.map((r) => r.server!.file_id);
      const payload = { file_ids, summary_model: "hf-bart-cnn", max_pages: 40, chunk_size: 3500 };
      const start = await axios.post<{ job_id: string }>(`${BACKEND}/jobs/summarize_cluster`, payload);
      const job_id = start.data.job_id;

      // poll a few times just to demo; your real page can loop until DONE
      const poll = async () => {
        const s = await axios.get<JobStatus>(`${BACKEND}/jobs/${job_id}/status`);
        setJob(s.data);
        if (s.data.state === "DONE" || s.data.state === "ERROR") return;
        setTimeout(poll, 1200);
      };
      poll();
    } catch (e) {
      console.error(e);
      setJob({ job_id: "error", state: "ERROR", stage: "failed", overall_progress: 0, message: "Failed to start job" });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="wrap">
      <header className="topbar">
        <div className="brand">SmartSearch</div>
        <nav className="nav">
          <span className="navitem active">Upload</span>
          <span className="navitem">All Papers</span>
          <span className="navitem">Cluster</span>
          <span className="navitem">Export</span>
        </nav>
      </header>

      <section className="card">
        <div
          className="drop"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          <div className="icon">+</div>
          <div className="title">Upload PDFs</div>
          <input
            type="file"
            multiple
            accept="application/pdf"
            onChange={(e) => startNow(e.target.files)}
            className="filepick"
            title=""
          />
        </div>

        <div className="list">
          {rows.length === 0 ? (
            <div className="placeholder">No files yet</div>
          ) : (
            rows.map((r) => (
              <div key={r.id} className="row">
                <div className="name">{r.server?.new_name ?? r.name}</div>
                <div className="status">
                  {r.status === "uploading" && (
                    <div className="bar">
                      <div className="fill" style={{ width: `${r.progress}%` }} />
                    </div>
                  )}
                  <span
                    className={
                      r.status === "done"
                        ? "ok"
                        : r.status === "error"
                        ? "bad"
                        : "muted"
                    }
                  >
                    {prettyStatus(r.status)}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        <button
          className="primary"
          onClick={processDocuments}
          disabled={!uploaded.length || busy}
        >
          Process Documents
        </button>

        {job && (
          <div className="job">
            <div><b>Stage:</b> {job.stage}</div>
            <div className="bar">
              <div className="fill" style={{ width: `${job.overall_progress}%` }} />
            </div>
            <div className="muted">{job.state}{job.message ? ` — ${job.message}` : ""}</div>
          </div>
        )}
      </section>

      <style jsx>{`
        .wrap { background:#2b2d31; min-height:100vh; padding:24px; }
        .topbar { max-width:820px; margin:0 auto 16px; display:flex; justify-content:space-between; align-items:center; color:#fff; }
        .brand { font-weight:700; }
        .nav { display:flex; gap:16px; font-size:14px; }
        .navitem { opacity:.8; }
        .navitem.active { opacity:1; }

        .card {
          max-width:820px; margin:0 auto; background:#fff; border-radius:12px; padding:20px;
          box-shadow: 0 6px 24px rgba(0,0,0,.15);
        }
        .drop {
          position:relative; border:2px dashed #c9b39a; border-radius:12px; padding:28px; text-align:center;
          background:#faf7f3; margin-bottom:14px;
        }
        .icon { width:44px; height:44px; line-height:44px; margin:0 auto 8px; border:1px solid #c9b39a; color:#8c6543; border-radius:10px; font-size:28px; }
        .title { font-size:20px; font-weight:600; color:#633; }
        .filepick { position:absolute; inset:0; opacity:0; cursor:pointer; }

        .list { border:1px solid #eee; border-radius:8px; background:#fff; }
        .placeholder { padding:12px; color:#888; }
        .row {
          display:flex; justify-content:space-between; align-items:center;
          padding:10px 12px; border-top:1px solid #f2f2f2;
        }
        .row:first-child { border-top:none; }
        .name { font-weight:600; color:#333; }
        .status { display:flex; align-items:center; gap:10px; }
        .bar { width:160px; height:8px; background:#eee; border-radius:999px; overflow:hidden; }
        .fill { height:100%; background:#b07a4a; transition:width .2s ease; }

        .ok { color:#2e7d32; font-weight:600; }
        .bad { color:#c62828; font-weight:600; }
        .muted { color:#777; }

        .primary {
          margin-top:14px; background:#9b6a3d; color:#fff; border:none; padding:12px 18px; border-radius:8px;
          cursor:pointer; font-weight:600;
        }
        .primary[disabled] { opacity:.5; cursor:not-allowed; }

        .job { margin-top:14px; }
      `}</style>
    </div>
  );
}

/**
 * NOTE: In this minimal demo we immediately upload as soon as files are chosen,
 * using `startNow`, so we don't keep the File objects in state long-term.
 * If you prefer a "queue then upload" approach, store File blobs keyed by row.id.
 */
