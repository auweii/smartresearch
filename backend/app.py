from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import logging
import requests
import re
import os
import glob
import tempfile

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

from models.schemas import (
    FullMetadata, UploadResponse, DocMeta,
    SearchRequest, SearchResponse, SearchHit, MetaResponse, TextResponse
)
from utils.storage import (
    save_file, save_text, get_text, list_docs, get_doc,
    delete_doc, save_meta, get_meta, FILES as FILES_DIR
)
from services.extract import pdf_to_text
from services.summarize import textrankish_summary
from services.ocr import ocr_pdf_to_text
from services.metadata import enrich_from_text
from services.metadata_compare import compare_metadata
from services import semantic
from services.cluster import Clusterer

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

logger = logging.getLogger("smartresearch.api")

app = FastAPI(title="SmartResearch API", version="0.6.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_vectorizer = None
_matrix = None
_doc_ids = None
_doc_names = None
_doc_texts = None


def _ensure_tfidf_ready():
    global _vectorizer, _matrix, _doc_ids, _doc_names, _doc_texts
    docs = list_docs()
    if not docs:
        return

    _doc_ids = [d["id"] for d in docs]
    _doc_names = [d["name"] for d in docs]
    _doc_texts = [f"{d['name']} " + get_text(d["id"]) for d in docs]

    _vectorizer = TfidfVectorizer(
        lowercase=True,
        token_pattern=r"(?u)\b[\w\-]{2,}\b",
        ngram_range=(1, 2),
        max_features=30000,
        sublinear_tf=True,
        smooth_idf=True,
        norm="l2",
    )
    _matrix = _vectorizer.fit_transform(_doc_texts)


def _get_recommendations_for_doc(doc_id: str, final_meta: dict, doc_name: str, limit: int = 5) -> list:
    doi = final_meta.get("doi")
    title = final_meta.get("title") or doc_name or ""

    academic_keywords = [
        "study", "analysis", "research", "paper", "experiment",
        "evaluation", "journal", "conference", "dataset", "neural", "algorithm"
    ]
    is_academic = any(re.search(rf"\b{k}\b", title.lower()) for k in academic_keywords)

    if doi:
        try:
            url = f"https://api.semanticscholar.org/recommendations/v1/papers/forpaper/DOI:{doi}"
            params = {"limit": limit, "fields": "title,authors,year,venue,externalIds"}
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json().get("recommendedPapers", [])
                if data:
                    return data
        except Exception:
            pass

    if is_academic and title:
        try:
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {"query": title, "limit": limit, "fields": "title,authors,year,venue,externalIds"}
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json().get("data", [])
                if data:
                    return data
        except Exception:
            pass

    return []


@app.on_event("startup")
def _startup_cache():
    try:
        _ensure_tfidf_ready()
    except Exception as e:
        print(f"tf-idf prebuild failed: {e}")

    # reindex semantic embeddings if index is empty but docs exist
    try:
        semantic.ensure_loaded()
        if semantic._vecs.shape[0] == 0:
            docs = list_docs()
            for d in docs:
                text = get_text(d["id"])
                if text and text.strip():
                    semantic.add_doc(d["id"], text)
    except Exception as e:
        print(f"semantic index prebuild failed: {e}")


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/docs", response_model=List[DocMeta])
def docs_list():
    docs = list_docs()
    enriched = []
    for d in docs:
        meta = get_meta(d["id"]) or {}
        final_meta = meta.get("final") or {}
        summary = final_meta.get("summary") or final_meta.get("abstract")
        enriched.append({**d, "summary": summary})
    return enriched


@app.get("/api/clustered")
def get_clusters():
    semantic.ensure_loaded()

    chunk_ids = list(getattr(semantic, "_ids", []))
    X = getattr(semantic, "_vecs", None)
    lookup = getattr(semantic, "_doc_lookup", {})

    if X is None or len(chunk_ids) == 0 or X.shape[0] == 0:
        return []

    docs = {d["id"]: d for d in list_docs()}

    doc_to_rows = defaultdict(list)
    for i, cid in enumerate(chunk_ids):
        did = lookup.get(cid, cid.split("::")[0])
        if did in docs:
            doc_to_rows[did].append(i)

    doc_ids = [did for did, rows in doc_to_rows.items() if rows]
    if len(doc_ids) == 0:
        return []

    X_doc = np.vstack([X[doc_to_rows[did]].mean(axis=0) for did in doc_ids])

    k = min(5, len(doc_ids))
    if k <= 1:
        did = doc_ids[0]
        text = get_text(did) or ""
        keywords = []

        if text.strip():
            vect = TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-]{2,}\b",
                ngram_range=(1, 2),
                max_features=20000,
            )
            tfidf = vect.fit_transform([text])
            vocab = vect.get_feature_names_out()
            mean = tfidf.mean(axis=0).A1
            top_idx = mean.argsort()[::-1][:8]
            keywords = [vocab[i] for i in top_idx if mean[i] > 0][:8]

        return [{
            "id": "cluster-0",
            "title": " / ".join(keywords[:3]) if keywords else "cluster 0",
            "authors": (get_meta(did) or {}).get("authors") or [],
            "count": 1,
            "description": ("keywords: " + ", ".join(keywords)) if keywords else "no keywords yet",
            "paper_ids": [did],
        }]

    clusterer = Clusterer()
    labels = clusterer.fit(X_doc)

    texts = {did: (get_text(did) or "") for did in doc_ids}

    vect = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-]{2,}\b",
        ngram_range=(1, 2),
        max_features=20000,
    )

    corpus_ids = [did for did in doc_ids if texts.get(did, "").strip()]
    if not corpus_ids:
        return []

    tfidf = vect.fit_transform([texts[did] for did in corpus_ids])
    vocab = vect.get_feature_names_out()
    id_to_row = {did: i for i, did in enumerate(corpus_ids)}

    grouped = defaultdict(list)
    for did, lab in zip(doc_ids, labels):
        if lab == -1:
            grouped["other"].append(did)
        else:
            grouped[lab].append(did)

    clusters_out = []
    for lab, dids in grouped.items():
        if lab == "other":
            continue

        rows = [id_to_row[did] for did in dids if did in id_to_row]
        keywords = []
        if rows:
            mean = tfidf[rows].mean(axis=0).A1
            top_idx = mean.argsort()[::-1][:8]
            keywords = [vocab[i] for i in top_idx if mean[i] > 0][:8]

        title = None
        for did in dids:
            meta = get_meta(did) or {}
            final_meta = meta.get("final") or {}
            title = final_meta.get("title")
            if title:
                break
        title = title or f"cluster {lab}"

        authors = []
        for did in dids:
            meta = get_meta(did) or {}
            final_meta = meta.get("final") or {}
            a = final_meta.get("authors") or []
            if isinstance(a, list):
                authors.extend(a[:2])
        authors = list(dict.fromkeys([x for x in authors if isinstance(x, str)]))[:6]

        clusters_out.append({
            "id": f"cluster-{lab}",
            "title": title,
            "authors": authors,
            "count": len(dids),
            "description": ("keywords: " + ", ".join(keywords)) if keywords else "no keywords yet",
            "paper_ids": dids,
        })

    if grouped.get("other"):
        clusters_out.append({
            "id": "cluster-other",
            "title": "Other",
            "authors": [],
            "count": len(grouped["other"]),
            "description": "Papers that didn't fit neatly into any cluster",
            "paper_ids": grouped["other"],
        })

    clusters_out.sort(key=lambda c: c["count"], reverse=True)
    return clusters_out


@app.get("/api/text/{doc_id}", response_model=TextResponse)
def fetch_text(doc_id: str):
    rec = get_doc(doc_id)
    text = get_text(doc_id)
    return TextResponse(id=doc_id, name=rec["name"], text=text, n_chars=len(text))


@app.get("/api/meta/{doc_id}", response_model=MetaResponse)
def fetch_meta(doc_id: str):
    try:
        _ = get_doc(doc_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found")

    meta = get_meta(doc_id) or {}
    pdf_meta = meta.get("pdf") or {}
    confidence = meta.get("confidence", 1.0)
    reliable = meta.get("reliable", True)
    stored_final = meta.get("final") or {}

    # skip comparison if an AI summary is saved - return stored data as-is
    if stored_final.get("original_summary"):
        external_meta = meta.get("external") or {}
        return MetaResponse(
            id=doc_id,
            meta=FullMetadata(
                pdf=pdf_meta,
                external=external_meta,
                final=stored_final,
                confidence=confidence,
                reliable=reliable,
            )
        )

    doi = pdf_meta.get("doi") or pdf_meta.get("DOI")
    comparison = compare_metadata(pdf_meta, title=pdf_meta.get("title"), doi=doi)
    external_meta = comparison.get("external") or {}
    final_meta = external_meta if comparison["reliable"] and external_meta else pdf_meta

    summary = final_meta.get("summary") or final_meta.get("abstract")
    if not summary:
        try:
            text = get_text(doc_id)
            if text and text.strip():
                summary = textrankish_summary(text, max_sentences=5, doi=doi)
            if not summary:
                summary = get_text(doc_id)[:200]
            final_meta["summary"] = summary
            final_meta["abstract"] = summary
        except Exception as e:
            logger.warning(f"Failed to generate summary for {doc_id}: {e}")

    meta.update({
        "external": external_meta,
        "final": final_meta,
        "confidence": comparison["confidence"],
        "reliable": comparison["reliable"],
    })
    save_meta(doc_id, meta)

    return MetaResponse(
        id=doc_id,
        meta=FullMetadata(
            pdf=pdf_meta,
            external=external_meta,
            final=final_meta,
            confidence=confidence,
            reliable=reliable,
        )
    )


@app.delete("/api/docs/{doc_id}")
def remove_doc(doc_id: str):
    ok = delete_doc(doc_id)
    try:
        semantic.remove_doc(doc_id)
    except Exception:
        pass
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"deleted": doc_id}


@app.post("/api/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF supported")

    raw = await file.read()
    used_ocr = False

    try:
        rec = save_file(file.filename, raw)
        text = pdf_to_text(rec["path"])

        # fall back to OCR if text extraction yields too little content
        if not text or len(text.strip()) < 50 or (len(text.strip()) < 5000 and "abstract" not in text.lower()):
            ocr_text = ocr_pdf_to_text(rec["path"])
            if len(ocr_text.strip()) > len(text.strip()):
                text = ocr_text
                used_ocr = True

        # strip URL lines - noise filtering for summaries handled in summarize.py
        clean_lines = [
            line.strip() for line in text.splitlines()
            if line.strip() and not any(
                p in line.strip().lower()
                for p in ["http://", "https://", "www."]
            )
        ]
        clean_text = "\n".join(clean_lines)

        if len(clean_text.strip()) < 50:
            raise HTTPException(status_code=422, detail="Unable to extract meaningful text from PDF")

        pdf_meta = enrich_from_text(clean_text, rec["path"]) or {}
        doi = pdf_meta.get("doi")
        summary = textrankish_summary(clean_text, max_sentences=5, doi=doi)

        meta_payload = {
            "pdf": pdf_meta,
            "external": {},
            "final": {
                **pdf_meta,
                "summary": summary,
                "abstract": summary,
            },
            "confidence": 1.0,
            "reliable": True,
        }

        save_meta(rec["id"], meta_payload)
        save_text(rec["id"], clean_text)

        try:
            _ensure_tfidf_ready()
        except Exception as e:
            logger.warning(f"TF-IDF cache build failed after upload {rec['id']}: {e}")

        try:
            semantic.add_doc(rec["id"], clean_text)
        except Exception as e:
            logger.warning(f"Semantic index update failed for {rec['id']}: {e}")

        preview = clean_text[:600] + ("..." if len(clean_text) > 600 else "")

        return UploadResponse(
            doc=DocMeta(id=rec["id"], name=rec["name"], n_chars=len(clean_text)),
            preview=preview,
            used_ocr=used_ocr,
            meta=FullMetadata(**meta_payload),
        )

    except Exception as e:
        logger.error(f"Upload failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/move_to_storage")
def move_to_storage():
    try:
        docs = list_docs()
        if not docs:
            return {"status": "no files to move"}
        moved_docs = [doc["name"] for doc in docs]
        return {"status": "ok", "moved_count": len(moved_docs), "docs": moved_docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search", response_model=SearchResponse)
async def keyword_search(req: SearchRequest):
    global _vectorizer, _matrix, _doc_ids, _doc_names, _doc_texts
    if _matrix is None or _vectorizer is None:
        _ensure_tfidf_ready()
    if _matrix is None:
        return SearchResponse(hits=[])

    q = req.q.strip()
    if not q:
        return SearchResponse(hits=[])

    qv = _vectorizer.transform([q])
    sims = cosine_similarity(qv, _matrix)[0]
    sims = sims / (sims.max() or 1.0)
    order = sims.argsort()[::-1][:req.topk]

    hits = []
    for i in order:
        score = float(sims[i])
        if score < 0.05:
            continue
        txt = _doc_texts[i]
        prev = txt[:220].replace("\n", " ") + ("..." if len(txt) > 220 else "")
        hits.append(SearchHit(id=_doc_ids[i], name=_doc_names[i], score=score, preview=prev))
    return SearchResponse(hits=hits)


@app.post("/api/semantic_search", response_model=SearchResponse)
async def semantic_search(req: SearchRequest):
    docs = {d["id"]: d for d in list_docs()}
    matches = semantic.search(req.q, topk=req.topk)
    hits = []
    for did, score in matches:
        if did not in docs:
            continue
        name = docs[did]["name"]
        txt = get_text(did)
        prev = txt[:220].replace("\n", " ") + ("..." if len(txt) > 220 else "")
        hits.append(SearchHit(id=did, name=name, score=float(score), preview=prev))
    return SearchResponse(hits=hits)


@app.post("/api/hybrid_search", response_model=SearchResponse)
async def hybrid_search(req: SearchRequest):
    global _vectorizer, _matrix, _doc_ids, _doc_names, _doc_texts
    if _matrix is None or _vectorizer is None:
        _ensure_tfidf_ready()
    if _matrix is None:
        return SearchResponse(hits=[])

    q = req.q.strip()
    topk = req.topk or 10
    if not q:
        return SearchResponse(hits=[])

    qv = _vectorizer.transform([q])
    kw_sims = cosine_similarity(qv, _matrix)[0]
    kw_sims = kw_sims / (kw_sims.max() or 1.0)
    kw_hits = {_doc_ids[i]: float(kw_sims[i]) for i in range(len(_doc_ids))}

    semantic.ensure_loaded()
    sem_hits = semantic.search(q, topk=topk * 2)
    sem_dict = {doc_id: score for doc_id, score in sem_hits}

    # weighted combination: 70% semantic, 30% keyword
    alpha = 0.7
    results = {}
    for doc_id in set(kw_hits.keys()).union(sem_dict.keys()):
        s_score = sem_dict.get(doc_id, 0.0)
        k_score = kw_hits.get(doc_id, 0.0)
        results[doc_id] = alpha * s_score + (1 - alpha) * k_score

    sorted_hits = sorted(results.items(), key=lambda x: -x[1])[:topk]
    hits = []
    for doc_id, score in sorted_hits:
        try:
            rec = get_doc(doc_id)
            text = get_text(doc_id)
            preview = text[:220].replace("\n", " ") + ("..." if len(text) > 220 else "")
            hits.append(SearchHit(id=doc_id, name=rec["name"], score=float(score), preview=preview))
        except Exception:
            continue
    return SearchResponse(hits=hits)


@app.get("/api/similar/{doc_id}", response_model=SearchResponse)
async def similar_docs(doc_id: str, topk: int = 10):
    semantic.ensure_loaded()

    docs = {d["id"]: d for d in list_docs()}
    matches = semantic.similar(doc_id, topk=topk * 2)

    hits = []
    for did, score in matches:
        if did == doc_id or score < 0.35 or did not in docs:
            continue

        txt = get_text(did) or ""
        prev = txt[:220].replace("\n", " ") + ("..." if len(txt) > 220 else "")
        other_meta = get_meta(did) or {}

        hits.append(
            SearchHit(
                id=did,
                name=docs[did]["name"],
                score=float(score),
                preview=prev,
                meta=FullMetadata(**other_meta) if other_meta else None,
            )
        )

    hits = sorted(hits, key=lambda x: -x.score)[:topk]
    return SearchResponse(hits=hits)


@app.get("/api/external_recs/{doc_id}")
def external_recommendations(doc_id: str):
    try:
        rec = get_doc(doc_id)
        meta = get_meta(doc_id) or {}
        final_meta = meta.get("final") or {}

        recs = _get_recommendations_for_doc(doc_id, final_meta, rec.get("name", ""))

        if recs:
            return {
                "source": "semantic_scholar",
                "recommendations": [
                    {
                        "title": d.get("title"),
                        "authors": [a.get("name") for a in d.get("authors", [])],
                        "year": d.get("year"),
                        "venue": d.get("venue"),
                        "doi": (d.get("externalIds") or {}).get("DOI", ""),
                    }
                    for d in recs
                ],
            }

        # local fallback using semantic similarity
        semantic.ensure_loaded()
        matches = semantic.similar(doc_id, topk=5)
        docs = {d["id"]: d for d in list_docs()}
        local_recs = []

        for did, score in matches:
            if did == doc_id or did not in docs:
                continue
            other = docs[did]
            other_meta = get_meta(did) or {}
            other_final = other_meta.get("final") or {}
            local_recs.append({
                "title": other_final.get("title") or other["name"],
                "authors": other_final.get("authors") or [],
                "year": other_final.get("year"),
                "venue": other_final.get("venue"),
                "score": float(score),
            })

        if local_recs:
            return {"source": "local", "recommendations": local_recs}

        raise HTTPException(status_code=404, detail="No recommendations found.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reindex")
def reindex():
    docs = list_docs()
    if not docs:
        return {"status": "ok", "reindexed": 0}

    semantic._ids.clear()
    semantic._vecs = np.zeros(
        (0, semantic._model.get_sentence_embedding_dimension()), dtype="float32"
    )

    reindexed = 0
    for d in docs:
        try:
            text = get_text(d["id"])
            if text.strip():
                semantic.add_doc(d["id"], text)
                reindexed += 1
        except Exception as e:
            logger.warning(f"Failed to reindex doc {d['id']}: {e}")
            continue
    return {"status": "ok", "reindexed": reindexed}


@app.get("/files/{file_id}.pdf")
def get_pdf(file_id: str):
    base_dir = str(Path(FILES_DIR))
    pattern = os.path.join(base_dir, f"{file_id}*.pdf")
    matches = glob.glob(pattern)
    if not matches:
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(matches[0], media_type="application/pdf")


@app.get("/api/system/gpu")
def gpu_status():
    import torch
    available = torch.cuda.is_available()
    return {
        "gpu_available": available,
        "device": torch.cuda.get_device_name(0) if available else "CPU",
    }


@app.post("/api/summarize/{doc_id}")
async def deep_summarize(doc_id: str, target: str = "medium"):
    try:
        _ = get_doc(doc_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found")

    text = get_text(doc_id)
    if not text or not text.strip():
        raise HTTPException(status_code=422, detail="No text available for this document")

    try:
        from services.abstractive import abstractive_summarize
        summary, n_chunks = abstractive_summarize(text, target=target)
        return {"doc_id": doc_id, "summary": summary, "chunks": n_chunks, "target": target}
    except Exception as e:
        logger.error(f"Abstractive summarization failed for {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/meta/{doc_id}/summary")
def update_summary(doc_id: str, payload: dict = Body(default={})):
    try:
        _ = get_doc(doc_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found")

    new_summary = payload.get("summary", "").strip()
    if not new_summary:
        raise HTTPException(status_code=400, detail="Summary cannot be empty")

    meta = get_meta(doc_id) or {}
    final_meta = meta.get("final") or {}

    # preserve original extractive summary before overwriting
    if not final_meta.get("original_summary"):
        final_meta["original_summary"] = final_meta.get("summary") or final_meta.get("abstract") or ""

    final_meta["summary"] = new_summary
    final_meta["abstract"] = new_summary
    meta["final"] = final_meta
    save_meta(doc_id, meta)
    return {"ok": True}


@app.patch("/api/meta/{doc_id}/recover_summary")
def recover_summary(doc_id: str):
    try:
        _ = get_doc(doc_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found")

    meta = get_meta(doc_id) or {}
    final_meta = meta.get("final") or {}
    original = final_meta.get("original_summary", "")

    if not original:
        # regenerate extractive summary if no original was saved
        text = get_text(doc_id)
        if not text or not text.strip():
            raise HTTPException(status_code=404, detail="No original summary found")
        doi = final_meta.get("doi")
        original = textrankish_summary(text, max_sentences=5, doi=doi)

    final_meta["summary"] = original
    final_meta["abstract"] = original
    final_meta.pop("original_summary", None)
    meta["final"] = final_meta
    save_meta(doc_id, meta)
    return {"ok": True}


@app.post("/api/export")
def export_report(payload: dict = Body(default={})):
    fmt = (payload.get("format") or "pdf").lower()
    if fmt != "pdf":
        raise HTTPException(status_code=400, detail="only pdf export is implemented")

    include_all = bool(payload.get("include", {}).get("all_papers", True))
    include_clusters_list = bool(payload.get("include", {}).get("clusters_list", True))
    include_papers_by_cluster = bool(payload.get("include", {}).get("papers_by_cluster", True))
    include_summaries = bool(payload.get("extras", {}).get("summaries", True))
    include_keywords = bool(payload.get("extras", {}).get("keywords", True))
    include_charts = bool(payload.get("extras", {}).get("charts", True))
    include_recommendations = bool(payload.get("extras", {}).get("recommendations", False))

    docs = list_docs() or []
    try:
        clusters = get_clusters() or []
    except Exception as e:
        logger.warning(f"Failed to fetch clusters for export: {e}")
        clusters = []

    tmpdir = tempfile.mkdtemp()
    out_path = os.path.join(
        tmpdir,
        f"smartresearch_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

    styles = getSampleStyleSheet()

    meta_style = ParagraphStyle(
        "MetaStyle", parent=styles["Normal"],
        fontSize=8, textColor=colors.grey, spaceAfter=2,
    )
    label_style = ParagraphStyle(
        "LabelStyle", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#8B5E3C"),
        fontName="Helvetica-Bold", spaceAfter=2,
    )
    missing_style = ParagraphStyle(
        "MissingStyle", parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#999999"),
        fontName="Helvetica-Oblique",
    )
    ai_badge_style = ParagraphStyle(
        "AIBadge", parent=styles["Normal"],
        fontSize=7, textColor=colors.HexColor("#065f46"),
        fontName="Helvetica-Bold",
    )

    story = []

    # cover page
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("SmartResearch", styles["Title"]))
    story.append(Paragraph("Research Export Report", styles["Heading2"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", styles["Normal"]))
    story.append(Paragraph(f"Total Papers: {len(docs)}", styles["Normal"]))
    story.append(Paragraph(f"Total Clusters: {len([c for c in clusters if c.get('id') != 'cluster-other'])}", styles["Normal"]))
    story.append(PageBreak())

    # analytics charts — cluster distribution and keywords only
    if include_charts and docs:
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics.charts.barcharts import HorizontalBarChart
        from reportlab.graphics.charts.piecharts import Pie

        story.append(Paragraph("Analytics", styles["Heading1"]))
        story.append(Spacer(1, 0.2 * inch))

        # cluster distribution pie chart
        cluster_data = [
            (c.get("title") or c.get("id"), c.get("count", 0))
            for c in clusters if c.get("count", 0) > 0
        ]
        if cluster_data:
            story.append(Paragraph("Cluster Distribution", styles["Heading2"]))
            story.append(Spacer(1, 0.1 * inch))

            pie_colors = [
                colors.HexColor("#8B5E3C"), colors.HexColor("#b07d56"),
                colors.HexColor("#d4a574"), colors.HexColor("#e8c9a0"),
                colors.HexColor("#6b4423"), colors.HexColor("#4a2e18"),
                colors.HexColor("#c9956b"),
            ]

            d = Drawing(400, 200)
            pie = Pie()
            pie.x = 100
            pie.y = 20
            pie.width = 150
            pie.height = 150
            pie.data = [c for _, c in cluster_data]
            pie.labels = [t[:20] for t, _ in cluster_data]
            pie.sideLabels = True
            pie.slices.strokeWidth = 0.5
            for i in range(len(cluster_data)):
                pie.slices[i].fillColor = pie_colors[i % len(pie_colors)]
            d.add(pie)
            story.append(d)
            story.append(Spacer(1, 0.3 * inch))

        # top keywords across all papers using TF-IDF
        if include_keywords:
            story.append(Paragraph("Top Keywords Across All Papers", styles["Heading2"]))
            story.append(Spacer(1, 0.1 * inch))

            all_text = " ".join(get_text(d["id"]) or "" for d in docs)
            if all_text.strip():
                from sklearn.feature_extraction.text import TfidfVectorizer as TV
                vect = TV(
                    lowercase=True,
                    stop_words="english",
                    token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-]{3,}\b",
                    ngram_range=(1, 1),
                    max_features=15,
                )
                tfidf = vect.fit_transform([all_text])
                vocab = vect.get_feature_names_out()
                scores = tfidf.toarray()[0]
                pairs = sorted(zip(vocab, scores), key=lambda x: -x[1])[:15]
                kw_labels = [k for k, _ in pairs]
                kw_values = [float(v) for _, v in pairs]

                d = Drawing(450, 250)
                hbc = HorizontalBarChart()
                hbc.x = 130
                hbc.y = 10
                hbc.width = 280
                hbc.height = 230
                hbc.data = [kw_values]
                hbc.categoryAxis.categoryNames = kw_labels
                hbc.categoryAxis.labels.fontSize = 7
                hbc.categoryAxis.labels.dx = -5
                hbc.valueAxis.valueMin = 0
                hbc.valueAxis.valueMax = max(kw_values) * 1.1
                hbc.bars[0].fillColor = colors.HexColor("#8B5E3C")
                d.add(hbc)
                story.append(d)
            else:
                story.append(Paragraph("No text data available.", missing_style))

        story.append(PageBreak())

    # clusters overview
    if include_clusters_list and clusters:
        story.append(Paragraph("Clusters Overview", styles["Heading1"]))
        story.append(Spacer(1, 0.15 * inch))

        for c in clusters:
            cluster_title = c.get("title") or c.get("id") or "Untitled"
            desc = c.get("description", "")
            m = re.match(r"^keywords:\s*(.+)$", desc, re.IGNORECASE)
            kw_text = m.group(1) if m else "not available"
            count = str(c.get("count") or 0)

            story.append(Paragraph(cluster_title, styles["Heading2"]))
            story.append(Paragraph(f"Papers: {count}", label_style))
            story.append(Paragraph(f"Keywords: {kw_text}", label_style))
            story.append(Spacer(1, 0.2 * inch))

        story.append(PageBreak())

    # papers grouped by cluster
    if include_papers_by_cluster and clusters:
        story.append(Paragraph("Papers by Cluster", styles["Heading1"]))
        story.append(Spacer(1, 0.15 * inch))

        doc_map = {d["id"]: d for d in docs}

        for c in clusters:
            cluster_title = c.get("title") or c.get("id") or "Cluster"
            story.append(Paragraph(cluster_title, styles["Heading2"]))

            if include_keywords:
                desc = c.get("description", "")
                m = re.match(r"^keywords:\s*(.+)$", desc, re.IGNORECASE)
                if m:
                    story.append(Paragraph(f"Keywords: {m.group(1)}", label_style))
                else:
                    story.append(Paragraph("Keywords: not available", missing_style))

            paper_ids = c.get("paper_ids") or []
            story.append(Paragraph(f"{len(paper_ids)} paper(s) in this cluster", meta_style))
            story.append(Spacer(1, 0.1 * inch))

            for did in paper_ids:
                rec = doc_map.get(did) or {"name": did}
                meta = get_meta(did) or {}
                final_meta = meta.get("final") or {}

                paper_title = final_meta.get("title") or rec.get("name") or "Untitled"
                story.append(Paragraph(f"• {paper_title}", styles["Normal"]))

                if include_summaries:
                    summary = final_meta.get("summary") or final_meta.get("abstract")
                    is_ai = bool(final_meta.get("original_summary"))
                    if summary:
                        if is_ai:
                            story.append(Paragraph("AI-generated summary", ai_badge_style))
                        story.append(Paragraph(f"<i>{summary[:1200]}</i>", styles["BodyText"]))
                    else:
                        story.append(Paragraph("Summary: not available", missing_style))

                story.append(Spacer(1, 0.1 * inch))

            story.append(Spacer(1, 0.2 * inch))

        story.append(PageBreak())

    # all papers with full metadata
    if include_all:
        story.append(Paragraph("All Papers", styles["Heading1"]))
        story.append(Spacer(1, 0.15 * inch))

        for d in docs:
            did = d["id"]
            meta = get_meta(did) or {}
            final_meta = meta.get("final") or {}

            paper_title = final_meta.get("title") or d.get("name") or "Untitled"
            story.append(Paragraph(paper_title, styles["Heading2"]))

            authors = final_meta.get("authors")
            if authors and isinstance(authors, list) and any(authors):
                story.append(Paragraph(f"Authors: {', '.join(str(a) for a in authors if a)}", label_style))
            else:
                story.append(Paragraph("Authors: not found", missing_style))

            year = final_meta.get("year")
            story.append(Paragraph(f"Year: {year}", label_style) if year else Paragraph("Year: not found", missing_style))

            venue = final_meta.get("venue") or final_meta.get("publisher")
            story.append(Paragraph(f"Venue: {venue}", label_style) if venue else Paragraph("Venue: not found", missing_style))

            doi = final_meta.get("doi")
            story.append(Paragraph(f"DOI: {doi}", label_style) if doi else Paragraph("DOI: not found", missing_style))

            if include_summaries:
                summary = final_meta.get("summary") or final_meta.get("abstract")
                is_ai = bool(final_meta.get("original_summary"))
                story.append(Spacer(1, 0.08 * inch))
                if summary:
                    if is_ai:
                        story.append(Paragraph("AI-generated summary", ai_badge_style))
                    story.append(Paragraph(summary[:2400], styles["BodyText"]))
                else:
                    story.append(Paragraph("Summary: not available", missing_style))

            # recommended papers via Semantic Scholar
            if include_recommendations:
                story.append(Spacer(1, 0.08 * inch))
                story.append(Paragraph("Recommended Papers", label_style))
                try:
                    recs = _get_recommendations_for_doc(did, final_meta, d.get("name", ""))
                    if recs:
                        for rec in recs:
                            rec_title = rec.get("title") or "Untitled"
                            rec_authors = ", ".join(a.get("name", "") for a in rec.get("authors", [])[:3])
                            rec_year = str(rec.get("year") or "")
                            rec_doi = (rec.get("externalIds") or {}).get("DOI", "")
                            rec_venue = rec.get("venue") or ""
                            rec_line = f"• {rec_title}"
                            if rec_authors:
                                rec_line += f" — {rec_authors}"
                            if rec_year:
                                rec_line += f" ({rec_year})"
                            story.append(Paragraph(rec_line, styles["Normal"]))
                            if rec_venue:
                                story.append(Paragraph(f"  Venue: {rec_venue}", meta_style))
                            if rec_doi:
                                story.append(Paragraph(f"  DOI: {rec_doi}", meta_style))
                            story.append(Spacer(1, 0.05 * inch))
                    else:
                        story.append(Paragraph("No recommendations available.", missing_style))
                except Exception:
                    story.append(Paragraph("No recommendations available.", missing_style))

            story.append(Spacer(1, 0.25 * inch))

    doc = SimpleDocTemplate(
        out_path,
        pagesize=LETTER,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    doc.build(story)

    return FileResponse(
        out_path,
        media_type="application/pdf",
        filename=os.path.basename(out_path),
    )
  