import os, uuid, json, hashlib, time
from pathlib import Path
from typing import Dict, List, Optional

# data directories
DATA_DIR = Path(os.getenv("SMARTRESEARCH_DATA", "./data_store")).resolve()
FILES = DATA_DIR / "files"
TEXTS = DATA_DIR / "texts"
INDEX_FILE = DATA_DIR / "index.json"

# make sure base folders exist
for p in (FILES, TEXTS):
    p.mkdir(parents=True, exist_ok=True)

# in-memory index cache
_index: Dict[str, Dict] = {}


# helper functions
def _new_id() -> str:
    """generate a short random id for new documents"""
    return uuid.uuid4().hex[:12]


def _sha1(b: bytes) -> str:
    """compute a SHA-1 hash for integrity checking or dedup"""
    h = hashlib.sha1()
    h.update(b)
    return h.hexdigest()


def _save_index():
    """write the in-memory index to disk as JSON"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(
        json.dumps(_index, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_index():
    """load index.json if it exists, else start empty"""
    global _index
    if INDEX_FILE.exists():
        try:
            _index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        except Exception:
            _index = {}
    else:
        _index = {}


# preload existing index on import
_load_index()


# file operations
def save_file(filename: str, content: bytes) -> dict:
    """
    save an uploaded file to disk and update the index.
    returns a record containing metadata for later retrieval.
    """
    did = _new_id()
    fpath = FILES / f"{did}_{filename}"
    fpath.write_bytes(content)

    rec = {
        "id": did,
        "name": filename,
        "path": str(fpath),
        "bytes": len(content),
        "sha1": _sha1(content),
        "created": int(time.time()),
    }

    _index[did] = rec
    _save_index()
    return rec


def save_text(did: str, text: str):
    """save processed or extracted text for a given document id"""
    (TEXTS / f"{did}.txt").write_text(text, encoding="utf-8")


def get_text(did: str) -> str:
    """load and return the stored text for a given document id"""
    p = TEXTS / f"{did}.txt"
    if p.exists():
        return p.read_text(encoding="utf-8")
    raise FileNotFoundError(did)


def save_meta(did: str, meta: dict):
    """store JSON metadata for a document"""
    (TEXTS / f"{did}.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_meta(did: str) -> Optional[dict]:
    """return metadata for a document, or None if unavailable"""
    p = TEXTS / f"{did}.meta.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def get_doc(did: str) -> dict:
    """return the index record for a given document id"""
    rec = _index.get(did)
    if not rec:
        raise FileNotFoundError(did)
    return rec


def list_docs() -> List[dict]:
    """
    list all stored documents with basic metadata.
    sorted newest-first (descending by id).
    """
    out = []
    for did, rec in _index.items():
        tpath = TEXTS / f"{did}.txt"
        n_chars = tpath.stat().st_size if tpath.exists() else 0
        out.append({"id": did, "name": rec["name"], "n_chars": int(n_chars)})

    out.sort(key=lambda r: r["id"], reverse=True)
    return out


def delete_doc(did: str) -> bool:
    """
    delete a document and all related data (file, text, metadata).
    returns True if successfully deleted, False if not found.
    """
    rec = _index.pop(did, None)
    if not rec:
        return False

    f = Path(rec.get("path", ""))
    if f.exists():
        try:
            f.unlink()
        except Exception:
            pass

    # remove extracted text + metadata
    for ext in [".txt", ".meta.json"]:
        t = TEXTS / f"{did}{ext}"
        if t.exists():
            try:
                t.unlink()
            except Exception:
                pass

    _save_index()
    return True
