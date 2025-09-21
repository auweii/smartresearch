"use client";
import { useMemo, useState } from "react";
import UploadZone from "@/components/UploadZone";
import ProcessPanel from "@/components/ProcessPanel";
import SearchFilter from "@/components/SearchFilter";
import type { FileInfo } from "@/types";
import { formatBytes, truncate } from "@/utils/format";

export default function Page() {
  const [uploaded, setUploaded] = useState<FileInfo[]>([]);
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!query) return uploaded;
    const q = query.toLowerCase();
    return uploaded.filter(f =>
      (f.title ?? "").toLowerCase().includes(q) ||
      (f.authors ?? "").toLowerCase().includes(q) ||
      (f.new_name ?? "").toLowerCase().includes(q)
    );
  }, [uploaded, query]);

  return (
    <>
      <h1 style={{ color: "#fff", marginBottom: 12 }}>Upload & Process</h1>

      <div className="card">
        <UploadZone onDone={(files) => setUploaded(prev => [...prev, ...files])} />
        <div className="mt-12">
          <SearchFilter value={query} onChange={setQuery} />
        </div>

        {filtered.length > 0 && (
          <div className="table-card mt-12">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Title</th>
                    <th>Authors</th>
                    <th>Year</th>
                    <th style={{ textAlign: "right" }}>Size</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(f => (
                    <tr key={f.file_id}>
                      <td>{truncate(f.new_name, 64)}</td>
                      <td>{truncate(f.title ?? "—", 80)}</td>
                      <td className="small">{f.authors ?? "—"}</td>
                      <td className="small">{f.year ?? "—"}</td>
                      <td className="small" style={{ textAlign: "right" }}>{formatBytes(f.size_bytes)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      <div className="card mt-16">
        <ProcessPanel files={uploaded} />
      </div>
    </>
  );
}
