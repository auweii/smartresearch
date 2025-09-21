"use client";
import React, { useEffect, useRef, useState } from "react";
import { startJob, getJobStatus, getJobResult } from "../lib/api";
import type { FileInfo, JobStatus, JobResult } from "../types";

const SUMMARY_PREVIEW_CHARS = 280; // 👈 adjust preview length here

export default function ProcessPanel({ files }: { files: FileInfo[] }) {
  const [jobId, setJobId] = useState<string>();
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [result, setResult] = useState<JobResult | null>(null);
  const poller = useRef<any>(null);

  async function onStart() {
    setResult(null);
    const id = await startJob({
      file_ids: files.map((f) => f.file_id),
      section_mode: "abstract", // always summarize abstract
      section_label: "introduction", // ignored unless section_mode === "section"
      summary_chars: 900,
      num_topics: 8,
      max_pages: 40,
    });
    setJobId(id);
  }

  useEffect(() => {
    if (!jobId) return;
    const tick = async () => {
      const s = await getJobStatus(jobId);
      setStatus(s);
      if (s.state === "DONE") {
        const r = await getJobResult(jobId);
        if ("error" in r) return;
        setResult(r);
        clearInterval(poller.current);
      } else if (s.state === "ERROR") {
        clearInterval(poller.current);
      }
    };
    poller.current = setInterval(tick, 1200);
    tick();
    return () => clearInterval(poller.current);
  }, [jobId]);

  return (
    <div className="panel">
      <button className="primary" onClick={onStart} disabled={!files.length}>
        Process Documents
      </button>

      {status && (
        <div className="status">
          <div>
            <b>Stage:</b> {status.stage} — {status.overall_progress}%
          </div>
          <progress value={status.overall_progress} max={100} />
          {status.message && <div className="muted">{status.message}</div>}
          {typeof status.eta_seconds === "number" && status.eta_seconds > 0 && (
            <div className="muted">ETA: ~{status.eta_seconds}s</div>
          )}
        </div>
      )}

      {result && (
        <div className="clusters">
          <h3>Clusters</h3>
          {result.clusters.map((c) => (
            <div className="cluster" key={c.topic_id}>
              <h4>{c.topic_label}</h4>
              <p className="muted">{c.summary}</p>
              <ul>
                {c.members.map((m) => (
                  <li key={m.file_id} className="member">
                    <div>
                      <b>{m.title ?? m.new_name}</b>{" "}
                      {m.year ? `(${m.year})` : ""} — {m.authors ?? "—"}
                      {m.key_terms?.length ? (
                        <span className="muted">
                          {" "}
                          — {m.key_terms.join(", ")}
                        </span>
                      ) : null}
                    </div>
                    {m.paper_summary && (
                      <CollapsibleSummary
                        text={m.paper_summary}
                        maxChars={SUMMARY_PREVIEW_CHARS}
                      />
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
          <small className="muted">
            Method: {String(result.metrics.method)}; k=
            {String(result.metrics.k)}
          </small>
        </div>
      )}

      <style jsx>{`
        .panel {
          margin-top: 16px;
          background: #fff;
          border-radius: 14px;
          padding: 16px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        }
        .primary {
          background: #9b6a3d;
          color: #fff;
          border: none;
          padding: 12px 18px;
          border-radius: 10px;
          font-weight: 600;
          margin-top: 10px;
        }
        .status {
          margin-top: 10px;
        }
        .muted {
          color: #666;
          font-size: 12px;
        }
        .clusters {
          margin-top: 14px;
        }
        .cluster {
          border-top: 1px solid #eee;
          padding-top: 10px;
          margin-top: 10px;
        }
        .member {
          margin-bottom: 12px;
        }
      `}</style>
    </div>
  );
}

/** Collapsible summary with "Show more / Show less" */
function CollapsibleSummary({
  text,
  maxChars = 280,
}: {
  text: string;
  maxChars?: number;
}) {
  const [open, setOpen] = useState(false);

  // try to avoid cutting mid-word; fall back to hard cut
  const short =
    text.length > maxChars
      ? text.slice(0, maxChars).replace(/\s+\S*$/, "") // trim to last whole word
      : text;

  const isTruncated = text.length > short.length;

  return (
    <div className="wrap">
      <p className="summary">{open || !isTruncated ? text : short + "…"} </p>
      {isTruncated && (
        <button className="link" onClick={() => setOpen((v) => !v)}>
          {open ? "Show less" : "Show more"}
        </button>
      )}

      <style jsx>{`
        .wrap {
          margin-top: 4px;
          padding-left: 8px;
          border-left: 2px solid #eee;
        }
        .summary {
          font-size: 13px;
          color: #333;
          margin: 0 0 4px;
          line-height: 1.45;
        }
        .link {
          background: transparent;
          border: none;
          padding: 0;
          color: #9b6a3d;
          font-weight: 600;
          cursor: pointer;
          font-size: 12px;
        }
        .link:hover {
          text-decoration: underline;
        }
      `}</style>
    </div>
  );
}
