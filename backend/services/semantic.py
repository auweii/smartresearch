import os
import json
from pathlib import Path
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer

DATA_DIR = Path(os.getenv("SMARTRESEARCH_DATA", "./data_store"))
SEM_FILE = DATA_DIR / "semantic_chunks.json"
EMB_MODEL_NAME = os.getenv("SR_EMB_MODEL", "allenai/specter2_base")
FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _load_model():
    try:
        print(f"🔄 Loading embedding model: {EMB_MODEL_NAME}")
        model = SentenceTransformer(
            EMB_MODEL_NAME,
            cache_folder=str(DATA_DIR / "models"),
            local_files_only=False,
        )
        print("✅ SPECTER2 model loaded")
        return model
    except Exception as e:
        print(f"⚠️ SPECTER2 failed: {e} — falling back to MiniLM")
        model = SentenceTransformer(FALLBACK_MODEL)
        print("✅ Fallback model loaded")
        return model


_model = _load_model()

_ids: List[str] = []
_doc_lookup: Dict[str, str] = {}
_vecs: np.ndarray = np.zeros(
    (0, _model.get_sentence_embedding_dimension()),
    dtype="float32",
)


def _save():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SEM_FILE.write_text(
        json.dumps({"ids": _ids, "vecs": _vecs.tolist(), "lookup": _doc_lookup}),
        encoding="utf-8",
    )


def _load():
    global _ids, _vecs, _doc_lookup
    if SEM_FILE.exists():
        try:
            data = json.loads(SEM_FILE.read_text(encoding="utf-8"))
            _ids = data.get("ids", [])
            _vecs = np.array(data.get("vecs", []), dtype="float32")
            _doc_lookup = data.get("lookup", {})
            print(f"📦 Loaded {len(_ids)} embeddings")
        except Exception as e:
            print(f"⚠️ Failed to load index: {e}")
            _ids = []
            _doc_lookup = {}
            _vecs = np.zeros((0, _model.get_sentence_embedding_dimension()), dtype="float32")
    else:
        _ids = []
        _doc_lookup = {}
        _vecs = np.zeros((0, _model.get_sentence_embedding_dimension()), dtype="float32")


def ensure_loaded():
    if _vecs.shape[0] == 0 and SEM_FILE.exists():
        _load()


def _encode(texts: List[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, _model.get_sentence_embedding_dimension()), dtype="float32")
    v = _model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return v.astype("float32")


def add_doc(doc_id: str, text: str):
    global _vecs, _ids, _doc_lookup

    ensure_loaded()
    remove_doc(doc_id)

    filename_text = doc_id.replace("_", " ").replace("-", " ")
    text = f"{filename_text}\n{text}"

    # split text into ~800-word chunks
    paras = [p.strip() for p in text.split("\n") if len(p.strip()) > 40]
    chunks = []
    buf = ""

    for p in paras:
        if len(buf.split()) + len(p.split()) < 800:
            buf += " " + p
        else:
            chunks.append(buf.strip())
            buf = p

    if buf:
        chunks.append(buf.strip())

    if not chunks:
        return

    chunks = [f"{filename_text}. {c}" for c in chunks]
    vecs = _encode(chunks)

    for i, v in enumerate(vecs):
        chunk_id = f"{doc_id}::{i}"
        _ids.append(chunk_id)
        _doc_lookup[chunk_id] = doc_id
        _vecs = (
            np.vstack([_vecs, v.reshape(1, -1)])
            if _vecs.size else v.reshape(1, -1)
        )

    _save()


def remove_doc(doc_id: str):
    global _vecs, _ids, _doc_lookup

    ensure_loaded()

    keep = [i for i, cid in enumerate(_ids) if not cid.startswith(f"{doc_id}::")]

    if len(keep) < len(_ids):
        _ids = [_ids[i] for i in keep]
        _vecs = _vecs[keep] if len(keep) else np.zeros(
            (0, _model.get_sentence_embedding_dimension()), dtype="float32"
        )
        _doc_lookup = {cid: did for cid, did in _doc_lookup.items() if did != doc_id}
        _save()


def search(q: str, topk: int = 10):
    ensure_loaded()

    if _vecs.shape[0] == 0:
        return []

    qv = _encode([q])
    qv = qv / np.linalg.norm(qv, axis=1, keepdims=True)
    sims = (qv @ (_vecs.T / np.linalg.norm(_vecs, axis=1))).flatten()
    order = np.argsort(-sims)

    out = []
    seen = set()

    for i in order:
        did = _doc_lookup.get(_ids[i], _ids[i].split("::")[0])
        if did not in seen:
            seen.add(did)
            out.append((did, float(sims[i])))
        if len(out) >= topk:
            break

    return out


def similar(doc_id: str, topk: int = 10):
    ensure_loaded()

    idx = [i for i, cid in enumerate(_ids) if cid.startswith(f"{doc_id}::")]
    if not idx:
        return []

    qv = _vecs[idx]
    qv = qv / np.linalg.norm(qv, axis=1, keepdims=True)
    sims = (qv @ (_vecs.T / np.linalg.norm(_vecs, axis=1))).mean(axis=0)
    order = np.argsort(-sims)

    out = []
    seen = set()

    for i in order:
        did = _doc_lookup.get(_ids[i], _ids[i].split("::")[0])
        if did == doc_id:
            continue
        if did not in seen:
            seen.add(did)
            out.append((did, float(sims[i])))
        if len(out) >= topk:
            break

    return out


try:
    _load()
except Exception as e:
    print("⚠️ Semantic index startup failed:", e)