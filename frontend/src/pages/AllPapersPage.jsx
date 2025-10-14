import { useEffect, useState, useMemo } from "react"
import axios from "axios"
import Card from "../components/Card"
import Modal from "../components/Modal"
import { useNavigate } from "react-router-dom"

// score color helper
const scoreClass = (s) => {
  if (typeof s !== "number") return "text-neutral-500"
  if (s >= 0.8) return "text-green-600 font-semibold"
  if (s >= 0.6) return "text-amber-600 font-medium"
  return "text-neutral-500"
}

// mode explainer
const modeText = {
  semantic: "Finds meaning-level matches using SPECTER2 embeddings.",
  hybrid: "Combines TF-IDF and semantic scores for balanced relevance.",
  keyword: "Performs simple keyword-based text matching only."
}

export default function AllPapersPage() {
  // data + ui state
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [query, setQuery] = useState("")
  const [mode, setMode] = useState("semantic")
  const [view, setView] = useState("all") // all | search
  const [lastQuery, setLastQuery] = useState("")
  const [searching, setSearching] = useState(false)

  // modal state
  const [detail, setDetail] = useState(null) // {id,name,score,preview,meta,...}
  const navigate = useNavigate()

  const isSearch = view === "search"

  // fetch all
  const loadAll = async () => {
    try {
      setLoading(true)
      const res = await axios.get("http://127.0.0.1:8000/api/docs")
      const data = (res.data || []).map((d) => ({
        id: d.id,
        name: d.name,
        n_chars: d.n_chars,
        summary: d.summary || "No description available.",
        score: undefined,
        preview: undefined
      }))
      setRows(data)
      setView("all")
      setError("")
    } catch (e) {
      console.error(e)
      setError("Failed to load documents.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAll()
  }, [])

  // do search
  const runSearch = async (ev) => {
    ev?.preventDefault?.()
    if (!query.trim()) return
    const endpoint =
      mode === "semantic"
        ? "http://127.0.0.1:8000/api/semantic_search"
        : mode === "hybrid"
        ? "http://127.0.0.1:8000/api/hybrid_search"
        : "http://127.0.0.1:8000/api/search"

    try {
      setSearching(true)
      setLastQuery(query)

      const res = await axios.post(endpoint, { q: query, topk: 50 })
      let hits = res.data?.hits || []

      // normalize + prune
      hits = hits
        .map((h) => ({
          id: h.id,
          name: h.name,
          score: typeof h.score === "number" ? h.score : 0,
          preview: h.preview || "",
          summary: h.meta?.summary || h.meta?.abstract || "",
          n_chars: undefined,
          meta: h.meta || null
        }))
        .filter((h) => h.id && (h.score > 0.01 || mode === "keyword"))

      // keyword fallback: naive title match if API returns nothing
      if (hits.length === 0 && mode === "keyword") {
        const allRes = await axios.get("http://127.0.0.1:8000/api/docs")
        const qLower = query.toLowerCase()
        hits = (allRes.data || [])
          .filter((d) => d.name?.toLowerCase().includes(qLower))
          .map((d) => ({
            id: d.id,
            name: d.name,
            score: 1.0,
            preview: "",
            summary: d.summary || "",
            n_chars: d.n_chars
          }))
      }

      setRows(hits)
      setView("search")
      setError("")
    } catch (e) {
      console.error(e)
      setError("Search failed — check backend.")
    } finally {
      setSearching(false)
    }
  }

  // re-run when mode changes during search
  useEffect(() => {
    if (isSearch && lastQuery) runSearch()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode])

  // open details modal
  const openDetails = async (row) => {
    try {
      const metaRes = await axios.get(`http://127.0.0.1:8000/api/meta/${row.id}`)
      setDetail({
        ...row,
        meta: metaRes.data?.meta || null,
        external: [],
        showExternal: false,
        loadingExternal: false,
        errorExternal: ""
      })
    } catch {
      setDetail({
        ...row,
        meta: null,
        external: [],
        showExternal: false,
        loadingExternal: false,
        errorExternal: "No metadata available."
      })
    }
  }

  // get external recs
  const fetchExternal = async () => {
    if (!detail) return
    try {
      setDetail((d) => ({ ...d, loadingExternal: true, errorExternal: "" }))
      const res = await axios.get(
        `http://127.0.0.1:8000/api/external_recs/${detail.id}`
      )
      const recs = res.data?.recommendations || []
      // light filter for junk titles
      const filtered = recs.filter((r) => {
        const t = (r.title || "").toLowerCase().trim()
        if (!t || t.length < 8) return false
        if (["worth reading", "copyright"].some((x) => t.includes(x))) return false
        return true
      })
      setDetail((d) => ({
        ...d,
        loadingExternal: false,
        external: filtered,
        showExternal: true
      }))
    } catch (e) {
      console.error(e)
      setDetail((d) => ({
        ...d,
        loadingExternal: false,
        showExternal: true,
        external: [],
        errorExternal: "Failed to fetch external recommendations."
      }))
    }
  }

  // delete doc
  const deleteDoc = async (id) => {
    const ok = confirm("Delete this paper and its data?")
    if (!ok) return
    try {
      await axios.delete(`http://127.0.0.1:8000/api/docs/${id}`)
      setDetail(null)
      await loadAll()
    } catch (e) {
      alert("Delete failed.")
    }
  }

  // columns
  const columns = useMemo(
    () => [
      { header: "Name", accessor: "name" },
      { header: isSearch ? "Relevance" : "Characters", accessor: "n_chars" },
      { header: "Description", accessor: "summary" },
      { header: "ID", accessor: "id" },
      { header: "Action", accessor: "__action" }
    ],
    [isSearch]
  )

  return (
    <div className="relative flex flex-col items-center min-h-[calc(100vh-56px)] bg-gradient-to-b from-bronze-100/60 to-bronze-50 text-bronze-800 p-8">
      <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.04]" />

      <div className="w-full max-w-7xl z-10">
        {/* header + back */}
        <div className="mb-6 flex items-center justify-between">
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-bronze-700 hover:underline"
          >
            ← Back
          </button>
        </div>

        <h1 className="text-4xl font-extrabold tracking-tight text-center mb-2">
          All Papers
        </h1>
        <p className="text-center text-neutral-600 mb-8">
          Browse and manage your uploaded papers. Search, sort, and open summaries.
        </p>

        {/* controls */}
        <form
          onSubmit={runSearch}
          className="flex items-center justify-center gap-3 mb-1"
        >
          <input
            type="text"
            placeholder="Search by title or keyword"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-[36rem] px-4 py-2 rounded-lg border border-neutral-300 focus:ring-2 focus:ring-bronze-400 outline-none"
          />
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="border border-neutral-300 rounded-lg px-4 py-[0.55rem] text-sm text-neutral-700 bg-white w-[9rem] leading-[1.2]"
          >
            <option value="semantic">Semantic</option>
            <option value="keyword">Keyword</option>
            <option value="hybrid">Hybrid</option>
          </select>
          <button
            type="submit"
            disabled={searching}
            className="bg-bronze-600 hover:bg-bronze-700 text-white px-5 py-2 rounded-lg font-semibold transition-all disabled:opacity-50"
          >
            {searching ? "Searching…" : "Search"}
          </button>
        </form>

        <p className="text-sm text-neutral-500 mb-4 text-center">
          {modeText[mode]}
        </p>

        {/* status row */}
        {isSearch && lastQuery && (
          <div className="flex items-center justify-between mb-4 text-sm text-neutral-600">
            <p>
              Showing {rows.length} result{rows.length !== 1 ? "s" : ""} for “{lastQuery}”
              <span className="text-neutral-500 ml-2">(Mode: {mode.toUpperCase()})</span>
            </p>
            <button
              onClick={async () => {
                setQuery("")
                setView("all")
                setLastQuery("")
                await loadAll()
              }}
              className="text-bronze-600 font-semibold hover:underline"
            >
              Show all papers
            </button>
          </div>
        )}

        {/* table card */}
        <Card className="p-0 w-full shadow-[0_8px_30px_rgba(139,94,60,0.12)] bg-gradient-to-b from-white/90 to-bronze-50/40 backdrop-blur-md ring-1 ring-bronze-200 rounded-3xl overflow-hidden">
          {loading ? (
            <p className="text-center text-neutral-500 py-8">Loading papers…</p>
          ) : error ? (
            <p className="text-center text-red-600 py-8">{error}</p>
          ) : rows.length === 0 ? (
            <p className="text-center text-neutral-500 py-10">No records found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-bronze-100/50 sticky top-0 z-10">
                  <tr className="text-bronze-800 uppercase text-xs tracking-wide">
                    {columns.map((c) => (
                      <th key={c.accessor} className="px-4 py-3 text-left">
                        {c.header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr
                      key={r.id}
                      className="border-t border-neutral-200 hover:bg-bronze-50/60 transition-colors"
                    >
                      <td className="px-4 py-3 font-semibold text-neutral-800">
                        {r.name}
                      </td>

                      <td className={`px-4 py-3 ${isSearch ? scoreClass(r.score ?? 0) : "text-neutral-700"}`}>
                        {isSearch ? Number(r.score ?? 0).toFixed(3) : (r.n_chars?.toLocaleString?.() ?? "—")}
                      </td>

                      <td className="px-4 py-3 text-neutral-600">
                        {r.summary || r.preview || "No description available."}
                      </td>

                      <td className="px-4 py-3 text-neutral-600">{r.id}</td>

                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2 justify-end">
                          <a
                            href={`/files/${r.id}.pdf`}
                            target="_blank"
                            rel="noreferrer"
                            className="px-3 py-1 text-xs rounded border border-neutral-300 text-neutral-700 hover:bg-neutral-100"
                            onClick={(e) => e.stopPropagation()}
                          >
                            Open PDF
                          </a>
                          <button
                            onClick={() => openDetails(r)}
                            className="px-3 py-1 text-xs rounded border border-bronze-700 text-bronze-700 hover:bg-bronze-700 hover:text-white"
                          >
                            View Summary
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>

      {/* floating cluster CTA */}
      <button
        onClick={() => navigate("/cluster")}
        className="fixed bottom-8 right-8 bg-bronze-600 hover:bg-bronze-700 text-white font-semibold px-5 py-3 rounded-full shadow-lg transition-all"
      >
        Go to Cluster View →
      </button>

      {/* details modal */}
      <Modal open={!!detail} onClose={() => setDetail(null)} size="large">
        {detail && (
          <div className="flex bg-white/95 rounded-2xl overflow-hidden shadow-2xl w-[90vw] h-[85vh]">
            {/* left column: meta + actions */}
            <div className="w-[32rem] min-w-[28rem] h-full border-r border-neutral-200 bg-white p-6 overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-bronze-800 pr-6 line-clamp-2">
                  {detail?.meta?.title || detail.name}
                </h2>
                <button
                  onClick={() => setDetail(null)}
                  aria-label="Close"
                  className="text-2xl text-neutral-500 hover:text-neutral-700"
                >
                  ×
                </button>
              </div>

              <div className="text-sm text-neutral-700 bg-neutral-50 border border-neutral-200 rounded-lg p-3 mb-4">
                {detail.preview ? (
                  <p className="line-clamp-4 whitespace-pre-wrap">{detail.preview}</p>
                ) : detail?.meta?.summary ? (
                  <p className="line-clamp-4 whitespace-pre-wrap">{detail.meta.summary}</p>
                ) : (
                  <p className="text-neutral-500">No preview available.</p>
                )}
              </div>

              <div className="space-y-2 text-sm text-neutral-700">
                <p><strong>File:</strong> {detail.name}</p>
                <p><strong>Doc ID:</strong> {detail.id}</p>

                {typeof detail.score === "number" && (
                  <p>
                    <strong>Relevance:</strong>{" "}
                    <span className={scoreClass(detail.score)}>
                      {Number(detail.score ?? 0).toFixed(3)}
                    </span>
                  </p>
                )}

                {detail.meta?.authors?.length > 0 && (
                  <p>
                    <strong>Authors:</strong>{" "}
                    <span className="text-neutral-800">
                      {detail.meta.authors.join(", ")}
                    </span>
                  </p>
                )}

                {detail.meta?.venue && <p><strong>Venue:</strong> {detail.meta.venue}</p>}
                {detail.meta?.year && <p><strong>Year:</strong> {detail.meta.year}</p>}

                {detail.meta?.doi && (
                  <p>
                    <strong>DOI:</strong>{" "}
                    <a
                      href={`https://doi.org/${detail.meta.doi}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-bronze-700 hover:underline"
                    >
                      {detail.meta.doi}
                    </a>
                  </p>
                )}

                {detail.meta?.publisher && (
                  <p><strong>Publisher:</strong> {detail.meta.publisher}</p>
                )}

                {detail.meta?.summary && (
                  <div className="mt-4">
                    <h3 className="text-base font-semibold text-bronze-800 mb-1">Description</h3>
                    <p className="text-sm text-neutral-700 leading-relaxed whitespace-pre-wrap">
                      {detail.meta.summary}
                    </p>
                  </div>
                )}
              </div>

              {/* actions */}
              <div className="mt-6 grid grid-cols-2 gap-3">
                <a
                  href={`/files/${detail.id}.pdf`}
                  target="_blank"
                  rel="noreferrer"
                  className="w-full py-2 text-center rounded-lg bg-bronze-600 text-white font-semibold hover:bg-bronze-700 transition"
                >
                  Open PDF
                </a>

                <button
                  onClick={fetchExternal}
                  className="w-full py-2 rounded-lg bg-neutral-200 text-neutral-800 font-semibold hover:bg-neutral-300 transition"
                >
                  {detail.loadingExternal ? "Fetching…" : "Get External Recs"}
                </button>

                <button
                  onClick={() => deleteDoc(detail.id)}
                  className="col-span-2 w-full py-2 rounded-lg bg-red-600 text-white font-semibold hover:bg-red-700 transition"
                >
                  Delete Paper
                </button>
              </div>
            </div>

            {/* right column: details / external recs */}
            <div className="flex-1 h-full overflow-y-auto bg-neutral-50 p-6">
              {detail.showExternal ? (
                <div>
                  <h3 className="text-lg font-semibold text-bronze-800 mb-3">
                    External Recommendations
                  </h3>

                  {detail.loadingExternal ? (
                    <p className="text-neutral-500">Fetching recommendations…</p>
                  ) : detail.errorExternal ? (
                    <p className="text-red-500">{detail.errorExternal}</p>
                  ) : detail.external?.length ? (
                    <ul className="space-y-4">
                      {detail.external.map((r, i) => (
                        <li
                          key={i}
                          className="rounded-xl border border-neutral-200 bg-white p-4 shadow-sm"
                        >
                          <p className="font-semibold text-neutral-800">
                            {r.title || "Untitled"}
                          </p>
                          {r.authors?.length > 0 && (
                            <p className="text-sm text-neutral-600 mt-1">
                              {r.authors.join(", ")}
                            </p>
                          )}
                          <div className="text-xs text-neutral-500 mt-1">
                            {r.venue || ""} {r.year ? `• ${r.year}` : ""}
                            {typeof r.citations === "number"
                              ? ` • ${r.citations} citations`
                              : ""}
                          </div>
                          {r.abstract && (
                            <p className="text-sm text-neutral-700 mt-2 line-clamp-3">
                              {r.abstract}
                            </p>
                          )}
                          {r.url && (
                            <a
                              className="inline-block mt-2 text-sm text-bronze-700 hover:underline"
                              href={r.url}
                              target="_blank"
                              rel="noreferrer"
                            >
                              Open on Semantic Scholar →
                            </a>
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-neutral-500">No external recommendations.</p>
                  )}
                </div>
              ) : (
                <div>
                  <h3 className="text-lg font-semibold text-bronze-800 mb-3">
                    Details
                  </h3>
                  {detail.meta?.abstract ? (
                    <div className="bg-white border border-neutral-200 rounded-xl p-4 shadow-sm">
                      <h4 className="font-semibold text-neutral-800">Abstract</h4>
                      <p className="text-sm text-neutral-700 mt-1 whitespace-pre-wrap">
                        {detail.meta.abstract}
                      </p>
                    </div>
                  ) : (
                    <p className="text-neutral-500">No abstract available.</p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
