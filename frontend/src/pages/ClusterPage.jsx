import { useEffect, useMemo, useState } from "react"
import axios from "axios"
import Modal from "../components/Modal"
import Card from "../components/Card"
import { useNavigate } from "react-router-dom"

const API_BASE = "http://127.0.0.1:8000"

function extractKeywords(cluster) {
  // backend currently stuffs keywords into description like: "keywords: a, b, c"
  const desc = (cluster?.description || "").trim()
  const m = desc.match(/^keywords:\s*(.+)$/i)
  if (!m) return []
  return m[1]
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
}

export default function ClusterPage() {
  const [clusters, setClusters] = useState([])
  const [modalCluster, setModalCluster] = useState(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [sortBy, setSortBy] = useState("default")
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const [clustersRes, docsRes] = await Promise.all([
          axios.get(`${API_BASE}/api/clustered`),
          axios.get(`${API_BASE}/api/docs`),
        ])

        const rawClusters = Array.isArray(clustersRes.data) ? clustersRes.data : []
        const docs = Array.isArray(docsRes.data) ? docsRes.data : []

        const docsById = new Map(docs.map((d) => [d.id, d]))

        const hydrated = rawClusters.map((c) => {
          const paperIds = Array.isArray(c.paper_ids) ? c.paper_ids : []
          const papers = paperIds.map((id) => docsById.get(id)).filter(Boolean)
          const keywords = extractKeywords(c)

          return {
            ...c,
            paper_ids: paperIds,
            papers,
            keywords,
            count: typeof c.count === "number" ? c.count : papers.length,
          }
        })

        setClusters(hydrated)
      } catch (e) {
        console.error("failed to load clusters/docs", e)
        setClusters([])
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  const filteredClusters = useMemo(() => {
    const term = searchTerm.toLowerCase().trim()
    return (clusters || [])
      .filter((c) => {
        const title = (c?.title || "").toLowerCase()
        const desc = (c?.description || "").toLowerCase()
        const kw = Array.isArray(c?.keywords) ? c.keywords.join(", ").toLowerCase() : ""
        return !term || title.includes(term) || desc.includes(term) || kw.includes(term)
      })
      .sort((a, b) => {
        if (sortBy === "name") return (a?.title || "").localeCompare(b?.title || "")
        if (sortBy === "count") return (b?.count || 0) - (a?.count || 0)
        return 0
      })
  }, [clusters, searchTerm, sortBy])

  return (
    <div className="relative min-h-screen bg-gradient-to-b from-bronze-50 to-bronze-100/60 text-bronze-800 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex items-center justify-between">
          <button
            onClick={() => navigate(-1)}
            className="text-bronze-700 hover:underline text-sm font-medium"
          >
            ← Back
          </button>
        </div>

        <h1 className="text-4xl font-extrabold tracking-tight text-center mb-2">
          Clustering
        </h1>
        <p className="text-center text-neutral-600 mb-8">
          clusters are generated from your uploaded papers. keywords are pulled from the cluster’s tf-idf.
        </p>

        <div className="flex items-center justify-center gap-3 mb-8">
          <input
            type="text"
            placeholder="Search by cluster name or keyword"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-[36rem] px-4 py-2 rounded-lg border border-neutral-300 focus:ring-2 focus:ring-bronze-400 outline-none"
          />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="border border-neutral-300 rounded-lg px-3 py-[0.55rem] text-sm text-neutral-700 bg-white w-[9rem] leading-[1.2]"
          >
            <option value="default">Sort by</option>
            <option value="name">Name</option>
            <option value="count">Paper Count</option>
          </select>
        </div>

        {loading ? (
          <Card className="p-8 text-center text-neutral-500">loading clusters…</Card>
        ) : filteredClusters.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredClusters.map((c) => (
              <div
                key={c.id || c.title}
                className="rounded-2xl bg-bronze-200/40 p-6 shadow-sm hover:bg-bronze-200/60 transition-all cursor-pointer"
                onClick={() => setModalCluster(c)}
              >
                <h2 className="text-lg font-bold mb-2">
                  {c.title || "untitled cluster"}
                </h2>

                {Array.isArray(c.keywords) && c.keywords.length > 0 ? (
                  <p className="text-sm text-neutral-700 line-clamp-2 mb-3">
                    keywords: {c.keywords.join(", ")}
                  </p>
                ) : (
                  <p className="text-sm text-neutral-500 line-clamp-2 mb-3">
                    no keywords returned
                  </p>
                )}

                <p className="text-base font-semibold mb-1">
                  {c.count ?? 0} papers
                </p>

                {c.description ? (
                  <p className="text-sm text-neutral-700 mb-4 line-clamp-2">
                    {c.description}
                  </p>
                ) : null}

                <button className="border border-bronze-700 text-bronze-700 hover:bg-bronze-700 hover:text-white font-medium text-sm rounded-md px-3 py-1 transition-all">
                  View Papers
                </button>
              </div>
            ))}
          </div>
        ) : (
          <Card className="p-8 text-center text-neutral-500">
            no clusters yet.
          </Card>
        )}
      </div>

      <Modal open={!!modalCluster} onClose={() => setModalCluster(null)} size="large">
        {modalCluster && (
          <div className="p-4 space-y-4">
            <h2 className="text-2xl font-bold">
              {modalCluster.title || "cluster details"}
            </h2>

            {modalCluster.description ? (
              <p className="text-neutral-700">{modalCluster.description}</p>
            ) : null}

            <p className="text-neutral-600 text-sm">
              <strong>Top Keywords:</strong>{" "}
              {Array.isArray(modalCluster.keywords) && modalCluster.keywords.length > 0
                ? modalCluster.keywords.join(", ")
                : "none"}
            </p>

            <p className="text-neutral-600 text-sm mb-4">
              <strong>Number of Papers:</strong> {modalCluster.count ?? 0}
            </p>

            <div className="flex items-center gap-3 mb-3">
              <input
                type="text"
                placeholder="Search papers"
                className="flex-1 px-3 py-2 rounded-lg border border-neutral-300 text-sm"
                disabled
              />
              <select
                className="border border-neutral-300 rounded-lg px-3 py-2 text-sm text-neutral-700 bg-white w-[10rem]"
                disabled
              >
                <option>Sort by: Date</option>
              </select>
            </div>

            {Array.isArray(modalCluster.papers) && modalCluster.papers.length > 0 ? (
              <div className="space-y-3">
                {modalCluster.papers.map((p, idx) => (
                  <div
                    key={p.id || p.name || idx}
                    className="border border-neutral-200 rounded-lg p-4 flex items-center justify-between"
                  >
                    <div className="text-sm text-neutral-700 max-w-[80%]">
                      <p className="font-semibold">{p.name || `paper ${idx + 1}`}</p>
                      {p.summary ? <p className="text-neutral-600 line-clamp-2">{p.summary}</p> : null}
                    </div>

                    {p.id ? (
                      <button
                        onClick={() => navigate(`/papers/${p.id}`)}
                        className="border border-bronze-700 text-bronze-700 hover:bg-bronze-700 hover:text-white font-medium text-xs rounded-md px-3 py-1 transition-all"
                      >
                        View Full Summary
                      </button>
                    ) : (
                      <button
                        className="border border-bronze-300 text-bronze-300 font-medium text-xs rounded-md px-3 py-1 cursor-not-allowed"
                        disabled
                      >
                        No link
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <Card className="p-6 text-center text-neutral-500">
                no papers returned for this cluster.
              </Card>
            )}
          </div>
        )}
      </Modal>

      <button
        onClick={() => navigate("/export")}
        className="fixed bottom-6 right-6 bg-bronze-700 hover:bg-bronze-800 text-white font-semibold text-sm px-6 py-2 rounded-full shadow-lg transition-all"
      >
        Next →
      </button>
    </div>
  )
}

