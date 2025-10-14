import os, json
from pathlib import Path
from typing import List, Tuple, Dict
import numpy as np
from sentence_transformers import SentenceTransformer

# optional FAISS acceleration (used if installed)
try:
    import faiss
    _HAS_FAISS = True
except Exception:
    _HAS_FAISS = False


# config / globals
DATA_DIR = Path(os.getenv("SMARTRESEARCH_DATA", "./data_store"))
SEM_FILE = DATA_DIR / "semantic_chunks.json"

EMB_MODEL_NAME = os.getenv("SR_EMB_MODEL", "allenai/specter2_base")
_model = SentenceTransformer(EMB_MODEL_NAME)

# in-memory store (aka the semantic swamp)
_ids: List[str] = []              # chunk IDs like "doc1::0"
_doc_lookup: Dict[str, str] = {}  # chunk_id → doc_id
_vecs: np.ndarray = np.zeros(
    (0, _model.get_sentence_embedding_dimension()), dtype="float32"
)
_index = None


# internal helpers
def _save():
    """Persist chunk embeddings to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"ids": _ids, "vecs": _vecs.tolist(), "lookup": _doc_lookup}
    SEM_FILE.write_text(json.dumps(payload), encoding="utf-8")


def _rebuild_index():
    """Rebuild FAISS or NumPy index depending on what’s available."""
    global _index
    if _vecs.shape[0] == 0:
        _index = None
        return

    if _HAS_FAISS:
        dim = _vecs.shape[1]
        ix = faiss.IndexFlatIP(dim)
        normed_vecs = _vecs / np.linalg.norm(_vecs, axis=1, keepdims=True)
        ix.add(normed_vecs.astype("float32"))
        _index = ix
    else:
        _index = None


def _load():
    """Load embeddings and IDs from disk (or start fresh)."""
    global _ids, _vecs, _doc_lookup
    if SEM_FILE.exists():
        try:
            data = json.loads(SEM_FILE.read_text(encoding="utf-8"))
            _ids = data.get("ids", [])
            _vecs = np.array(data.get("vecs", []), dtype="float32")
            _doc_lookup = data.get("lookup", {})
            print(f"✅ Loaded {_vecs.shape[0]} chunk embeddings from {SEM_FILE}")
        except Exception as e:
            print(f"⚠️ Failed to load semantic index: {e}")
            _ids, _doc_lookup = [], {}
            _vecs = np.zeros(
                (0, _model.get_sentence_embedding_dimension()), dtype="float32"
            )
    else:
        _ids, _doc_lookup = [], {}
        _vecs = np.zeros(
            (0, _model.get_sentence_embedding_dimension()), dtype="float32"
        )

    _rebuild_index()


def ensure_loaded():
    """Guarantees the index is ready before anything touches it."""
    if (_vecs is None) or (_vecs.shape[0] == 0 and not SEM_FILE.exists()):
        _load()
    elif _index is None:
        _rebuild_index()


def _encode(texts: List[str]) -> np.ndarray:
    """Encode text into normalized vector space."""
    if not texts:
        return np.zeros((0, _model.get_sentence_embedding_dimension()), dtype="float32")
    v = _model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return v.astype("float32")


# public functions
def add_doc(doc_id: str, text: str):
    """
    Splits a document into semantic chunks and adds them to the index.
    Removes any existing chunks first to prevent duplication.
    """
    global _vecs, _ids, _doc_lookup
    ensure_loaded()

    # clean slate for this doc
    remove_doc(doc_id)

    # include filename context for literal recall
    filename_text = doc_id.replace("_", " ").replace("-", " ")
    text = f"{filename_text}\n{text}"

    # split into ~300–600 word chunks (paragraph-based)
    paras = [p.strip() for p in text.split("\n") if len(p.strip()) > 40]
    chunks, buf = [], ""
    for p in paras:
        if len(buf.split()) + len(p.split()) < 500:
            buf += " " + p
        else:
            chunks.append(buf.strip())
            buf = p
    if buf:
        chunks.append(buf.strip())

    if not chunks:
        return

    # prefix filename for context anchoring
    chunks = [f"{filename_text}. {c}" for c in chunks]
    vecs = _encode(chunks)
    if vecs.shape[0] == 0:
        return

    # append vectors + update in-memory maps
    for i, v in enumerate(vecs):
        chunk_id = f"{doc_id}::{i}"
        _ids.append(chunk_id)
        _doc_lookup[chunk_id] = doc_id
        _vecs = np.vstack([_vecs, v.reshape(1, -1)]) if _vecs.size else v.reshape(1, -1)

    _save()
    _rebuild_index()
    print(f"📚 Added {len(chunks)} chunks for {doc_id} (total {_vecs.shape[0]} vectors)")


def remove_doc(doc_id: str):
    """Remove all chunks for a given document."""
    global _vecs, _ids, _doc_lookup
    ensure_loaded()
    keep_indices = [i for i, cid in enumerate(_ids) if not cid.startswith(f"{doc_id}::")]
    if len(keep_indices) < len(_ids):
        _vecs = _vecs[keep_indices, :] if len(keep_indices) else np.zeros(
            (0, _model.get_sentence_embedding_dimension()), dtype="float32"
        )
        _ids = [_ids[i] for i in keep_indices]
        _doc_lookup = {cid: did for cid, did in _doc_lookup.items() if did != doc_id}
        _save()
        _rebuild_index()


def search(q: str, topk: int = 10) -> List[Tuple[str, float]]:
    """
    Performs chunk-level semantic search and aggregates scores by document.
    Uses FAISS if available, else falls back to NumPy similarity.
    """
    ensure_loaded()
    if _vecs.shape[0] == 0:
        return []

    qv = _encode([q])
    if qv.shape[0] == 0:
        return []

    qv = qv / np.linalg.norm(qv, axis=1, keepdims=True)

    # chunk-level similarity computation
    if _HAS_FAISS and _index is not None:
        D, I = _index.search(qv.astype("float32"), min(topk * 3, len(_ids)))
        scores = [(_ids[i], float(D[0][j])) for j, i in enumerate(I[0])]
    else:
        sims = (qv @ (_vecs.T / np.linalg.norm(_vecs, axis=1))).flatten()
        order = np.argsort(-sims)[: min(topk * 3, len(_ids))]
        scores = [(_ids[i], float(sims[i])) for i in order]

    # aggregate by doc
    doc_scores: Dict[str, List[float]] = {}
    for cid, s in scores:
        doc_id = _doc_lookup.get(cid, cid.split("::")[0])
        doc_scores.setdefault(doc_id, []).append(s)

    # average of top-3 chunk scores = doc score
    agg = []
    for doc_id, vals in doc_scores.items():
        vals.sort(reverse=True)
        agg.append((doc_id, float(np.mean(vals[:3]))))

    agg.sort(key=lambda x: -x[1])
    return agg[:topk]


def similar(doc_id: str, topk: int = 10) -> List[Tuple[str, float]]:
    """
    Finds documents semantically similar to a given one
    by averaging cosine similarities across all chunks.
    """
    ensure_loaded()
    chunk_indices = [i for i, cid in enumerate(_ids) if cid.startswith(f"{doc_id}::")]
    if not chunk_indices:
        return []

    qv = _vecs[chunk_indices, :]
    qv = qv / np.linalg.norm(qv, axis=1, keepdims=True)
    sims = (qv @ (_vecs.T / np.linalg.norm(_vecs, axis=1))).mean(axis=0)
    order = np.argsort(-sims)

    out = []
    for i in order:
        cid = _ids[i]
        did = _doc_lookup.get(cid, cid.split("::")[0])
        if did == doc_id:
            continue
        out.append((did, float(sims[i])))

    # remove dupes and truncate
    seen, final = set(), []
    for did, s in out:
        if did not in seen:
            seen.add(did)
            final.append((did, s))
        if len(final) >= topk:
            break
    return final


# initialize on import (so you don't have to remember)
try:
    _load()
except Exception as e:
    print("⚠️ Semantic index not loaded at startup:", e)
