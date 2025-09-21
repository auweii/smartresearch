import asyncio, uuid
from typing import Dict, Any, List
import numpy as np
from .pdf_sections import extract_abstract, extract_section

from .storage import FILES, JOBS
from .pdf_text import extract_text
from .nlp_pipeline import (
    normalize,
    build_lda_sklearn,
    cluster_docs,
    topic_label_sklearn,
    summarize_extractive_sklearn,
)

async def start_job(payload: Dict[str, Any]) -> str:
    job_id = f"job_{uuid.uuid4().hex[:6]}"
    JOBS[job_id] = {
        "state": "QUEUED",
        "stage": "queued",
        "overall_progress": 0,
        "files": [{"file_id": fid, "progress": 0, "stage": "queued"} for fid in payload.get("file_ids", [])],
        "message": "Queued",
        "result": None,
    }
    asyncio.create_task(run_job(job_id, payload))
    return job_id

async def run_job(job_id: str, cfg: Dict[str, Any]):
    j = JOBS[job_id]
    try:
        file_ids: List[str] = cfg.get("file_ids", [])
        j.update({"state": "PROCESSING", "stage": "extracting", "overall_progress": 5, "message": "Reading PDFs"})

        docs, metas, summaries, raw_texts = [], [], [], []
        for i, fid in enumerate(file_ids):
            rec = FILES.get(fid)
            if not rec: 
                continue

            # choose source text
            chosen = None
            if (cfg.get("section_mode") or "full").lower() == "abstract":
                chosen = extract_abstract(rec["path"], max_pages=4)
            elif (cfg.get("section_mode") or "").lower() == "section" and cfg.get("section_label"):
                chosen = extract_section(rec["path"], label=cfg["section_label"], scan_pages=10)

            if not chosen:
                chosen = extract_text(rec["path"], max_pages=cfg.get("max_pages", 40))

            raw_texts.append(chosen)

            toks = normalize(chosen)
            docs.append(toks)
            metas.append(rec)

            summaries.append(
                summarize_extractive_sklearn(
                    chosen,
                    max_sentences=int(cfg.get("summary_sentences", 5)),
                    max_chars=int(cfg.get("summary_chars", 900)),
                )
            )

            j["overall_progress"] = 5 + int(25 * (i + 1) / max(1, len(file_ids)))
            await asyncio.sleep(0)

        # ---------- Topic model (sklearn LDA) ----------
        j.update({"stage": "topic_model", "message": "Building topics", "overall_progress": 35})
        lda, vectorizer, vecs = build_lda_sklearn(docs, num_topics=cfg.get("num_topics", 8))
        # vecs shape: [n_docs, n_topics] — dense doc-topic distributions

        # ---------- Clustering ----------
        j.update({"stage": "clustering", "message": "Clustering documents", "overall_progress": 65})
        labels, k = cluster_docs(vecs, k=cfg.get("cluster_k"))

        # ---------- Assemble result ----------
        clusters: list[dict] = []
        for c in range(k):
            idxs = [i for i, lab in enumerate(labels) if lab == c]
            if not idxs:
                continue

            # Choose a label for the cluster by the highest-probability topic in the centroid
            centroid = vecs[idxs].mean(axis=0)
            top_topic = int(np.argmax(centroid))
            label = topic_label_sklearn(lda, vectorizer, top_topic)
            key_terms = topic_label_sklearn(lda, vectorizer, top_topic, topn=6).split(" / ")

            members = []
            for i in idxs:
                rec = metas[i]
                members.append({
                    "file_id": next(fid for fid, v in FILES.items() if v["path"] == rec["path"]),
                    "new_name": rec["new_name"],
                    "title": rec["title"],
                    "authors": rec["authors"],
                    "year": rec["year"],
                    "paper_summary": None,   # fill later when you add summarizer
                    "key_terms": key_terms,
                })

            clusters.append({
                "topic_id": c,
                "topic_label": label,
                "summary": f"{len(members)} papers about {label}",
                "members": members,
            })

        j["result"] = {
            "clusters": clusters,
            "metrics": {"k": int(k), "method": "kmeans-on-lda-sklearn", "embedding": "sklearn-doc-topic"},
        }
        j.update({"stage": "finished", "state": "DONE", "overall_progress": 100, "message": "Done"})
    except Exception as e:
        j.update({"state": "ERROR", "message": str(e)})
