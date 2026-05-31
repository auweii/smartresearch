import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";

const API_BASE = "http://127.0.0.1:8000";
const GPU_BANNER_KEY = "sr_gpu_banner_dismissed";

function MetaRow({ label, value }) {
  if (!value) return null;
  return (
    <div className="flex gap-3 text-sm">
      <span className="text-bronze-500 font-medium min-w-[72px]">{label}</span>
      <span className="text-neutral-700">{value}</span>
    </div>
  );
}

function RecommendedPapers({ docId }) {
  const [recs, setRecs] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API_BASE}/api/external_recs/${docId}`)
      .then(r => setRecs(r.data?.recommendations || []))
      .catch(() => setRecs([]))
      .finally(() => setLoading(false));
  }, [docId]);

  if (loading) return <p className="text-xs text-neutral-400">Loading recommendations...</p>;
  if (!recs || recs.length === 0) return <p className="text-xs text-neutral-400">No recommendations available.</p>;

  return (
    <div className="space-y-3">
      {recs.map((r, i) => (
        <div key={i} className="text-sm">
          <p className="font-medium text-neutral-800">{r.title || "Untitled"}</p>
          {r.authors?.length > 0 && (
            <p className="text-neutral-500 text-xs">
              {Array.isArray(r.authors) ? r.authors.slice(0, 3).join(", ") : r.authors}
            </p>
          )}
          <div className="flex gap-3 text-xs text-neutral-400 mt-0.5">
            {r.year && <span>{r.year}</span>}
            {r.venue && <span>{r.venue}</span>}
            {r.doi && (
              <a
                href={`https://doi.org/${r.doi}`}
                target="_blank"
                rel="noreferrer"
                className="text-bronze-600 hover:underline"
              >
                DOI
              </a>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function FullSummary() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [meta, setMeta] = useState(null);
  const [metaLoading, setMetaLoading] = useState(true);
  const [target, setTarget] = useState("medium");
  const [aiSummary, setAiSummary] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");
  const [aiDone, setAiDone] = useState(false);
  const [gpuInfo, setGpuInfo] = useState(null);
  const [gpuBannerDismissed, setGpuBannerDismissed] = useState(
    () => sessionStorage.getItem(GPU_BANNER_KEY) === "1"
  );

  // check GPU status once per session
  useEffect(() => {
    if (gpuBannerDismissed) return;
    axios
      .get(`${API_BASE}/api/system/gpu`)
      .then((r) => setGpuInfo(r.data))
      .catch(() => {});
  }, [gpuBannerDismissed]);

  const dismissGpuBanner = () => {
    sessionStorage.setItem(GPU_BANNER_KEY, "1");
    setGpuBannerDismissed(true);
  };

  useEffect(() => {
    if (!id) return;
    setMetaLoading(true);
    axios
      .get(`${API_BASE}/api/meta/${id}`)
      .then((r) => setMeta(r.data?.meta?.final || {}))
      .catch(() => setMeta(null))
      .finally(() => setMetaLoading(false));
  }, [id]);

  const requestAiSummary = async () => {
    if (aiLoading) return;
    setAiLoading(true);
    setAiSummary("");
    setAiError("");
    setAiDone(false);

    try {
      const res = await axios.post(`${API_BASE}/api/summarize/${id}?target=${target}`);
      setAiSummary(res.data?.summary || "No summary returned.");
      setAiDone(true);
    } catch (e) {
      setAiError(
        e?.response?.data?.detail ||
          "Summarisation failed. The model may still be loading — try again in a moment."
      );
    } finally {
      setAiLoading(false);
    }
  };

  const final = meta || {};
  const title = final.title || "Untitled Paper";
  const authors = Array.isArray(final.authors)
    ? final.authors.join(", ")
    : typeof final.authors === "string"
    ? final.authors
    : "";
  const year = final.year ? String(final.year) : "";
  const venue = final.venue || final.publisher || "";
  const doi = final.doi || final.DOI || "";
  const showGpuWarning = !gpuBannerDismissed && gpuInfo !== null && gpuInfo.gpu_available === false;

  return (
    <div className="relative min-h-screen bg-gradient-to-b from-bronze-50 to-bronze-100/60 text-bronze-800 p-8">
      {showGpuWarning && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-amber-50 border-b border-amber-300 px-6 py-3 flex items-center justify-between text-sm text-amber-800">
          <span>
            <strong>No GPU detected.</strong> Summaries will generate on CPU and may take 30–90 seconds longer on average.
          </span>
          <button
            onClick={dismissGpuBanner}
            className="ml-6 text-amber-600 hover:text-amber-900 font-bold text-lg leading-none"
            aria-label="Dismiss"
          >
            ×
          </button>
        </div>
      )}

      <div className={`max-w-3xl mx-auto ${showGpuWarning ? "mt-14" : "mt-0"}`}>
        <button
          onClick={() => navigate(-1)}
          className="text-sm text-bronze-600 hover:underline mb-6 inline-block"
        >
          ← Back
          {aiLoading && (
            <span className="ml-2 text-amber-600 font-normal">
              (summary will continue generating in the background)
            </span>
          )}
        </button>

        {/* paper metadata */}
        <div className="bg-white/80 backdrop-blur-md border border-bronze-200 rounded-2xl shadow-sm p-8 mb-6">
          {metaLoading ? (
            <div className="text-neutral-400 text-sm">Loading metadata…</div>
          ) : (
            <>
              <h1 className="text-2xl font-bold text-bronze-800 mb-4 leading-snug">{title}</h1>
              <div className="space-y-2">
                <MetaRow label="Authors" value={authors} />
                <MetaRow label="Year" value={year} />
                <MetaRow label="Venue" value={venue} />
                {doi && (
                  <div className="flex gap-3 text-sm">
                    <span className="text-bronze-500 font-medium min-w-[72px]">DOI</span>
                    <a
                      href={"https://doi.org/" + doi}
                      target="_blank"
                      rel="noreferrer"
                      className="text-bronze-700 hover:underline break-all"
                    >
                      {doi}
                    </a>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* summary generation card */}
        <div className="bg-white/80 backdrop-blur-md border border-bronze-200 rounded-2xl shadow-sm p-8 mb-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-bronze-800">Generate Summary</h2>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-neutral-500">Length:</span>
              {["short", "medium", "long"].map((t) => (
                <button
                  key={t}
                  onClick={() => setTarget(t)}
                  disabled={aiLoading}
                  className={`px-3 py-1 rounded-full border text-xs font-semibold transition-all ${
                    target === t
                      ? "bg-bronze-700 text-white border-bronze-700"
                      : "border-bronze-300 text-bronze-600 hover:bg-bronze-50"
                  } disabled:opacity-40`}
                >
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {!aiDone && !aiLoading && (
            <button
              onClick={requestAiSummary}
              className="w-full py-3 rounded-xl bg-bronze-700 hover:bg-bronze-800 text-white font-semibold transition-all"
            >
              Generate Summary
            </button>
          )}

          {aiLoading && (
            <div className="flex flex-col items-center gap-4 py-8 text-neutral-500">
              <div className="w-8 h-8 border-4 border-bronze-300 border-t-bronze-700 rounded-full animate-spin" />
              <p className="text-sm text-center">
                Generating {target} summary…
                {gpuInfo && !gpuInfo.gpu_available && (
                  <>
                    <br />
                    <span className="text-xs text-neutral-400">
                      This may take some time as you're using CPU.
                    </span>
                  </>
                )}
              </p>
            </div>
          )}

          {aiError && (
            <div className="mt-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-4">
              {aiError}
              <button
                onClick={requestAiSummary}
                className="block mt-2 text-red-600 hover:underline font-semibold"
              >
                Try again
              </button>
            </div>
          )}

          {aiDone && aiSummary && (
            <div className="mt-2">
              <p className="text-neutral-700 leading-relaxed whitespace-pre-wrap">{aiSummary}</p>
              <div className="flex items-center gap-4 mt-6">
                <button
                  onClick={async () => {
                    try {
                      await axios.patch(`${API_BASE}/api/meta/${id}/summary`, { summary: aiSummary });
                      alert("Summary updated successfully.");
                    } catch {
                      alert("Failed to update summary.");
                    }
                  }}
                  className="text-sm bg-bronze-700 hover:bg-bronze-800 text-white px-4 py-2 rounded-lg font-semibold transition-all"
                >
                  Replace existing summary
                </button>
                <button
                  onClick={() => { setAiDone(false); setAiSummary(""); }}
                  className="text-sm text-bronze-600 hover:underline"
                >
                  Generate again
                </button>
              </div>
            </div>
          )}
        </div>

        {/* recommended papers */}
        {!metaLoading && (
          <div className="bg-white/80 backdrop-blur-md border border-bronze-200 rounded-2xl shadow-sm p-8">
            <h2 className="text-lg font-bold text-bronze-800 mb-4">Recommended Papers</h2>
            <RecommendedPapers docId={id} />
          </div>
        )}
      </div>
    </div>
  );
}