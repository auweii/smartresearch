import { useState, useEffect } from "react"
import axios from "axios"
import Modal from "../components/Modal"
import Card from "../components/Card"
import { useNavigate } from "react-router-dom"

// filler clusters (mock data)
const mockClusters = [
  {
    id: "cluster-1",
    title: "Transformer Models for Text Summarization",
    authors: [
      "Ashish Vaswani",
      "Noam Shazeer",
      "Niki Parmar",
      "Jakob Uszkoreit",
      "Lukasz Kaiser",
    ],
    count: 12,
    description: "Papers related to language models and summarization.",
  },
  {
    id: "cluster-2",
    title: "Natural Language Processing Foundations",
    authors: ["Tom Brown", "Sam Altman", "Alec Radford"],
    count: 7,
    description:
      "Focuses on NLP techniques, tokenization, embeddings, and contextual learning in large language models.",
  },
  {
    id: "cluster-3",
    title: "Explainable AI and Model Interpretability",
    authors: ["Cynthia Rudin", "Marco Tulio Ribeiro", "Sameer Singh"],
    count: 9,
    description:
      "Research on transparency, model interpretability, and trust in machine learning pipelines.",
  },
  {
    id: "cluster-4",
    title: "Computer Vision in Healthcare",
    authors: ["Fei-Fei Li", "Andrew Ng", "Joy Buolamwini"],
    count: 6,
    description:
      "Papers tackling diagnostic imaging, bias mitigation, and ethical AI in medical computer vision.",
  },
  {
    id: "cluster-5",
    title: "Cybersecurity Threat Detection",
    authors: ["Ross Anderson", "Bruce Schneier", "Gene Spafford"],
    count: 10,
    description:
      "Detection of anomalies, intrusion patterns, and adversarial resilience in cyber defense systems.",
  },
  {
    id: "cluster-6",
    title: "Graph Neural Networks",
    authors: ["Thomas Kipf", "Max Welling", "Petar Veličković"],
    count: 8,
    description:
      "Exploration of graph structures, message passing, and relational reasoning across domains.",
  },
  {
    id: "cluster-7",
    title: "Federated Learning and Privacy",
    authors: ["Jakub Konečný", "H. Brendan McMahan", "Daniel Ramage"],
    count: 11,
    description:
      "Distributed learning approaches preserving data privacy and improving model generalization.",
  },
  {
    id: "cluster-8",
    title: "Reinforcement Learning for Robotics",
    authors: ["Pieter Abbeel", "Sergey Levine", "Chelsea Finn"],
    count: 5,
    description:
      "Papers on policy gradients, control optimization, and generalization in robotic learning environments.",
  },
  {
    id: "cluster-9",
    title: "Ethics and Bias in AI Systems",
    authors: ["Timnit Gebru", "Kate Crawford", "Ruha Benjamin"],
    count: 13,
    description:
      "Examines systemic bias, fairness, and accountability in AI design and deployment.",
  },
  {
    id: "cluster-10",
    title: "Quantum Computing for Optimization",
    authors: ["Scott Aaronson", "John Preskill", "Peter Shor"],
    count: 4,
    description:
      "Optimization algorithms and hybrid quantum-classical systems in applied computation.",
  },
]

export default function ClusterPage() {
  const [clusters, setClusters] = useState([])
  const [modalCluster, setModalCluster] = useState(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [sortBy, setSortBy] = useState("default")
  const navigate = useNavigate()

  useEffect(() => {
    const loadClusters = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:8000/api/clustered")
        setClusters(res.data || mockClusters)
      } catch {
        setClusters(mockClusters)
      }
    }
    loadClusters()
  }, [])

  const filteredClusters = clusters
    .filter((c) =>
      c.title.toLowerCase().includes(searchTerm.toLowerCase().trim())
    )
    .sort((a, b) => {
      if (sortBy === "name") return a.title.localeCompare(b.title)
      if (sortBy === "count") return b.count - a.count
      return 0
    })

  return (
    <div className="relative min-h-screen bg-gradient-to-b from-bronze-50 to-bronze-100/60 text-bronze-800 p-8">
      <div className="max-w-7xl mx-auto">
        {/* back button */}
        <div className="mb-8 flex items-center justify-between">
          <button
            onClick={() => navigate(-1)}
            className="text-bronze-700 hover:underline text-sm font-medium"
          >
            ← Back
          </button>
        </div>

        {/* header + intro */}
        <h1 className="text-4xl font-extrabold tracking-tight text-center mb-2">
          Clustering
        </h1>
        <p className="text-center text-neutral-600 mb-8">
          Select which papers to include, then cluster into topic groups. Cards
          use tables and trimmed summaries.
        </p>

        {/* search + sort controls */}
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

        {/* grid view */}
        {filteredClusters.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredClusters.map((c) => (
              <div
                key={c.id}
                className="rounded-2xl bg-bronze-200/40 p-6 shadow-sm hover:bg-bronze-200/60 transition-all cursor-pointer"
                onClick={() => setModalCluster(c)}
              >
                <h2 className="text-lg font-bold mb-1">{c.title}</h2>
                <p className="text-sm text-neutral-700 line-clamp-2 mb-3">
                  {c.authors.join(", ")}
                </p>
                <p className="text-base font-semibold mb-1">{c.count} papers</p>
                <p className="text-sm text-neutral-700 mb-4">
                  {c.description}
                </p>
                <button className="border border-bronze-700 text-bronze-700 hover:bg-bronze-700 hover:text-white font-medium text-sm rounded-md px-3 py-1 transition-all">
                  View Papers
                </button>
              </div>
            ))}
          </div>
        ) : (
          <Card className="p-8 text-center text-neutral-500">
            No clusters yet.
          </Card>
        )}
      </div>

      {/* modal */}
      <Modal
        open={!!modalCluster}
        onClose={() => setModalCluster(null)}
        size="large"
      >
        {modalCluster && (
          <div className="p-4 space-y-4">
            <h2 className="text-2xl font-bold">
              {modalCluster.title || "Cluster Details"}
            </h2>
            <p className="text-neutral-700">
              This cluster includes papers focused on NLP techniques, models,
              and summarization approaches.
            </p>
            <p className="text-neutral-600 text-sm">
              <strong>Top Keywords:</strong> NLP, Transformers, BERT, Token
            </p>
            <p className="text-neutral-600 text-sm mb-4">
              <strong>Number of Papers:</strong> {modalCluster.count}
            </p>

            {/* local search + sort for papers */}
            <div className="flex items-center gap-3 mb-3">
              <input
                type="text"
                placeholder="Search papers"
                className="flex-1 px-3 py-2 rounded-lg border border-neutral-300 text-sm"
              />
              <select className="border border-neutral-300 rounded-lg px-3 py-2 text-sm text-neutral-700 bg-white w-[10rem]">
                <option>Sort by: Date</option>
                <option>Sort by: Name</option>
              </select>
            </div>

            {/* list of papers */}
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div
                  key={i}
                  className="border border-neutral-200 rounded-lg p-4 flex items-center justify-between"
                >
                  <div className="text-sm text-neutral-700 max-w-[80%]">
                    <p className="font-semibold">Paper {i}</p>
                    <p>
                      Transformer Models for Text Summarization's text
                      summarization is introduced...
                    </p>
                  </div>
                  <button className="border border-bronze-700 text-bronze-700 hover:bg-bronze-700 hover:text-white font-medium text-xs rounded-md px-3 py-1 transition-all">
                    View Full Summary
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </Modal>

      {/* next button */}
      <button
        onClick={() => navigate("/export")}
        className="fixed bottom-6 right-6 bg-bronze-700 hover:bg-bronze-800 text-white font-semibold text-sm px-6 py-2 rounded-full shadow-lg transition-all"
      >
        Next →
      </button>
    </div>
  )
}
