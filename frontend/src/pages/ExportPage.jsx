import { useNavigate } from "react-router-dom"
import axios from "axios"
import { useMemo, useState } from "react"

const API_BASE = "http://127.0.0.1:8000"

function mimeFromFormat(fmt) {
  if (fmt === "csv") return "text/csv"
  if (fmt === "json") return "application/json"
  return "application/pdf"
}

function extFromFormat(fmt) {
  if (fmt === "csv") return "csv"
  if (fmt === "json") return "json"
  return "pdf"
}

function filenameFromHeader(headerValue, fallback) {
  if (!headerValue) return fallback
  const m1 = /filename\*\s*=\s*UTF-8''([^;]+)/i.exec(headerValue)
  if (m1?.[1]) return decodeURIComponent(m1[1].trim())
  const m2 = /filename\s*=\s*"?([^"]+)"?/i.exec(headerValue)
  if (m2?.[1]) return m2[1].trim()
  return fallback
}

export default function ExportPage() {
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState("")
  const [options, setOptions] = useState({
    allPapers: true,
    clustersList: true,
    papersByCluster: true,
    format: "pdf",
    summaries: true,
    keywords: true,
    charts: true,
    recommendations: false,
  })

  const payload = useMemo(() => ({
    include: {
      all_papers: !!options.allPapers,
      clusters_list: !!options.clustersList,
      papers_by_cluster: !!options.papersByCluster,
    },
    extras: {
      summaries: !!options.summaries,
      keywords: !!options.keywords,
      charts: !!options.charts,
      recommendations: !!options.recommendations,
    },
    format: options.format,
  }), [options])

  const handleChange = (e) => {
    const { name, type, checked, value } = e.target
    setOptions((prev) => ({
      ...prev,
      [name]: type === "radio" ? value : checked,
    }))
  }

  const onExport = async () => {
    if (busy) return
    setErr("")
    setBusy(true)
    try {
      const res = await axios.post(`${API_BASE}/api/export`, payload, {
        responseType: "blob",
        timeout: 120000,
        headers: {
          Accept: mimeFromFormat(options.format),
          "Content-Type": "application/json",
        },
      })
      const fallbackName = `smartresearch_export.${extFromFormat(options.format)}`
      const cd = res.headers?.["content-disposition"]
      const filename = filenameFromHeader(cd, fallbackName)
      const blob = new Blob([res.data], { type: mimeFromFormat(options.format) })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      console.error("export failed", e)
      setErr("Export failed — check that the backend is running and try again.")
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex flex-col items-center justify-start min-h-[calc(100vh-56px)] bg-bronze-50 text-bronze-700 p-8">
      <button
        onClick={() => navigate(-1)}
        className="self-start text-sm text-bronze-600 hover:text-bronze-800 mb-4"
      >
        ← Back
      </button>

      <div className="w-full max-w-4xl bg-white/70 backdrop-blur-md border border-bronze-200 rounded-2xl shadow-sm p-10">
        <h1 className="text-4xl font-bold text-center text-bronze-800 mb-2">
          Export Report
        </h1>
        <p className="text-center text-bronze-600 mb-10">
          Generate a PDF report of your research session. AI-generated summaries
          are used automatically where available.
        </p>

        {/* what to include */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold mb-3 text-bronze-800">Include</h2>
          <div className="grid grid-cols-2 gap-3 ml-2">
            <label className="flex items-center gap-2">
              <input type="checkbox" name="allPapers" checked={options.allPapers} onChange={handleChange} />
              All Papers (with full metadata)
            </label>

            <label className="flex items-center gap-2">
              <input type="checkbox" name="clustersList" checked={options.clustersList} onChange={handleChange} />
              Clusters Overview Table
            </label>

            <label className="flex items-center gap-2">
              <input type="checkbox" name="papersByCluster" checked={options.papersByCluster} onChange={handleChange} />
              Papers Grouped by Cluster
            </label>

            <label className="flex items-center gap-2">
              <input type="checkbox" name="summaries" checked={options.summaries} onChange={handleChange} />
              Summaries
            </label>

            <label className="flex items-center gap-2">
              <input type="checkbox" name="keywords" checked={options.keywords} onChange={handleChange} />
              Keywords
            </label>

            <label className="flex items-center gap-2">
              <input type="checkbox" name="charts" checked={options.charts} onChange={handleChange} />
              Charts (cluster distribution, keywords)
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                name="recommendations"
                checked={options.recommendations}
                onChange={handleChange}
              />
              Recommended Papers (via Semantic Scholar, per paper)
            </label>
          </div>
        </section>

        {/* format */}
        <section className="mb-10">
          <h2 className="text-lg font-semibold mb-3 text-bronze-800">Format</h2>
          <div className="flex gap-6 ml-2">
            <label className="flex items-center gap-2">
              <input type="radio" name="format" value="pdf" checked={options.format === "pdf"} onChange={handleChange} />
              PDF
            </label>
            <label className="flex items-center gap-2 text-neutral-400 cursor-not-allowed">
              <input type="radio" name="format" value="csv" disabled />
              CSV (coming soon)
            </label>
            <label className="flex items-center gap-2 text-neutral-400 cursor-not-allowed">
              <input type="radio" name="format" value="json" disabled />
              JSON (coming soon)
            </label>
          </div>
        </section>

        {/* what's included note */}
        <div className="mb-8 bg-bronze-50 border border-bronze-200 rounded-xl p-4 text-sm text-bronze-700">
          <p className="font-semibold mb-1">What's included in the export:</p>
          <ul className="list-disc ml-5 space-y-1 text-bronze-600">
            <li>Cover page with generation date and paper count</li>
            <li>Analytics charts — cluster distribution and top keywords</li>
            <li>Cluster overview table with paper counts and keywords</li>
            <li>Papers grouped by cluster with summaries</li>
            <li>All papers with full metadata (authors, year, venue, DOI)</li>
            <li>AI-generated summaries used where available, labelled clearly</li>
            <li>Missing metadata explicitly noted as "not found"</li>
          </ul>
        </div>

        {err && (
          <div className="mb-6 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">
            {err}
          </div>
        )}

        <div className="flex justify-center">
          <button
            onClick={onExport}
            disabled={busy}
            className={`px-8 py-3 font-semibold rounded-xl transition ${
              busy
                ? "bg-bronze-300 text-white cursor-not-allowed"
                : "bg-bronze-700 hover:bg-bronze-800 text-white"
            }`}
          >
            {busy ? "Generating export…" : "Export PDF"}
          </button>
        </div>
      </div>
    </div>
  )
}