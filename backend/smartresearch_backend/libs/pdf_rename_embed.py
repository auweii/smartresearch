import os, re, sys, unicodedata, tempfile, shutil, datetime
from typing import Optional, Literal, Tuple
import fitz  # PyMuPDF

from .pdf_formatter import parse_structured, parse_heuristic

Mode = Literal["auto", "structured", "heuristic"]

# ---------- read first N pages ----------
def read_text_first_n_pages(pdf_path: str, pages: int = 1) -> str:
    try:
        with fitz.open(pdf_path) as doc:
            pages = max(1, min(pages, len(doc)))
            return "\n".join((doc[i].get_text("text") or "") for i in range(pages))
    except Exception as e:
        print(f"[WARN] cannot read '{pdf_path}': {e}", file=sys.stderr)
        return ""

# ---------- choose extraction ----------
def extract_meta(text: str, mode: Mode = "auto") -> Tuple[Optional[str], Optional[str], Optional[int]]:
    if mode == "structured":
        return parse_structured(text)
    if mode == "heuristic":
        return parse_heuristic(text)

    # auto: try structured then fallback
    t, a, y = parse_structured(text)
    if not (t and a and y):
        t2, a2, y2 = parse_heuristic(text)
        t = t or t2
        a = a or a2
        y = y or y2
    return t, a, y

# ---------- filename helpers ----------
def _slug(s: str, maxlen: int) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s-]+", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    s = re.sub(r"_+", "_", s)
    return s.lower().strip("_")[:maxlen]

def _slug_authors(auth_line: Optional[str], maxlen: int = 80) -> str:
    if not auth_line:
        return "anon"
    # remove extra spaces, commas/semicolons become underscores
    clean = auth_line.replace(";", "_").replace(",", "_")
    clean = "_".join(clean.split())  # collapse spaces
    return _slug(clean, maxlen)

def _split_authors(auth_line: str) -> list[str]:
    """Split an author line into individual author names.
    Prefers ';' or ' and ' as separators. Falls back to ', ' when there are 2+ commas
    (to avoid splitting single 'Last, First' names)."""
    s = auth_line.strip()
    if ";" in s:
        parts = [p.strip() for p in s.split(";") if p.strip()]
    elif " and " in s.lower():
        parts = [p.strip() for p in re.split(r"\s+[Aa][Nn][Dd]\s+", s) if p.strip()]
    elif s.count(",") >= 2:
        # e.g., "Ada Lovelace, Alan Turing"  (multiple authors with comma separators)
        parts = [p.strip() for p in s.split(",") if p.strip()]
    else:
        parts = [s] if s else []
    return parts

def _slug_name(name: str) -> str:
    """Slugify a single author name (full name kept)."""
    # collapse multiple spaces, then reuse _slug
    name = re.sub(r"\s{2,}", " ", name.strip())
    return _slug(name, 60)

def _slug_authors_limited(auth_line: str | None, limit: int = 3) -> str:
    """Slugify authors for filename: keep first N full names, append _etal if truncated."""
    if not auth_line:
        return "anon"
    authors = _split_authors(auth_line)
    if not authors:
        return "anon"
    kept = authors[:limit]
    slugged = "_".join(_slug_name(a) for a in kept if a)
    if len(authors) > limit:
        slugged = f"{slugged}_etal"
    return slugged or "anon"


def build_filename(title: Optional[str], authors: Optional[str], year: Optional[int], fallback: str) -> str:
    t = _slug(title or fallback, 80)
    a = _slug_authors_limited(authors, limit=3)  # <-- first 3 authors, then _etal
    y = str(year) if year else "noyear"
    return f"{t}_{a}_{y}.pdf"



def unique_path(path: str) -> str:
    base, ext = os.path.splitext(path)
    out, k = path, 1
    while os.path.exists(out):
        out = f"{base}-{k}{ext}"
        k += 1
    return out

# ---------- embed metadata & save ----------
def embed_title_author_dates(src: str, dst: str,
                             title: Optional[str], authors: Optional[str], year: Optional[int]) -> None:
    with fitz.open(src) as doc:
        meta = doc.metadata or {}
        meta["title"]  = title or os.path.splitext(os.path.basename(dst))[0]
        meta["author"] = authors or "Unknown"
        meta["modDate"] = datetime.datetime.now().strftime("D:%Y%m%d%H%M%S")
        if year and 1900 <= year <= 2100:
            meta["creationDate"] = f"D:{year}0101000000Z"
        doc.set_metadata(meta)

        tmpdir = tempfile.mkdtemp(prefix="pdfmeta_")
        try:
            tmp_out = os.path.join(tmpdir, os.path.basename(dst))
            doc.save(tmp_out)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(tmp_out, dst)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

# ---------- main worker ----------
def rename_folder(folder: str, apply: bool = False, pages: int = 1, mode: Mode = "auto"):
    """
    Yields tuples:
      ("dry"/"done", old_name, new_name, title, authors, year)
    """
    files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
    files.sort()
    for fname in files:
        src = os.path.join(folder, fname)
        stem, _ = os.path.splitext(fname)

        text = read_text_first_n_pages(src, pages)
        title, authors, year = extract_meta(text, mode)
        new_name = build_filename(title, authors, year, fallback=stem)
        dst = unique_path(os.path.join(folder, new_name))

        if not apply:
            # preview only
            yield ("dry", fname, os.path.basename(dst), title, authors, year)
        else:
            # write metadata & move
            embed_title_author_dates(src, dst, title, authors, year)
            if os.path.abspath(src) != os.path.abspath(dst):
                try:
                    os.remove(src)
                except Exception:
                    pass
            yield ("done", fname, os.path.basename(dst), title, authors, year)
