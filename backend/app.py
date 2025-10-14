from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import requests
import re
import os
import glob
from pathlib import Path

from models.schemas import (
    UploadResponse, DocMeta, SummarizeRequest, SummarizeResponse,
    SearchRequest, SearchResponse, SearchHit, MetaResponse, Metadata, TextResponse
)
from utils.storage import (
    save_file, save_text, get_text, list_docs, get_doc,
    delete_doc, save_meta, get_meta, FILES as FILES_DIR
)
from services.extract import pdf_to_text
from services.summarize import textrankish_summary
from services.ocr import ocr_pdf_to_text
from services.metadata import enrich_from_text
from services import semantic
from services.cluster import Clusterer 


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
    """return all indexed docs with minimal metadata"""
    docs = list_docs()
    enriched = []
    for d in docs:
        meta = get_meta(d["id"]) or {}
        summary = meta.get("summary") or meta.get("abstract")
        enriched.append({**d, "summary": summary})
    return enriched

@app.get("/api/clustered")
def get_clusters():
    """temporary mock clusters for frontend testing"""
    return [
        {
            "id": "cluster-1",
            "title": "Transformer Models for Text Summarization",
            "authors": [
                "Ashish Vaswani",
                "Noam Shazeer",
                "Niki Parmar",
                "Jakob Uszkoreit",
                "Lukasz Kaiser",
            ],
            "count": 12,
            "description": "Papers related to language models and summarization.",
        },
        {
            "id": "cluster-2",
            "title": "Natural Language Processing Foundations",
            "authors": ["Tom Brown", "Sam Altman", "Alec Radford"],
            "count": 7,
            "description":
                "Focuses on NLP techniques, tokenization, embeddings, and contextual learning in large language models.",
        },
        {
            "id": "cluster-3",
            "title": "Explainable AI and Model Interpretability",
            "authors": ["Cynthia Rudin", "Marco Tulio Ribeiro", "Sameer Singh"],
            "count": 9,
            "description":
                "Research on transparency, model interpretability, and trust in machine learning pipelines.",
        },
        {
            "id": "cluster-4",
            "title": "Cybersecurity Threat Detection",
            "authors": ["Ross Anderson", "Bruce Schneier", "Gene Spafford"],
            "count": 10,
            "description":
                "Detection of anomalies, intrusion patterns, and adversarial resilience in cyber defense systems.",
        },
        {
            "id": "cluster-5",
            "title": "Federated Learning and Privacy",
            "authors": ["Jakub Konečný", "H. Brendan McMahan", "Daniel Ramage"],
            "count": 11,
            "description":
                "Distributed learning approaches preserving data privacy and improving model generalization.",
        },
    ]


@app.get("/api/text/{doc_id}", response_model=TextResponse)
def fetch_text(doc_id: str):
    """return full text for a given doc"""
    rec = get_doc(doc_id)
    text = get_text(doc_id)
    return TextResponse(id=doc_id, name=rec["name"], text=text, n_chars=len(text))


@app.get("/api/meta/{doc_id}", response_model=MetaResponse)
def fetch_meta(doc_id: str):
    """retrieve and refresh metadata where possible"""
    _ = get_doc(doc_id)
    meta = get_meta(doc_id)
    doi = meta.get("doi") if isinstance(meta, dict) else None

    # if no abstract, fetch from Semantic Scholar
    if doi and "abstract" not in meta:
        try:
            res = requests.get(
                f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}",
                params={"fields": "title,abstract,venue,year,authors,citationCount"},
                timeout=10,
            )
            if res.status_code == 200:
                data = res.json()
                meta.update({
                    "abstract": data.get("abstract"),
                    "venue": data.get("venue"),
                    "citationCount": data.get("citationCount"),
                })
                save_meta(doc_id, meta)
        except Exception:
            pass

    # ensure summary always exists
    try:
        summary = meta.get("summary") if isinstance(meta, dict) else None
        if not summary:
            summary = (meta.get("abstract") if isinstance(meta, dict) else None) or textrankish_summary(get_text(doc_id))
            if isinstance(meta, dict):
                meta["summary"] = summary
                save_meta(doc_id, meta)
    except Exception:
        pass

    return MetaResponse(id=doc_id, meta=Metadata(**meta) if isinstance(meta, dict) else None)


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

    raw = await file.read()
    rec = save_file(file.filename, raw)

    text = pdf_to_text(rec["path"])
    used_ocr = False
    if len(text.strip()) < 200:
        try:
            ocr_text = ocr_pdf_to_text(rec["path"])
            if len(ocr_text.strip()) > len(text.strip()):
                text = ocr_text
                used_ocr = True
        except Exception:
            pass

    save_text(rec["id"], text)
    try:
        semantic.add_doc(rec["id"], text)
    except Exception:
        pass

    meta = enrich_from_text(text) or {}
    if meta:
        save_meta(rec["id"], meta)

    preview = (text[:600] + "…") if len(text) > 600 else text
    try:
        _ensure_tfidf_ready()
    except Exception:
        pass

    return UploadResponse(
        doc=DocMeta(id=rec["id"], name=rec["name"], n_chars=len(text)),
        preview=preview,
        used_ocr=used_ocr,
        meta=Metadata(**meta) if meta else None,
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
        hits.append(SearchHit(id=did, name=docs[did]["name"], score=float(score), preview=prev))

    hits = sorted(hits, key=lambda x: -x.score)[:topk]
    return SearchResponse(hits=hits)


@app.get("/api/external_recs/{doc_id}")
def external_recommendations(doc_id: str):
    """fetch related works using DOI/title; fallback to local semantic neighbors"""
    try:
        rec = get_doc(doc_id)
        meta = get_meta(doc_id) or {}
        doi = meta.get("doi")
        title = meta.get("title") or rec["name"]

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
        except Exception:
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

