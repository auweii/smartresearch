import React, { useState } from "react"
import { useNavigate } from "react-router-dom"

export default function ExportPage() {
  const navigate = useNavigate()
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

  const handleChange = (e) => {
    const { name, type, checked, value } = e.target
    setOptions((prev) => ({
      ...prev,
      [name]: type === "radio" ? value : checked,
    }))
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

        {/* What to export */}
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

        {/* Format */}
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

        {/* Include extras */}
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

        {/* Export button */}
        <div className="flex justify-center">
          <button className="px-6 py-2 bg-bronze-700 hover:bg-bronze-800 text-white font-semibold rounded-md transition">
            Export
          </button>
        </div>
      </div>
    </div>
  )
}
