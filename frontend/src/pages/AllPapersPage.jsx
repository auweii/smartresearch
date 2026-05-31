import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import Card from "../components/Card";
import Modal from "../components/Modal";
import {
  getPapers,
  getPaperMeta,
  deletePaper,
  keywordSearch,
  semanticSearch,
  hybridSearch,
} from "../api";

const API_BASE = "http://127.0.0.1:8000";

const scoreClass = (s) => {
  if (typeof s !== "number") return "text-neutral-500";
  if (s >= 0.8) return "text-green-600 font-semibold";
  if (s >= 0.6) return "text-amber-600 font-medium";
  return "text-neutral-500";
};

const modeText = {
  semantic: "Finds meaning-level matches using SPECTER2 embeddings.",
  hybrid: "Combines TF-IDF and semantic scores for balanced relevance.",
  keyword: "Performs simple keyword-based text matching only.",
};

function getFinalMeta(metaRes) {
  return metaRes?.data?.meta?.final || {};
}

export default function AllPapersPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [metaLoading, setMetaLoading] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("hybrid");
  const [view, setView] = useState("all");
  const [lastQuery, setLastQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [detail, setDetail] = useState(null);
  const [deletingAll, setDeletingAll] = useState(false);

  const navigate = useNavigate();
  const isSearch = view === "search";

  const enrichPaper = async (paper) => {
    try {
      const metaRes = await getPaperMeta(paper.id);
      const finalMeta = getFinalMeta(metaRes);
      return {
        id: paper.id,
        name: paper.name,
        fileName: paper.name,
        n_chars: paper.n_chars,
        title: finalMeta.title || paper.name || "Untitled",
        summary: paper.summary || finalMeta.summary || finalMeta.abstract || "No summary available.",
        authors: Array.isArray(finalMeta.authors) ? finalMeta.authors : [],
        year: finalMeta.year || "-",
        relevance: "-",
        score: undefined,
        meta: finalMeta,
      };
    } catch {
      return {
        id: paper.id,
        name: paper.name,
        fileName: paper.name,
        n_chars: paper.n_chars,
        title: paper.name || "Untitled",
        summary: paper.summary || "No summary available.",
        authors: [],
        year: "-",
        relevance: "-",
        score: undefined,
        meta: null,
      };
    }
  };

  const loadAll = async () => {
    try {
      setLoading(true);
      setMetaLoading(true);
      setError("");
      const res = await getPapers();
      const papers = res.data || [];
      const enriched = await Promise.all(papers.map(enrichPaper));
      setRows(enriched);
      setView("all");
    } catch (e) {
      console.error(e);
      setError("Failed to load documents.");
    } finally {
      setLoading(false);
      setMetaLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  function getTitle(p) {
    const title = p.title || p.meta?.title || p.fileName || p.name;
    return typeof title === "string" && title.trim() ? title.trim() : "Untitled";
  }

  function getSummary(p) {
    const summary = p.summary || p.meta?.summary || p.meta?.abstract;
    return typeof summary === "string" && summary.trim() ? summary.trim() : "No summary available.";
  }

  const deleteAll = async () => {
    const ok = confirm(`Delete all ${rows.length} papers and their data? This cannot be undone.`);
    if (!ok) return;
    setDeletingAll(true);
    try {
      await Promise.all(rows.map((r) => deletePaper(r.id)));
      await loadAll();
    } catch (e) {
      console.error(e);
      alert("Some papers could not be deleted.");
    } finally {
      setDeletingAll(false);
    }
  };

  const runSearch = async () => {
    if (!query.trim()) return;
    try {
      setSearching(true);
      setError("");
      setLastQuery(query);

      let res;
      if (mode === "semantic") res = await semanticSearch(query, 50);
      else if (mode === "keyword") res = await keywordSearch(query, 50);
      else res = await hybridSearch(query, 50);

      const hits = res.data?.hits || [];
      const enriched = await Promise.all(
        hits.map(async (h) => {
          const base = {
            id: h.id,
            name: h.name,
            fileName: h.name,
            n_chars: undefined,
            title: h.name || "Untitled",
            summary: h.preview || "No summary available.",
            authors: [],
            year: "-",
            relevance: typeof h.score === "number" ? Number(h.score).toFixed(3) : "-",
            score: typeof h.score === "number" ? h.score : 0,
            meta: h.meta || null,
          };
          try {
            const metaRes = await getPaperMeta(h.id);
            const finalMeta = getFinalMeta(metaRes);
            return {
              ...base,
              title: finalMeta.title || h.name || "Untitled",
              summary: finalMeta.summary || finalMeta.abstract || h.preview || "No summary available.",
              authors: Array.isArray(finalMeta.authors) ? finalMeta.authors : [],
              year: finalMeta.year || "-",
              meta: finalMeta,
            };
          } catch {
            return base;
          }
        })
      );
      setRows(enriched);
      setView("search");
    } catch (e) {
      console.error(e);
      setError("Search failed. Check backend.");
    } finally {
      setSearching(false);
    }
  };

  // re-run search when mode changes while in search view
  useEffect(() => {
    if (isSearch && lastQuery) runSearch();
  }, [mode]);

  const openDetails = async (row) => {
    try {
      const metaRes = await getPaperMeta(row.id);
      const finalMeta = getFinalMeta(metaRes);
      setDetail({ ...row, meta: finalMeta });
    } catch {
      setDetail({ ...row, meta: null });
    }
  };

  const deleteDoc = async (id) => {
    const ok = confirm("Delete this paper and its data?");
    if (!ok) return;
    try {
      await deletePaper(id);
      setDetail(null);
      await loadAll();
    } catch (e) {
      console.error(e);
      alert("Delete failed.");
    }
  };

  const columns = useMemo(
    () => ["ID", "Title", "File Name", "Summary", "Author", "Year", "Relevance", "Delete"],
    []
  );

  return (
    <div className="relative flex flex-col items-center min-h-[calc(100vh-56px)] bg-gradient-to-b from-bronze-100/60 to-bronze-50 text-bronze-800 p-8">
      <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.04]" />

      <div className="w-full max-w-7xl z-10">
        <div className="mb-6 flex items-center justify-between">
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-bronze-700 hover:underline"
          >
            ← Back
          </button>

          <div className="flex items-center gap-3">
            <button
              onClick={loadAll}
              className="text-sm bg-white border border-bronze-300 text-bronze-700 px-4 py-2 rounded-lg hover:bg-bronze-50"
            >
              Refresh
            </button>
            {rows.length > 0 && (
              <button
                onClick={deleteAll}
                disabled={deletingAll}
                className="text-sm bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
              >
                {deletingAll ? "Deleting…" : "Delete All"}
              </button>
            )}
          </div>
        </div>

        <h1 className="text-4xl font-extrabold tracking-tight text-center mb-2">All Papers</h1>
        <p className="text-center text-neutral-600 mb-8">
          Browse uploaded papers, metadata, summaries, and document IDs.
        </p>

        <form
          onSubmit={(e) => { e.preventDefault(); runSearch(); }}
          className="flex items-center justify-center gap-3 mb-1"
        >
          <input
            type="text"
            placeholder="Search by title, topic, or keyword"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-[36rem] px-4 py-2 rounded-lg border border-neutral-300 focus:ring-2 focus:ring-bronze-400 outline-none"
          />
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="border border-neutral-300 rounded-lg px-4 py-[0.55rem] text-sm text-neutral-700 bg-white w-[9rem]"
          >
            <option value="hybrid">Hybrid</option>
            <option value="semantic">Semantic</option>
            <option value="keyword">Keyword</option>
          </select>
          <button
            type="submit"
            disabled={searching}
            className="bg-bronze-600 hover:bg-bronze-700 text-white px-5 py-2 rounded-lg font-semibold transition-all disabled:opacity-50"
          >
            {searching ? "Searching…" : "Search"}
          </button>
        </form>

        <p className="text-sm text-neutral-500 mb-4 text-center">{modeText[mode]}</p>

        {isSearch && lastQuery && (
          <div className="flex items-center justify-between mb-4 text-sm text-neutral-600">
            <p>
              Showing {rows.length} result{rows.length !== 1 ? "s" : ""} for "{lastQuery}"
              <span className="text-neutral-500 ml-2">Mode: {mode.toUpperCase()}</span>
            </p>
            <button
              onClick={async () => {
                setQuery("");
                setLastQuery("");
                setView("all");
                await loadAll();
              }}
              className="text-bronze-600 font-semibold hover:underline"
            >
              Show all papers
            </button>
          </div>
        )}

        <Card className="p-0 w-full shadow-[0_8px_30px_rgba(139,94,60,0.12)] bg-gradient-to-b from-white/90 to-bronze-50/40 backdrop-blur-md ring-1 ring-bronze-200 rounded-3xl overflow-hidden">
          {loading ? (
            <p className="text-center text-neutral-500 py-8">Loading papers…</p>
          ) : error ? (
            <p className="text-center text-red-600 py-8">{error}</p>
          ) : rows.length === 0 ? (
            <p className="text-center text-neutral-500 py-10">No records found.</p>
          ) : (
            <div className="overflow-auto max-h-[70vh]">
              <table className="min-w-full text-sm">
                <thead className="bg-bronze-100/50 sticky top-0 z-10">
                  <tr className="text-bronze-800 uppercase text-xs tracking-wide">
                    {columns.map((header) => (
                      <th key={header} className="px-4 py-3 text-left">{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr
                      key={r.id}
                      className="border-t border-neutral-200 hover:bg-bronze-50/60 transition-colors"
                    >
                      <td className="px-4 py-3 text-neutral-600 font-mono text-xs min-w-[120px]">{r.id}</td>
                      <td className="px-4 py-3 font-semibold text-neutral-800 min-w-[220px]">
                        <button
                          onClick={() => openDetails(r)}
                          className="text-left hover:underline hover:text-bronze-700"
                        >
                          {getTitle(r)}
                        </button>
                      </td>
                      <td className="px-4 py-3 text-neutral-700 min-w-[180px]">{r.fileName || r.name || "-"}</td>
                      <td className="px-4 py-3 text-neutral-600 min-w-[320px]">{getSummary(r)}</td>
                      <td className="px-4 py-3 text-neutral-700 min-w-[180px]">
                        {r.authors?.length ? r.authors.join(", ") : "-"}
                      </td>
                      <td className="px-4 py-3 text-neutral-700">{r.year || "-"}</td>
                      <td className={`px-4 py-3 ${typeof r.score === "number" ? scoreClass(r.score) : "text-neutral-500"}`}>
                        {r.relevance || "-"}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => deleteDoc(r.id)}
                          className="px-3 py-1 text-xs rounded bg-red-600 text-white hover:bg-red-700"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {metaLoading && (
                <p className="text-xs text-neutral-500 px-4 py-3">Loading metadata…</p>
              )}
            </div>
          )}
        </Card>
      </div>

      <button
        onClick={() => navigate("/cluster")}
        className="fixed bottom-8 right-8 bg-bronze-600 hover:bg-bronze-700 text-white font-semibold px-5 py-3 rounded-full shadow-lg transition-all"
      >
        Go to Cluster View →
      </button>

      <Modal open={!!detail} onClose={() => setDetail(null)} size="large">
        {detail && (
          <div className="p-8 h-full overflow-y-auto">
            <div className="flex items-start justify-between mb-6">
              <h2 className="text-xl font-bold text-bronze-800 pr-6 leading-snug">
                {detail.meta?.title || detail.title || detail.name}
              </h2>
              <button
                onClick={() => setDetail(null)}
                className="text-2xl text-neutral-400 hover:text-neutral-700 shrink-0"
              >
                ×
              </button>
            </div>

            <div className="space-y-2 text-sm text-neutral-700 mb-6">
              <div className="flex gap-3">
                <span className="text-bronze-500 font-medium min-w-[72px]">ID</span>
                <span className="font-mono text-xs text-neutral-500">{detail.id}</span>
              </div>
              <div className="flex gap-3">
                <span className="text-bronze-500 font-medium min-w-[72px]">File</span>
                <span>{detail.fileName || detail.name}</span>
              </div>
              {detail.authors?.length > 0 && (
                <div className="flex gap-3">
                  <span className="text-bronze-500 font-medium min-w-[72px]">Authors</span>
                  <span>{detail.authors.join(", ")}</span>
                </div>
              )}
              {detail.year && detail.year !== "-" && (
                <div className="flex gap-3">
                  <span className="text-bronze-500 font-medium min-w-[72px]">Year</span>
                  <span>{detail.year}</span>
                </div>
              )}
              {detail.relevance && detail.relevance !== "-" && (
                <div className="flex gap-3">
                  <span className="text-bronze-500 font-medium min-w-[72px]">Relevance</span>
                  <span>{detail.relevance}</span>
                </div>
              )}
              {detail.meta?.venue && (
                <div className="flex gap-3">
                  <span className="text-bronze-500 font-medium min-w-[72px]">Venue</span>
                  <span>{detail.meta.venue}</span>
                </div>
              )}
              {detail.meta?.doi && (
                <div className="flex gap-3">
                  <span className="text-bronze-500 font-medium min-w-[72px]">DOI</span>
                    <a
                      href={"https://doi.org/" + detail.meta.doi}
                      target="_blank"
                      rel="noreferrer"
                      className="text-bronze-700 hover:underline break-all"
                    >
                    {detail.meta.doi}
                    </a>
                  </div>
               )}
            </div>

            <div className="border-t border-neutral-100 pt-5">
              <h3 className="font-semibold text-bronze-800 mb-2 text-sm uppercase tracking-wide">
                Summary
              </h3>
              <p className="text-sm text-neutral-700 leading-relaxed whitespace-pre-wrap">
                {detail.summary || "No summary available."}
              </p>
            </div>

            <div className="flex items-center justify-between mt-6 pt-4 border-t border-neutral-100">
              <button
                onClick={() => navigate("/papers/" + detail.id)}
                className="text-sm bg-bronze-700 hover:bg-bronze-800 text-white px-4 py-2 rounded-lg font-semibold transition-all"
              >
                Generate Summary →
              </button>
              <div className="flex gap-3">
                <button
                  onClick={async () => {
                    try {
                      await axios.patch(`${API_BASE}/api/meta/${detail.id}/recover_summary`);
                      await loadAll();
                      setDetail(null);
                    } catch {
                      alert("No summary to recover.");
                    }
                  }}
                  className="text-sm text-bronze-600 hover:underline"
                >
                  Recover Summary
                </button>
                <button
                  onClick={() => deleteDoc(detail.id)}
                  className="text-sm text-red-600 hover:underline"
                >
                  Delete paper
                </button>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}