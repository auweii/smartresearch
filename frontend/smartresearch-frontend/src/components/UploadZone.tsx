"use client";
import React, { useState } from "react";
import { uploadOne } from "../lib/api";
import type { FileInfo } from "../types";

type Row = {
  id: string;
  file: File;
  progress: number;
  status: "waiting" | "uploading" | "done" | "error";
  server?: FileInfo;
};

export default function UploadZone({ onDone }: { onDone: (files: FileInfo[]) => void }) {
  const [rows, setRows] = useState<Row[]>([]);
  const [dragOver, setDragOver] = useState(false);

  async function addFiles(list: FileList | null) {
    if (!list) return;
    const toAdd: Row[] = Array.from(list).map(f => ({ id: crypto.randomUUID(), file: f, progress: 0, status: "waiting" }));
    setRows(r => [...r, ...toAdd]);

    const collected: FileInfo[] = [];
    // sequential uploads so you can animate per-row progress if you want later
    for (const r of toAdd) {
      setRows(rs => rs.map(x => x.id === r.id ? { ...x, status: "uploading", progress: 10 } : x));
      try {
        const info = await uploadOne(r.file);
        collected.push(info);
        setRows(rs => rs.map(x => x.id === r.id ? { ...x, status: "done", progress: 100, server: info } : x));
      } catch {
        setRows(rs => rs.map(x => x.id === r.id ? { ...x, status: "error", progress: 0 } : x));
      }
    }
    if (collected.length) onDone(collected);
  }

  return (
    <div className="card">
      <div
        className={`drop ${dragOver ? "over" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files); }}
      >
        <div className="icon">+</div>
        <div className="title">Upload PDFs</div>
        <input type="file" multiple accept="application/pdf" onChange={(e) => addFiles(e.target.files)} className="filepick" title="" />
      </div>

      <div className="list">
        {rows.length === 0 ? (
          <div className="placeholder">No files yet</div>
        ) : rows.map(r => (
          <div className="row" key={r.id} title={r.server?.new_name ?? r.file.name}>
            <div className="meta">
              <div className="name">{(r.server?.new_name ?? r.file.name)}</div>
              {r.server?.title && <div className="sub">{r.server.title}</div>}
            </div>
            <div className="right">
              {r.status === "uploading" && (
                <div className="bar"><div className="fill" style={{ width: `${r.progress}%` }} /></div>
              )}
              <span className={`badge ${r.status}`}>
                {r.status === "waiting" ? "Waiting" : r.status === "uploading" ? "Uploading…" : r.status === "done" ? "Completed" : "Failed"}
              </span>
            </div>
          </div>
        ))}
      </div>

      <style jsx>{`
        .card { background:#fff; border-radius:14px; padding:20px; box-shadow: 0 10px 30px rgba(0,0,0,.1); }
        .drop { position:relative; border:2px dashed #c9b39a; border-radius:12px; padding:28px; text-align:center; background:#faf7f3; margin-bottom:14px; }
        .drop.over { background:#f6efe6; border-color:#b07a4a; }
        .icon { width:44px; height:44px; line-height:44px; margin:0 auto 8px; border:1px solid #c9b39a; color:#8c6543; border-radius:10px; font-size:28px; }
        .title { font-size:20px; font-weight:600; color:#633; }
        .filepick { position:absolute; inset:0; opacity:0; cursor:pointer; }

        .list { border:1px solid #eee; border-radius:10px; background:#fff; overflow:hidden; }
        .placeholder { padding:14px; color:#888; }
        .row { display:flex; justify-content:space-between; align-items:center; padding:12px 14px; border-top:1px solid #f2f2f2; }
        .row:first-child { border-top:none; }
        .meta { min-width:0; }
        .name { font-weight:600; color:#333; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .sub { font-size:12px; color:#6b6b6b; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-top:2px; }

        .right { display:flex; align-items:center; gap:10px; }
        .bar { width:160px; height:8px; background:#eee; border-radius:999px; overflow:hidden; }
        .fill { height:100%; background:#b07a4a; transition:width .18s ease; }
        .badge { font-size:12px; padding:4px 8px; border-radius:999px; }
        .badge.waiting { background:#f4f4f5; color:#666; border:1px solid #e7e7e9; }
        .badge.uploading { background:#f4f4f5; color:#666; border:1px solid #e7e7e9; }
        .badge.done { background:#e6f4ea; color:#2e7d32; border:1px solid #c8e6c9; }
        .badge.error { background:#fdeceb; color:#c62828; border:1px solid #ffcdd2; }
      `}</style>
    </div>
  );
}
