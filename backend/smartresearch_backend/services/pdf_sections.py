# smartresearch_backend/services/pdf_sections.py
from __future__ import annotations
import re
from typing import Optional
import fitz  # PyMuPDF

# ---------- helpers ----------
_HEADING_STOP = re.compile(
    r"(?im)^\s*(\d+\.?\s+)?("
    r"introduction|background|related work|literature review|methods?|methodology|"
    r"materials and methods|results|experiments?|analysis|discussion|conclusion|"
    r"conclusions|summary|acknowledg(e)?ments?|references|bibliography|appendix"
    r")\s*$"
)

def _norm(s: str) -> str:
    return re.sub(r"[ \t]+", " ", (s or "").strip())

# ---------- abstract ----------
def extract_abstract(pdf_path: str, max_pages: int = 25) -> Optional[str]:
    """
    Try to extract the Abstract from the first `max_pages` pages.
    Heuristics:
      1) TOC/outline entry 'Abstract'
      2) Standalone heading 'Abstract' on its own line -> until next heading
      3) Inline 'Abstract:' prefix -> until blank/Keywords/next heading
    """
    doc = fitz.open(pdf_path)
    try:
        n = min(max_pages, len(doc))
        pages_text = [doc[i].get_text("text") or "" for i in range(n)]
        joined = "\n".join(pages_text)

        # 1) TOC/outline
        toc = doc.get_toc(simple=True) or []
        for _, title, page in toc[:40]:
            if re.search(r"(?i)\babstract\b", title or "") and 1 <= (page or 0) <= n:
                t = doc[page - 1].get_text("text") or ""
                return _norm(t)[:3000] or None

        # 2) Standalone heading
        m = re.search(r"(?im)^\s*abstract\s*$", joined)
        if m:
            rest = joined[m.end():]
            stop = _HEADING_STOP.search(rest)
            block = rest[: stop.start()] if stop else rest
            return _norm(block)[:3000] or None

        # 3) Inline 'Abstract:'
        m = re.search(
            r"(?is)\babstract\s*[:\-]\s*(.+?)(?:\n{2,}|keywords?\s*[:\-]|introduction\b)",
            joined,
        )
        if m:
            return _norm(m.group(1))[:3000] or None

        return None
    finally:
        doc.close()

# ---------- generic section ----------
def extract_section(pdf_path: str, label: str, scan_pages: int = 25) -> Optional[str]:
    """
    Extract a named section (e.g., 'introduction', 'methods', 'conclusion') from the first `scan_pages`.
    Looks for a heading line that matches the label (case-insensitive), optionally with numbering.
    Returns text up to the next major heading.
    """
    if not label:
        return None
    label_rx = re.compile(rf"(?im)^\s*(\d+\.?\s+)?{re.escape(label)}\s*$")

    doc = fitz.open(pdf_path)
    try:
        n = min(scan_pages, len(doc))
        pages_text = [doc[i].get_text("text") or "" for i in range(n)]
        joined = "\n".join(pages_text)

        m = label_rx.search(joined)
        if not m:
            # also try inline "Label:" form
            m = re.search(rf"(?is)\b{re.escape(label)}\s*[:\-]\s*(.+?)\n{{2,}}", joined)
            if m:
                return _norm(m.group(1))[:4000] or None

        if not m:
            return None

        rest = joined[m.end():]
        stop = _HEADING_STOP.search(rest)
        block = rest[: stop.start()] if stop else rest
        return _norm(block)[:4000] or None
    finally:
        doc.close()
