import asyncio, uuid, time
from typing import Dict, Any, List
import numpy as np

from .storage import FILES, JOBS
from .pdf_sections import extract_abstract, extract_section
from .pdf_text import extract_text
from .nlp_pipeline import (
    normalize, build_lda_sklearn, cluster_docs, topic_label_sklearn, summarize_paper_hf,
)
from ..libs.logger import job_logger, remove_handler  # NEW

async def start_job(payload: Dict[str, Any]) -> str:
    job_id = f"job_{uuid.uuid4().hex[:6]}"
    JOBS[job_id] = {
        "state": "QUEUED", "stage": "queued", "overall_progress": 0,
        "files": [{"file_id": fid, "progress": 0, "stage": "queued"} for fid in payload.get("file_ids", [])],
        "message": "Queued", "eta_seconds": None, "result": None,
        # we’ll fill 'logfile' in run_job when we create the handler
    }
    asyncio.create_task(run_job(job_id, payload))
    return job_id

async def run_job(job_id: str, cfg: Dict[str, Any]):
    log, h, logfile = job_logger(job_id)   # NEW: per-job file handler
    JOBS[job_id]["logfile"] = logfile      # expose path in status/result
    try:
        file_ids: List[str] = cfg.get("file_ids", [])
        total_files = len(file_ids)
        start_time = time.time()

        log.info(f"Starting job with {total_files} files")
        log.debug(f"payload={cfg}")

        j = JOBS[job_id]
        j.update({"state":"PROCESSING","stage":"extracting","overall_progress":5,"message":"Reading PDFs","eta_seconds":None})

        docs, metas, summaries = [], [], []

        mode = (cfg.get("section_mode") or "abstract").lower()
        label = (cfg.get("section_label") or "").strip()
        max_pages = int(cfg.get("max_pages", 40))
        abstract_scan_pages = int(cfg.get("abstract_scan_pages", 25))
        char_cap = int(cfg.get("summary_chars", 900))
        use_abstractive = bool(cfg.get("use_abstractive", True))

        for i, fid in enumerate(file_ids):
            rec = FILES.get(fid)
            if not rec:
                log.warning(f"Missing FILES record for {fid}; skipping")
                continue

            log.info(f"[{i+1}/{total_files}] {rec['new_name']} (file_id={fid})")
            text = None
            try:
                if mode == "abstract":
                    text = extract_abstract(rec["path"], max_pages=abstract_scan_pages)
                elif mode == "section" and label:
                    text = extract_section(rec["path"], label, scan_pages=abstract_scan_pages)
            except Exception as e:
                log.exception(f"Section extraction failed: {e}")

            if not text:
                log.warning("No section text found; falling back to full-text extract")
                text = extract_text(rec["path"], max_pages=max_pages)

            if text:
                log.debug(f"Extracted {len(text)} chars")
            else:
                log.error("Empty text; continuing")
                metas.append(rec); docs.append([]); summaries.append("")
                continue

            toks = normalize(text)
            docs.append(toks); metas.append(rec)

            summ = summarize_paper_hf(text, max_chars=char_cap, use_abstractive=use_abstractive) or ""
            summaries.append(summ)
            log.info(f"Summary length={len(summ)} chars")

            # progress + eta
            done = i + 1
            frac = done / max(1, total_files)
            elapsed = time.time() - start_time
            est_total = (elapsed / frac) if frac > 0 else 0
            eta = max(0, est_total - elapsed)

            j["overall_progress"] = 5 + int(25 * frac)
            j["eta_seconds"] = int(eta)
            j["message"] = f"Processed {done}/{total_files} files (ETA ~{int(eta)}s)"

            await asyncio.sleep(0)

        log.info("Building topic model (sklearn LDA)")
        j.update({"stage":"topic_model","message":"Building topics","overall_progress":35,"eta_seconds":None})
        lda, vectorizer, vecs = build_lda_sklearn(docs, num_topics=cfg.get("num_topics", 8))

        log.info("Clustering documents")
        j.update({"stage":"clustering","message":"Clustering documents","overall_progress":65,"eta_seconds":None})
        labels, k = cluster_docs(vecs, k=cfg.get("cluster_k"))
        log.info(f"Clustering done: k={k}")

        clusters: list[dict] = []
        for c in range(k):
            idxs = [i for i, lab in enumerate(labels) if lab == c]
            if not idxs: continue

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
                    "paper_summary": summaries[i],
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
            "logfile": logfile,
        }

        j.update({"stage":"finished","state":"DONE","overall_progress":100,"message":"Done","eta_seconds":0})
        log.info("Job finished successfully")

    except Exception as e:
        JOBS[job_id].update({"state":"ERROR","message":str(e),"eta_seconds":0})
        log.exception(f"Job failed: {e}")
    finally:
        # IMPORTANT: detach file handler
        remove_handler(log, h)
