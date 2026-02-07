import React, { useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import axios from "axios"

const API_BASE = "http://127.0.0.1:8000"

function extFromFormat(fmt) {
  if (fmt === "csv") return "csv"
  if (fmt === "json") return "json"
  return "pdf"
}

function mimeFromFormat(fmt) {
  if (fmt === "csv") return "text/csv"
  if (fmt === "json") return "application/json"
  return "application/pdf"
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
    selectedPapers: true,
    format: "pdf",
    summaries: true,
    keywords: true,
    insights: true,
  })

  const payload = useMemo(() => {
    return {
      include: {
        all_papers: !!options.allPapers,
        clusters_list: !!options.clustersList,
        papers_by_cluster: !!options.papersByCluster,
        selected_papers: !!options.selectedPapers,
      },
      extras: {
        summaries: !!options.summaries,
        keywords: !!options.keywords,
        insights: !!options.insights,
      },
      format: options.format,
    }
  }, [options])

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
        timeout: 60000,
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
      setErr("export failed. backend endpoint /api/export isn’t returning a file yet, or it crashed.")
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
          Export Data
        </h1>
        <p className="text-center text-bronze-600 mb-10">
          Choose what to include in your export package. Files will be generated
          in the selected format with optional summaries and insights.
        </p>

        <section className="mb-8">
          <h2 className="text-lg font-semibold mb-3 text-bronze-800">
            Select what you want to export:
          </h2>
          <div className="grid grid-cols-2 gap-3 ml-2">
            <label>
              <input
                type="checkbox"
                name="allPapers"
                checked={options.allPapers}
                onChange={handleChange}
              />{" "}
              All Papers
            </label>
            <label>
              <input
                type="checkbox"
                name="clustersList"
                checked={options.clustersList}
                onChange={handleChange}
              />{" "}
              Clusters List
            </label>
            <label>
              <input
                type="checkbox"
                name="papersByCluster"
                checked={options.papersByCluster}
                onChange={handleChange}
              />{" "}
              Papers By Cluster
            </label>
            <label>
              <input
                type="checkbox"
                name="selectedPapers"
                checked={options.selectedPapers}
                onChange={handleChange}
              />{" "}
              Selected Papers
            </label>
          </div>
        </section>

        <section className="mb-8">
          <h2 className="text-lg font-semibold mb-3 text-bronze-800">
            Choose format:
          </h2>
          <div className="flex gap-6 ml-2">
            <label>
              <input
                type="radio"
                name="format"
                value="pdf"
                checked={options.format === "pdf"}
                onChange={handleChange}
              />{" "}
              PDF
            </label>
            <label>
              <input
                type="radio"
                name="format"
                value="csv"
                checked={options.format === "csv"}
                onChange={handleChange}
              />{" "}
              CSV
            </label>
            <label>
              <input
                type="radio"
                name="format"
                value="json"
                checked={options.format === "json"}
                onChange={handleChange}
              />{" "}
              JSON
            </label>
          </div>
        </section>

        <section className="mb-10">
          <h2 className="text-lg font-semibold mb-3 text-bronze-800">
            Include:
          </h2>
          <div className="flex gap-6 ml-2">
            <label>
              <input
                type="checkbox"
                name="summaries"
                checked={options.summaries}
                onChange={handleChange}
              />{" "}
              Summaries
            </label>
            <label>
              <input
                type="checkbox"
                name="keywords"
                checked={options.keywords}
                onChange={handleChange}
              />{" "}
              Keywords
            </label>
            <label>
              <input
                type="checkbox"
                name="insights"
                checked={options.insights}
                onChange={handleChange}
              />{" "}
              Cluster Insights
            </label>
          </div>
        </section>

        {err ? (
          <div className="mb-6 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">
            {err}
          </div>
        ) : null}

        <div className="flex justify-center">
          <button
            onClick={onExport}
            disabled={busy}
            className={`px-6 py-2 font-semibold rounded-md transition ${
              busy
                ? "bg-bronze-300 text-white cursor-not-allowed"
                : "bg-bronze-700 hover:bg-bronze-800 text-white"
            }`}
          >
            {busy ? "exporting..." : "Export"}
          </button>
        </div>
      </div>
    </div>
  )
}

