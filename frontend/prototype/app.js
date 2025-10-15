// Shared helpers + fake services with persistence and richer summaries.
const MAX_FILES = 10;
const store = {
  get(key, def){ try { return JSON.parse(localStorage.getItem(key)) ?? def; } catch { return def; } },
  set(key, val){ localStorage.setItem(key, JSON.stringify(val)); }
};
function clearIfSchemaChanged(){
  const v = 'ss_v4';
  if (store.get('ss_schema') !== v){
    localStorage.clear();
    store.set('ss_schema', v);
  }
}
clearIfSchemaChanged();

function setPapers(arr){ store.set('ss_papers', arr); }
function getPapers(){ return store.get('ss_papers', []); }

function setSummaries(map){ store.set('ss_summaries', map); }
function getSummaries(){ return store.get('ss_summaries', {}); }

function setClusters(obj){ store.set('ss_clusters', obj); }
function getClusters(){ return store.get('ss_clusters', null); }

function uid(){ return Math.random().toString(36).slice(2); }

// 10+ long summaries (≈120–150 words each)
const SUMMARY_POOL = [
`This paper investigates end‑to‑end pipelines for automatic research paper understanding, focusing on robust PDF ingestion, section segmentation, and extractive‑abstractive hybrid summarisation. The authors compare rule‑based parsing with learning‑augmented layouts, then evaluate sentence selection using TF‑IDF, Maximal Marginal Relevance, and embedding‑based redundancy control. For generation, they trial sequence‑to‑sequence models with constrained decoding to preserve citations and entity names. Results across a 1,200‑paper corpus show that hybrid summaries outperform purely generative baselines on factual consistency and reviewer preference, especially when supported by paragraph‑level evidence pointers. The discussion emphasises operational concerns—CPU‑friendly preprocessing, batching strategies, and failure‑mode telemetry—that make the system suitable for institutional deployment rather than only benchmark wins.`,
`The study evaluates topic clustering strategies for heterogeneous academic corpora where domains and writing styles vary widely. It benchmarks classical vector spaces, modern transformer embeddings, and lightweight domain‑adapted encoders trained with contrastive learning on citation graphs. The pipeline tests K‑Means, HDBSCAN, and spherical K‑Means with automatic k estimation using stability curves. Quantitative metrics are complemented by human audits from graduate researchers who judge topical coherence and label clarity. Findings suggest that dimensionality reduction before clustering is essential; however, aggressive reduction harms cluster semantics. A moderate compression with PCA or UMAP preserves neighborhood quality while cutting compute cost. The paper further proposes a handoff mechanism that allows curators to split or merge clusters with provenance tracking so changes remain auditable.`,
`This work proposes a practical playbook for summarising long methods sections without losing reproducibility details. It introduces a template that anchors summaries to inputs, algorithms, hyperparameters, and evaluation criteria, creating a ‘minimum reproducible statement.’ Experiments compare vanilla large language models, retrieval‑augmented variants, and a constrained template‑filler that draws fields from parsed tables and captions. Human raters score completeness, correctness, and re‑usability. The constrained approach consistently yields clearer steps and fewer hallucinations, though at the cost of slightly drier prose. The authors also release a small rubric for teaching assistants to grade generated summaries quickly, demonstrating that rubric‑aligned training signals can meaningfully reduce vague statements while encouraging explicit parameter ranges.`,
`The authors analyse failure modes in academic PDF processing, cataloguing over fifty edge cases such as two‑column layouts, rotated figures, math‑dense pages, and scanned supplements. They present a detector that flags risky pages using vision features and simple heuristics, then routes them to specialised parsers. A triage policy ensures partial progress is preserved rather than failing the whole document. In controlled tests, the approach improves overall pipeline reliability by thirty percent with negligible latency overhead. A qualitative appendix shows before‑and‑after examples where captions were previously fused with body text or reference lists bled into abstracts. The paper argues that reliability engineering, logging, and retry budgets matter as much as model quality for systems meant to serve real researchers at scale.`,
`This paper compares embedding spaces for scholarly text, contrasting generic open‑domain models with encoders tuned on scientific corpora. The evaluation spans retrieval, clustering, and cross‑domain generalisation from physics to social sciences. The authors introduce a calibration step that rescales vector norms to counteract frequency bias introduced by tokenisation. They show that the simple calibration notably improves both nearest‑neighbour retrieval and density‑based clustering without re‑training. Ablations reveal that sentence‑level pooling strategies impact downstream performance more than expected; attention pooling yields robust gains when abstracts contain formulae or long parentheticals. The study concludes with deployment notes on index sharding and approximate search that keep costs predictable under heavy interactive workloads.`,
`The study explores human‑in‑the‑loop workflows for paper triage in literature reviews. It models the interaction as a sequence of micro‑decisions—keep, defer, or discard—and trains a bandit to recommend the next paper that maximises marginal utility given reviewer fatigue. A small UI experiment finds that surfacing two alternative ‘contrast’ papers per decision speeds convergence to a stable shortlist and reduces second‑guessing. Summaries are adapted on the fly to show deltas relative to already‑kept items, which reviewers rated as more informative than standalone snippets. The paper argues that product framing—latency, pagination, and undo affordances—meaningfully shapes the perceived intelligence of the system, sometimes more than raw model improvements.`,
`The authors present an evaluation of factual consistency in generated summaries using citation‑grounded checks. They align summary claims to source sentences with lexical and semantic overlap and ask annotators to verify whether each claim is supported. A lightweight verifier, trained on this alignment signal, detects unsupported assertions and prompts regeneration of specific spans rather than full summaries. On a mixed‑domain dataset, targeted regeneration reduces hallucination rates by nearly half. Case studies show that even high‑performing generators omit limitations sections; the proposed verifier nudges models to include caveats by retrieving discussion sentences, leading to more balanced outputs that reviewers prefer during paper screening.`,
`This technical report details a streaming architecture for large‑batch PDF processing. It uses a chunked upload protocol with resumable parts, a queue for CPU‑heavy parsing, and asynchronous summarisation workers. The design isolates failures so a single corrupt file doesn’t stall the entire batch. Back‑pressure is communicated to the UI with per‑document states, enabling operators to pause, retry, or skip. Cost modelling suggests that batching small PDFs improves throughput while keeping GPU utilisation high. The authors also document practical observability choices—structured logs, per‑stage metrics, and red‑line alerts—that shorten incident diagnosis times, a crucial requirement in university environments with tight submission windows.`,
`The paper examines clustering evaluation beyond standard intrinsic metrics. It proposes a reviewer‑centric score that rewards clusters which speed up exploration: do users reach relevant papers faster, and can they name the cluster meaningfully after a brief scan? A controlled study with domain experts shows that simple labels derived from the top discriminative terms already improve perceived quality, provided the label avoids overly generic words. The authors recommend exposing a ‘confidence’ bar for each cluster and presenting a one‑sentence rationale so users can better judge edge cases. These product choices reduce cognitive friction and help non‑experts trust the grouping.`,
`This work introduces a compact schema for exporting literature review bundles as JSON. The schema captures papers, generated summaries, and cluster memberships with stable identifiers and light provenance. The authors compare JSON with PDF and CSV exports for different audiences: JSON is best for re‑ingestion into tools; PDF serves reporting and discussions; CSV helps spreadsheet‑centric workflows. A small user study finds that offering multiple exports reduces copy‑paste errors and encourages team‑level review. The paper provides migration guidance and examples of merging bundles from separate sessions, emphasising de‑duplication via checksum or DOI and preserving editorial notes during merges.`
];

function longSummaryFor(name, idx){
  const s = SUMMARY_POOL[idx % SUMMARY_POOL.length];
  return s;
}

// Fake clustering
function fakeCluster(papers){
  const themes = ['Neural Summarisation','Graph-based Methods','Evaluation & Metrics','Clustering Pipelines','Retrieval & Embeddings'];
  const clusters = themes.map(t => ({ id: uid(), label: t, paperIds: [] }));
  papers.forEach((p,i)=> clusters[i % clusters.length].paperIds.push(p.id));
  return clusters;
}

// Export JSON
function buildExport(){
  const papers = getPapers();
  const summaries = getSummaries();
  const clusters = getClusters();
  return { generatedAt: new Date().toISOString(), papers, summaries, clusters };
}

// Download helpers
function downloadBlob(filename, data, type='application/json'){
  const blob = new Blob([data], {type});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
}

// Data ops
function deletePaper(id){
  const papers = getPapers().filter(p => p.id !== id);
  setPapers(papers);
  const s = getSummaries(); delete s[id]; setSummaries(s);
  let c = getClusters();
  if (c){
    c.forEach(cl => { cl.paperIds = cl.paperIds.filter(pid => pid !== id); });
    setClusters(c);
  }
}

function movePaperToCluster(paperId, clusterId){
  const clusters = getClusters(); if (!clusters) return;
  clusters.forEach(cl => { cl.paperIds = cl.paperIds.filter(id => id !== paperId); });
  const target = clusters.find(c => c.id === clusterId);
  if (target) target.paperIds.push(paperId);
  setClusters(clusters);
}