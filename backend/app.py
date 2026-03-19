from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import logging
import requests
import re
import os
import glob
from pathlib import Path

from models.schemas import (
    FullMetadata, UploadResponse, DocMeta, SummarizeRequest, SummarizeResponse,
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
from services.metadata_compare import compare_metadata  # <-- new imports
from services import semantic
from services.cluster import Clusterer 
from services.pdf_processing import process_pdf

logger = logging.getLogger("smartresearch.api")

# app setup
app = FastAPI(title="SmartResearch API", version="0.6.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# cached tf-idf vectors
_vectorizer = None
_matrix = None
_doc_ids = None
_doc_names = None
_doc_texts = None


def _ensure_tfidf_ready():
    """build or rebuild tf-idf vectors from current stored docs"""
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


@app.on_event("startup")
def _startup_cache():
    """warm tf-idf cache so first query isn’t slow"""
    try:
        _ensure_tfidf_ready()
    except Exception as e:
        print(f" tf-idf prebuild failed: {e}")


# base endpoints
@app.get("/api/health")
def health():
    """health check"""
    return {"ok": True}


@app.get("/api/docs", response_model=List[DocMeta])
def docs_list():
    """return all indexed docs with minimal metadata and summary from final metadata"""
    docs = list_docs()
    enriched = []
    for d in docs:
        meta = get_meta(d["id"]) or {}
        final_meta = meta.get("final") or {}
        summary = final_meta.get("summary") or final_meta.get("abstract")
        enriched.append({
            **d,
            "summary": summary
        })
    return enriched


from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

@app.get("/api/clustered")
def get_clusters():
    semantic.ensure_loaded()

    chunk_ids = list(getattr(semantic, "_ids", []))
    X = getattr(semantic, "_vecs", None)
    lookup = getattr(semantic, "_doc_lookup", {})  # chunk_id -> doc_id

    if X is None or len(chunk_ids) == 0 or X.shape[0] == 0:
        return []

    # docs that exist in your store
    docs = {d["id"]: d for d in list_docs()}

    # group chunk row indices by doc_id
    doc_to_rows = defaultdict(list)
    for i, cid in enumerate(chunk_ids):
        did = lookup.get(cid, cid.split("::")[0])
        if did in docs:
            doc_to_rows[did].append(i)

    doc_ids = [did for did, rows in doc_to_rows.items() if rows]
    if len(doc_ids) == 0:
        return []

    # doc-level vectors = mean of that doc's chunk vectors
    X_doc = np.vstack([X[doc_to_rows[did]].mean(axis=0) for did in doc_ids])

    # kmeans can't have more clusters than docs
    target_k = 5
    k = min(target_k, len(doc_ids))
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

    clusterer = Clusterer(k=k)
    labels = clusterer.fit(X_doc)

    # pull doc texts for tf-idf
    texts = {did: (get_text(did) or "") for did in doc_ids}

    # tf-idf across all docs (doc-level)
    vect = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-]{2,}\b",
        ngram_range=(1, 2),
        max_features=20000,
    )
    corpus_ids = [did for did in doc_ids if texts.get(did, "").strip()]
    if not corpus_ids:
        # no text loaded somehow; still return grouping
        grouped = defaultdict(list)
        for did, lab in zip(doc_ids, labels):
            grouped[lab].append(did)

        out = []
        for lab, dids in grouped.items():
            out.append({
                "id": f"cluster-{lab}",
                "title": f"cluster {lab}",
                "authors": [],
                "count": len(dids),
                "description": "no keywords yet",
                "paper_ids": dids,
            })
        out.sort(key=lambda c: c["count"], reverse=True)
        return out

    tfidf = vect.fit_transform([texts[did] for did in corpus_ids])
    vocab = vect.get_feature_names_out()
    id_to_row = {did: i for i, did in enumerate(corpus_ids)}

    # group docs by label
    grouped = defaultdict(list)
    for did, lab in zip(doc_ids, labels):
        grouped[lab].append(did)

    clusters_out = []
    for lab, dids in grouped.items():
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

    clusters_out.sort(key=lambda c: c["count"], reverse=True)
    return clusters_out


@app.get("/api/text/{doc_id}", response_model=TextResponse)
def fetch_text(doc_id: str):
    """return full text for a given doc"""
    rec = get_doc(doc_id)
    text = get_text(doc_id)
    return TextResponse(id=doc_id, name=rec["name"], text=text, n_chars=len(text))


@app.get("/api/meta/{doc_id}", response_model=MetaResponse)
def fetch_meta(doc_id: str):
    """Retrieve and refresh metadata safely with PDF + external comparison"""

    # ensure doc exists
    try:
        _ = get_doc(doc_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found")

    meta = get_meta(doc_id) or {}

    pdf_meta = meta.get("pdf") or {}
    external_meta = meta.get("external") or {}
    final_meta = meta.get("final") or pdf_meta
    confidence = meta.get("confidence", 1.0)
    reliable = meta.get("reliable", True)


    # DOI from PDF metadata
    doi = pdf_meta.get("doi") or pdf_meta.get("DOI")

    # fetch external metadata if DOI exists
    if doi:
        try:
            res = requests.get(
                f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}",
                params={"fields": "title,abstract,venue,year,authors,citationCount"},
                timeout=10,
            )
            res.raise_for_status()
            data = res.json()

            external_meta = {
                "title": data.get("title"),
                "authors": [a["name"] for a in data.get("authors", [])],
                "year": data.get("year"),
                "venue": data.get("venue"),
                "abstract": data.get("abstract"),
                "citationCount": data.get("citationCount"),
                "doi": doi,
                "source": "semantic_scholar",
            }

            comparison = compare_metadata(pdf_meta, external_meta)
            final_meta = external_meta if comparison["reliable"] else pdf_meta

            meta.update({
                "external": external_meta,
                "final": final_meta,
                "confidence": comparison["confidence"],
                "reliable": comparison["reliable"],
            })
            save_meta(doc_id, meta)

        except requests.RequestException as e:
            logger.warning(f"Semantic Scholar API request failed for DOI {doi}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error fetching external metadata for {doc_id}: {e}")

    # ensure summary always exists
    try:
        summary = final_meta.get("summary") if isinstance(final_meta, dict) else None
        if not summary:
            summary = (
                final_meta.get("abstract") if isinstance(final_meta, dict) else None
            ) or textrankish_summary(get_text(doc_id))
            if isinstance(meta, dict):
                final_meta["summary"] = summary
                meta["final"] = final_meta
                save_meta(doc_id, meta)
    except Exception as e:
        logger.warning(f"Failed to generate summary for {doc_id}: {e}")

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
    """delete doc + associated semantic embeddings"""
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
    """handle PDF upload, OCR fallback, metadata enrichment, and indexing"""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF supported")

    # save uploaded file
    raw = await file.read()
    rec = save_file(file.filename, raw)

    # extract text from PDF
    text = pdf_to_text(rec["path"])
    
    print(f"\n===== PDF UPLOAD DEBUG: {file.filename} =====")
    print(text[:1000])  # print first 1000 characters
    print("==========================================\n")

    # fallback OCR if text is very short
    used_ocr = False
    if len(text.strip()) < 200:
        try:
            ocr_text = ocr_pdf_to_text(rec["path"])
            if len(ocr_text.strip()) > len(text.strip()):
                text = ocr_text
                used_ocr = True
        except Exception as e:
            logger.warning(f"OCR failed for {file.filename}: {e}")


    # save the extracted text
    save_text(rec["id"], text)

    # add to semantic embeddings
    try:
        semantic.add_doc(rec["id"], text)
    except Exception as e:
        logger.warning(f"Failed to add semantic embedding for {rec['id']}: {e}")

    # --- Step 2: store BOTH metadata sources ---
    pdf_meta = enrich_from_text(text) or {}

    summary = textrankish_summary(text, max_sentences=5)

    meta_payload = {
        "pdf": pdf_meta,            # metadata extracted from PDF
        "external": {},             # no external metadata yet
        "final": {**pdf_meta,       # copy PDF meta as base
                "summary": summary,
                "abstract": summary},  # optional: reuse summary for abstract
        "confidence": 1.0,          # full confidence in PDF source for now
        "reliable": True,           # assume reliable until compared
    }

    save_meta(rec["id"], meta_payload)
    # --- end Step 2 ---

   # prepare a preview
    preview = (text[:600] + "…") if len(text) > 600 else text
    try:
        _ensure_tfidf_ready()
    except Exception as e:
        logger.warning(f"TF-IDF cache build failed after upload {rec['id']}: {e}")

    return UploadResponse(
        doc=DocMeta(id=rec["id"], name=rec["name"], n_chars=len(text)),
        preview=preview,
        used_ocr=used_ocr,
        meta=FullMetadata(**meta_payload)
    )

@app.post("/api/move_to_storage")
def move_to_storage():
    """mock file mover for long-term storage"""
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
    """basic tf-idf keyword search"""
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
        if score < 0.02:
            continue
        txt = _doc_texts[i]
        prev = txt[:220].replace("\n", " ") + ("…" if len(txt) > 220 else "")
        hits.append(SearchHit(id=_doc_ids[i], name=_doc_names[i], score=score, preview=prev))
    return SearchResponse(hits=hits)


@app.post("/api/semantic_search", response_model=SearchResponse)
async def semantic_search(req: SearchRequest):
    """semantic embedding search (SPECTER2 model)"""
    docs = {d["id"]: d for d in list_docs()}
    matches = semantic.search(req.q, topk=req.topk)
    hits = []
    for did, score in matches:
        if did not in docs:
            continue
        name = docs[did]["name"]
        txt = get_text(did)
        prev = txt[:220].replace("\n", " ") + ("…" if len(txt) > 220 else "")
        hits.append(SearchHit(id=did, name=name, score=float(score), preview=prev))
    return SearchResponse(hits=hits)


@app.post("/api/hybrid_search", response_model=SearchResponse)
async def hybrid_search(req: SearchRequest):
    """combine tf-idf + semantic search with weighted fusion"""
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

    alpha = 0.8
    results = {}
    for doc_id in set(kw_hits.keys()).union(sem_dict.keys()):
        s_score = sem_dict.get(doc_id, 0.0)
        k_score = min(kw_hits.get(doc_id, 0.0), 0.75)
        results[doc_id] = alpha * s_score + (1 - alpha) * k_score

    sorted_hits = sorted(results.items(), key=lambda x: -x[1])[:topk]
    hits = []
    for doc_id, score in sorted_hits:
        try:
            rec = get_doc(doc_id)
            name = rec["name"]
            text = get_text(doc_id)
            preview = text[:220].replace("\n", " ") + ("…" if len(text) > 220 else "")
            hits.append(SearchHit(id=doc_id, name=name, score=float(score), preview=preview))
        except Exception:
            continue
    return SearchResponse(hits=hits)


@app.get("/api/similar/{doc_id}", response_model=SearchResponse)
async def similar_docs(doc_id: str, topk: int = 10):
    """find locally similar docs using semantic embeddings"""
    semantic.ensure_loaded()
    docs = {d["id"]: d for d in list_docs()}
    matches = semantic.similar(doc_id, topk=topk * 2)

    hits = []
    for did, score in matches:
        if did == doc_id or score < 0.35 or did not in docs:
            continue
        txt = get_text(did)
        prev = txt[:220].replace("\n", " ") + ("…" if len(txt) > 220 else "")
        hits.append(SearchHit(id=did, name=docs[did]["name"], score=float(score), preview=prev, meta=FullMetadata(**other_meta) if isinstance(other_meta, dict) else None ))

    hits = sorted(hits, key=lambda x: -x.score)[:topk]
    return SearchResponse(hits=hits)


@app.get("/api/external_recs/{doc_id}")
def external_recommendations(doc_id: str):
    """fetch related works using DOI/title; fallback to local semantic neighbors"""
    try:
        rec = get_doc(doc_id)
        final_meta = meta.get("final") or {}
        doi = final_meta.get("doi")
        title = final_meta.get("title")
        authors = final_meta.get("authors", [])


        academic_keywords = [
            "study", "analysis", "research", "paper", "experiment",
            "evaluation", "journal", "conference", "dataset", "neural", "algorithm"
        ]
        is_academic = any(re.search(rf"\b{k}\b", title.lower()) for k in academic_keywords)

        if doi:
            url = f"https://api.semanticscholar.org/recommendations/v1/papers/forpaper/DOI:{doi}"
            params = {"limit": 5, "fields": "title,authors,year,venue,abstract,url,citationCount"}
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json().get("recommendedPapers", [])
                if data:
                    return {
                        "source": "doi",
                        "recommendations": [
                            {
                                "title": d.get("title"),
                                "authors": [a["name"] for a in d.get("authors", [])],
                                "year": d.get("year"),
                                "venue": d.get("venue"),
                                "abstract": d.get("abstract"),
                                "citations": d.get("citationCount"),
                                "url": d.get("url"),
                            }
                            for d in data
                        ],
                    }

        if is_academic:
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {"query": title, "limit": 5, "fields": "title,authors,year,venue,abstract,url,citationCount"}
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json().get("data", [])
                if data:
                    return {
                        "source": "title",
                        "recommendations": [
                            {
                                "title": d.get("title"),
                                "authors": [a["name"] for a in d.get("authors", [])],
                                "year": d.get("year"),
                                "venue": d.get("venue"),
                                "abstract": d.get("abstract"),
                                "citations": d.get("citationCount"),
                                "url": d.get("url"),
                            }
                            for d in data
                        ],
                    }

        semantic.ensure_loaded()
        matches = semantic.similar(doc_id, topk=5)
        docs = {d["id"]: d for d in list_docs()}
        recs = []
        for did, score in matches:
            if did == doc_id or did not in docs:
                continue
            other = docs[did]
            other_meta = get_meta(did) or {}
            recs.append({
                "title": other_meta.get("title") or other["name"],
                "authors": other_meta.get("authors", []),
                "year": other_meta.get("year"),
                "venue": other_meta.get("venue"),
                "abstract": None,
                "citations": None,
                "url": None,
                "meta": FullMetadata(**other_meta)
            })
        if recs:
            return {"source": "local", "recommendations": recs}

        raise HTTPException(status_code=404, detail="No recommendations found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reindex")
def reindex():
    """rebuild semantic embeddings from stored text"""
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
    """serve pdf by id, matching saved filename prefix"""
    base_dir = str(Path(FILES_DIR))
    pattern = os.path.join(base_dir, f"{file_id}*.pdf")
    matches = glob.glob(pattern)
    if not matches:
        raise HTTPException(status_code=404, detail="Not Found")
    path = matches[0]
    return FileResponse(path, media_type="application/pdf")

from fastapi import Body
from datetime import datetime
import tempfile

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

@app.post("/api/export")
def export_report(payload: dict = Body(default={})):
    # payload comes from ExportPage checkboxes/radios
    fmt = (payload.get("format") or "pdf").lower()
    if fmt != "pdf":
        raise HTTPException(status_code=400, detail="only pdf export is implemented")

    include_all = bool(payload.get("allPapers", True))
    include_clusters_list = bool(payload.get("clustersList", True))
    include_papers_by_cluster = bool(payload.get("papersByCluster", True))
    include_summaries = bool(payload.get("summaries", True))
    include_keywords = bool(payload.get("keywords", True))
    include_insights = bool(payload.get("insights", True))

    docs = list_docs() or []

    try:
        clusters = get_clusters() or []
    except Exception as e:
        print("[export] failed to fetch clusters:", e)
        clusters = []

    # temp pdf path
    tmpdir = tempfile.mkdtemp()
    out_path = os.path.join(
        tmpdir,
        f"smartresearch_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

    styles = getSampleStyleSheet()
    story = []

    # ------------------------------------------------------------------
    # Cover
    # ------------------------------------------------------------------
    story.append(Paragraph("SmartResearch Export Report", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles["Normal"]
    ))
    story.append(Paragraph(f"Papers: {len(docs)}", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    # ------------------------------------------------------------------
    # Clusters overview
    # ------------------------------------------------------------------
    if include_clusters_list:
        story.append(Paragraph("Clusters", styles["Heading1"]))
        story.append(Spacer(1, 0.15 * inch))

        if clusters:
            rows = [["Cluster", "Papers", "Keywords / Description"]]
            for c in clusters:
                rows.append([
                    c.get("title") or c.get("id") or "untitled",
                    str(c.get("count") or 0),
                    (c.get("description") or "")[:1600],
                ])

            table = Table(rows, colWidths=[2.4*inch, 0.8*inch, 3.8*inch])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
                ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE", (0,0), (-1,-1), 9),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.lightyellow]),
                ("LEFTPADDING", (0,0), (-1,-1), 6),
                ("RIGHTPADDING", (0,0), (-1,-1), 6),
                ("TOPPADDING", (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]))
            story.append(table)
        else:
            story.append(Paragraph("No clusters available.", styles["Normal"]))

        story.append(PageBreak())

    # helper lookup
    doc_map = {d["id"]: d for d in docs}

    # ------------------------------------------------------------------
    # Papers by cluster
    # ------------------------------------------------------------------
    if include_papers_by_cluster and clusters:
        story.append(Paragraph("Papers by Cluster", styles["Heading1"]))
        story.append(Spacer(1, 0.15 * inch))

        for c in clusters:
            title = c.get("title") or c.get("id") or "cluster"
            story.append(Paragraph(title, styles["Heading2"]))

            if include_keywords and c.get("description"):
                story.append(Paragraph(c["description"], styles["Normal"]))

            paper_ids = c.get("paper_ids") or []
            story.append(Paragraph(f"Papers: {len(paper_ids)}", styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))

            for did in paper_ids:
                rec = doc_map.get(did) or {"name": did}
                meta = get_meta(did) or {}
                final_meta = meta.get("final") or {}

                title = final_meta.get("title") or rec.get("name") or did
                story.append(Paragraph(f"- {title}", styles["Normal"]))

                if include_summaries:
                    summary = (
                        final_meta.get("summary")
                        or final_meta.get("abstract")
                    )

                    if not summary:
                        try:
                            summary = textrankish_summary(get_text(did) or "")
                        except Exception as e:
                            logger.warning(f"Summary generation failed for doc {did}: {e}")
                            summary = None

                    if summary:
                        story.append(
                            Paragraph(f"<i>{summary[:1800]}</i>", styles["BodyText"])
                        )

                story.append(Spacer(1, 0.12 * inch))

            story.append(Spacer(1, 0.2 * inch))

        story.append(PageBreak())

    # ------------------------------------------------------------------
    # All papers
    # ------------------------------------------------------------------
    if include_all:
        story.append(Paragraph("All Papers", styles["Heading1"]))
        story.append(Spacer(1, 0.15 * inch))

        for d in docs:
            did = d["id"]
            meta = get_meta(did) or {}
            final_meta = meta.get("final") or {}

            title = final_meta.get("title") or d.get("name") or did
            story.append(Paragraph(title, styles["Heading2"]))

            # metadata line
            bits = []
            if final_meta.get("year"):
                bits.append(str(final_meta["year"]))
            if final_meta.get("venue"):
                bits.append(str(final_meta["venue"]))
            if final_meta.get("doi"):
                bits.append(f"doi: {final_meta['doi']}")

            if bits:
                story.append(Paragraph(" | ".join(bits), styles["Normal"]))

            # summary
            if include_summaries:
                summary = (
                    final_meta.get("summary")
                    or final_meta.get("abstract")
                )

                if not summary:
                    try:
                        summary = textrankish_summary(get_text(did) or "")
                    except Exception:
                        summary = None

                if summary:
                    story.append(
                        Paragraph(summary[:2400], styles["BodyText"])
                    )

            # reliability hint (optional but useful)
            if meta.get("confidence") is not None:
                story.append(
                    Paragraph(
                        f"<font size=8>confidence: {meta.get('confidence'):.2f} · reliable: {meta.get('reliable', True)}</font>",
                        styles["Normal"]
                    )
                )

            story.append(Spacer(1, 0.25 * inch))

    # ------------------------------------------------------------------
    # Build PDF
    # ------------------------------------------------------------------
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
