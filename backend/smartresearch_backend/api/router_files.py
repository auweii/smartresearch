from fastapi import APIRouter, UploadFile, File, HTTPException
import os, shutil, uuid, hashlib, re
from typing import List
from ..services.storage import FILES, UPLOAD_DIR
from ..schemas.models import FileInfo
from ..libs.pdf_formatter import parse_front_matter  # if you have it
import fitz  # PyMuPDF for embedding metadata

router = APIRouter()

SAFE_CHARS = re.compile(r"[^a-z0-9_\-]+")

def slug(s: str) -> str:
    s = (s or "").lower().strip()
    s = s.replace("&", " and ").replace("/", " ").replace("\\", " ")
    s = SAFE_CHARS.sub("_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "untitled"

def safe_filename(title: str, authors: str | None, year: int | None, max_len: int = 140) -> str:
    author_part = ""
    if authors:
        # use first surname only to keep name short
        first = authors.split(";")[0].strip()
        # keep last token as surname if possible
        surname = first.split()[-1] if first else ""
        author_part = f"_{slug(surname)}"
    yr = f"_{year}" if year else ""
    base = f"{slug(title)}{author_part}{yr}".strip("_")
    # cap total length incl extension
    ext = ".pdf"
    if len(base) > max_len:
        base = base[:max_len]
        base = base.rstrip("_-")
    return f"{base}{ext}"

def unique_path(dirpath: str, filename: str) -> str:
    """Ensure filename doesn't collide."""
    path = os.path.join(dirpath, filename)
    if not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(filename)
    # short contentless hash to avoid overlong names
    salt = hashlib.sha1(stem.encode("utf-8")).hexdigest()[:6]
    return os.path.join(dirpath, f"{stem}_{salt}{ext}")

def embed_pdf_metadata(path: str, title: str | None, authors: str | None, year: int | None):
    try:
        doc = fitz.open(path)
        meta = doc.metadata or {}
        if title:   meta["title"] = title
        if authors: meta["author"] = authors
        if year:    meta["modDate"] = f"D:{year}0101000000Z"  # simple year stamp
        doc.set_metadata(meta)
        doc.save(path, incremental=True, deflate=True)
        doc.close()
    except Exception:
        # don't fail upload if metadata fails
        pass

@router.post("", response_model=list[FileInfo])
async def upload_files(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(400, "no files")
    out: list[dict] = []

    # 1) save raw uploads with their incoming names (temp)
    saved_paths: list[str] = []
    for f in files:
        raw_path = os.path.join(UPLOAD_DIR, f.filename)
        with open(raw_path, "wb") as out_f:
            shutil.copyfileobj(f.file, out_f)
        saved_paths.append(raw_path)

    # 2) process ONLY those paths: extract front-matter, build safe name, rename
    for raw_path in saved_paths:
        # extract frontmatter (title/authors/year) from first pages
        title, authors, year = None, None, None
        try:
            title, authors, year = parse_front_matter(raw_path, pages=2)  # your helper
        except Exception:
            pass

        # fallback title = original name without extension
        if not title:
            title = os.path.splitext(os.path.basename(raw_path))[0]

        new_name = safe_filename(title, authors, year)
        new_path = unique_path(UPLOAD_DIR, new_name)

        # rename (move) the file
        os.replace(raw_path, new_path)

        # embed metadata (best-effort)
        embed_pdf_metadata(new_path, title, authors, year)

        # register a single FILES record for THIS upload
        file_id = uuid.uuid4().hex[:8]
        rec = {
            "file_id": file_id,
            "old_name": os.path.basename(raw_path),
            "new_name": os.path.basename(new_path),
            "title": title,
            "authors": authors,
            "year": year,
            "path": new_path,
            "size_bytes": os.path.getsize(new_path),
        }
        FILES[file_id] = rec
        out.append({k: rec[k] for k in ["file_id","old_name","new_name","title","authors","year","size_bytes"]})

    return out
