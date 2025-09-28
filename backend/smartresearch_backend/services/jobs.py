# smartresearch_backend/services/jobs.py
import asyncio, uuid, time
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

from smartresearch_backend.libs.logger import job_logger, remove_handler
from .storage import FILES, JOBS
from .pdf_sections import extract_abstract, extract_section
from .pdf_text import extract_text
from .nlp_pipeline import (
    normalize,
    build_lda_sklearn,
    cluster_docs,
    topic_label_sklearn,
    summarize_paper_hf,
)

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
async def start_job(payload: Dict[str, Any]) -> str:
    job_id = f"job_{uuid.uuid4().hex[:6]}"
    JOBS[job_id] = {
        "state": "QUEUED",
        "stage": "queued",
        "overall_progress": 0,
        "files": [{"file_id": fid, "progress": 0, "stage": "queued"} for fid in payload.get("file_ids", [])],
        "message": "Queued",
        "eta_seconds": None,
        "result": None,
        # "logfile" will be set in run_job
    }
    asyncio.create_task(run_job(job_id, payload))
    return job_id


# ----------------------------------------------------------------------
# Worker
# ----------------------------------------------------------------------
async def run_job(job_id: str, cfg: Dict[str, Any]):
    log = job_logger(job_id)                           # per-job file logger (also prints to console)
    logfile = str(Path("logs") / f"{job_id}.log")      # expose path in status
    JOBS[job_id]["logfile"] = logfile

    try:
        file_ids: List[str] = cfg.get("file_ids", [])
        total_files = len(file_ids)
        start_time = time.time()

        log.info(f"Starting job with {total_files} files")
        log.debug(f"payload={cfg}")

        j = JOBS[job_id]
        j.update({
            "state": "PROCESSING",
            "stage": "extracting",
            "overall_progress": 5,
            "message": "Reading PDFs",
            "eta_seconds": None
        })

        # ------------------- Config -------------------
        mode = (cfg.get("section_mode") or "abstract").lower()         # "abstract" | "section" | "full"
        label = (cfg.get("section_label") or "").strip()
        max_pages = int(cfg.get("max_pages", 40))
        abstract_scan_pages = int(cfg.get("abstract_scan_pages", 25))
        char_cap = int(cfg.get("summary_chars", 900))
        use_abstractive = bool(cfg.get("use_abstractive", True))
        cluster_backend = (cfg.get("cluster_backend") or "auto").lower()  # "auto"|"sklearn"|"bertopic"

        # ------------------- Extract + Summarize -------------------
        docs: List[List[str]] = []
        metas: List[dict] = []
        summaries: List[str] = []

        for i, fid in enumerate(file_ids):
            rec = FILES.get(fid)
            if not rec:
                log.warning(f"Missing FILES record for {fid}; skipping")
                continue

            log.info(f"[{i+1}/{total_files}] {rec['new_name']} (file_id={fid})")

            # choose section text first
            text = None
            try:
                if mode == "abstract":
                    text = extract_abstract(rec["path"], max_pages=abstract_scan_pages)
                elif mode == "section" and label:
                    text = extract_section(rec["path"], label, scan_pages=abstract_scan_pages)
                elif mode == "full":
                    text = extract_text(rec["path"], max_pages=max_pages)
            except Exception as e:
                log.exception(f"Section extraction failed: {e}")

            if not text:
                log.warning("No section text found; falling back to full-text extract")
                text = extract_text(rec["path"], max_pages=max_pages)

            if text:
                log.debug(f"Extracted {len(text)} chars")
            else:
                log.error("Empty text; continuing")
                metas.append(rec)
                docs.append([])
                summaries.append("")
                # progress/ETA still update
                done = i + 1
                frac = done / max(1, total_files)
                elapsed = time.time() - start_time
                est_total = (elapsed / frac) if frac > 0 else 0
                eta = max(0, est_total - elapsed)
                j["overall_progress"] = 5 + int(25 * frac)
                j["eta_seconds"] = int(eta)
                j["message"] = f"Processed {done}/{total_files} files (ETA ~{int(eta)}s)"
                await asyncio.sleep(0)
                continue

            toks = normalize(text)
            docs.append(toks)
            metas.append(rec)

            # HF summary (fallback to extractive inside)
            summ = summarize_paper_hf(text, max_chars=char_cap, use_abstractive=use_abstractive) or ""
            summaries.append(summ)
            log.info(f"Summary length={len(summ)} chars")

            # Progress + ETA
            done = i + 1
            frac = done / max(1, total_files)
            elapsed = time.time() - start_time
            est_total = (elapsed / frac) if frac > 0 else 0
            eta = max(0, est_total - elapsed)

            j["overall_progress"] = 5 + int(25 * frac)
            j["eta_seconds"] = int(eta)
            j["message"] = f"Processed {done}/{total_files} files (ETA ~{int(eta)}s)"

            await asyncio.sleep(0)

        # ------------------- Decide backend (auto) -------------------
        usable_docs = [i for i, toks in enumerate(docs) if toks]
        n_docs = len(usable_docs)

        if cluster_backend == "auto":
            selected = "sklearn" if n_docs < 6 else "bertopic"
        else:
            selected = cluster_backend

        log.info(f"Clustering backend selected: {selected} (n_docs={n_docs})")

        # ------------------- Cluster: BERTopic path -------------------
        if selected == "bertopic":
            from .topic_bertopic import build_topics_bertopic  # lazy import

            j.update({
                "stage": "clustering",
                "message": "Clustering documents (BERTopic)",
                "overall_progress": 65,
                "eta_seconds": None
            })
            # Better semantic signal: summaries if available, else tokens
            texts_for_topics = [s if s else " ".join(toks) for s, toks in zip(summaries, docs)]

            bt = build_topics_bertopic(
                texts_for_topics,
                model_name="all-MiniLM-L6-v2",
                min_topic_size=3,
            )
            labels = bt["labels"]
            k = bt["k"]
            topics_info = {ti["topic_id"]: ti for ti in bt["topics_info"]}

            clusters: List[dict] = []
            for t in sorted(set(labels.tolist())):
                idxs = [i for i, lab in enumerate(labels) if lab == t]
                if not idxs:
                    continue

                if t == -1:
                    topic_label = "Outliers"
                    key_terms: List[str] = []
                else:
                    ti = topics_info.get(int(t), {"label": f"Topic {t}", "top_words": []})
                    topic_label = ti["label"]
                    key_terms = ti["top_words"]

                members = []
                for i in idxs:
                    rec = metas[i]
                    members.append({
                        "file_id": next(fid for fid, v in FILES.items() if v["path"] == rec["path"]),
                        "new_name": rec["new_name"],
                        "title": rec["title"],
                        "authors": rec["authors"],
                        "year": rec["year"],
                        "paper_summary": summaries[i],
                        "key_terms": key_terms,
                    })

                clusters.append({
                    "topic_id": int(t),
                    "topic_label": topic_label,
                    "summary": f"{len(members)} papers about {topic_label}",
                    "members": members,
                })

            j["result"] = {
                "clusters": clusters,
                "metrics": {"k": int(k), "method": "bertopic(auto)", "embedding": "sentence-transformers"},
                "logfile": logfile,
            }
            j.update({"stage": "finished", "state": "DONE", "overall_progress": 100, "message": "Done", "eta_seconds": 0})
            log.info(f"BERTopic clustering finished: k={k}")
            return

        # ------------------- Cluster: sklearn path -------------------
        j.update({
            "stage": "topic_model",
            "message": "Building topics",
            "overall_progress": 35,
            "eta_seconds": None
        })
        lda, vectorizer, vecs = build_lda_sklearn(docs, num_topics=cfg.get("num_topics", 8))

        j.update({
            "stage": "clustering",
            "message": "Clustering documents",
            "overall_progress": 65,
            "eta_seconds": None
        })
        labels, k = cluster_docs(vecs, k=cfg.get("cluster_k"))
        log.info(f"Clustering done: k={k}")

        clusters: List[dict] = []
        for c in range(k):
            idxs = [i for i, lab in enumerate(labels) if lab == c]
            if not idxs:
                continue

            centroid = vecs[idxs].mean(axis=0)
            top_topic = int(np.argmax(centroid))
            topic_label = topic_label_sklearn(lda, vectorizer, top_topic)
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
                    "paper_summary": summaries[i],
                    "key_terms": key_terms,
                })

            clusters.append({
                "topic_id": c,
                "topic_label": topic_label,
                "summary": f"{len(members)} papers about {topic_label}",
                "members": members,
            })

        j["result"] = {
            "clusters": clusters,
            "metrics": {"k": int(k), "method": "kmeans-on-lda-sklearn(auto)", "embedding": "sklearn-doc-topic"},
            "logfile": logfile,
        }
        j.update({"stage": "finished", "state": "DONE", "overall_progress": 100, "message": "Done", "eta_seconds": 0})
        log.info(f"sklearn clustering finished: k={k}")

    except Exception as e:
        JOBS[job_id].update({"state": "ERROR", "message": str(e), "eta_seconds": 0})
        log.exception(f"Job failed: {e}")
    finally:
        # Detach/close per-job file handlers
        remove_handler(job_id)
