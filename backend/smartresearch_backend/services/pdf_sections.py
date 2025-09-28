# smartresearch_backend/services/pdf_sections.py
from __future__ import annotations
import re
from typing import Optional, Tuple
import fitz  # PyMuPDF

# stop when we hit a typical next-heading
_HEADING_STOP = re.compile(
    r"(?im)^\s*(\d+[\.\)]\s+)?("
    r"related work|literature review|methods?|methodology|"
    r"materials and methods|results|experiments?|analysis|discussion|conclusion|"
    r"conclusions|summary|acknowledg(e)?ments?|keywords?|references|bibliography|appendix"
    r")\s*$"
)

# accepted variants for "Abstract"
_ABS_LABELS = [
    r"abstract", r"extended abstract", r"executive summary", r"summary", r"summaries", r"introduction"
]

def _norm(s: str) -> str:
    return re.sub(r"[ \t]+", " ", (s or "").strip())

def _join_pages(doc, max_pages: int) -> str:
    n = min(max_pages, len(doc))
    return "\n".join((doc[i].get_text("text") or "") for i in range(n))

def _find_outline_abstract(doc, n: int) -> Optional[str]:
    toc = doc.get_toc(simple=True) or []
    for _, title, page in toc[:80]:
        if title and re.search(r"(?i)\babstract\b", title):
            if 1 <= (page or 0) <= n:
                return doc[page - 1].get_text("text") or ""
    return None

def _largest_font_heading_extract(doc, max_pages: int) -> Optional[str]:
    """
    Heuristic: find a heading span whose text =~ 'Abstract' with large size/bold.
    Then extract until next large heading or canonical stop heading.
    """
    n = min(max_pages, len(doc))
    # collect candidate (page_index, y1, text, font_size, is_bold)
    candidates: list[Tuple[int, float, str, float, bool]] = []

    for pi in range(n):
        d = doc[pi].get_text("dict")  # layout dict with blocks/lines/spans
        for b in d.get("blocks", []):
            for l in b.get("lines", []):
                for sp in l.get("spans", []):
                    t = (sp.get("text") or "").strip()
                    if not t:
                        continue
                    if re.fullmatch(r"(?is)\s*(abstract|extended abstract)\s*", t):
                        size = float(sp.get("size", 0.0))
                        font = (sp.get("font", "") or "").lower()
                        is_bold = "bold" in font or "black" in font
                        y1 = float(sp.get("bbox", [0, 0, 0, 0])[1])
                        candidates.append((pi, y1, t, size, is_bold))

    if not candidates:
        return None

    # pick the "strongest heading": largest size, then boldness, then earliest page
    candidates.sort(key=lambda x: (x[3], x[4], -x[0]), reverse=True)
    h_page, _, _, _, _ = candidates[0]

    # extract from heading line to next heading/stop keyword on the SAME PAGE FIRST
    page_text = doc[h_page].get_text("text") or ""
    # split by lines, find the "Abstract" line, take following lines until stop
    lines = [ln for ln in page_text.splitlines()]
    start_idx = None
    for idx, ln in enumerate(lines):
        if re.fullmatch(r"(?im)\s*abstract\s*$", ln.strip()):
            start_idx = idx + 1
            break
    if start_idx is not None:
        rest = "\n".join(lines[start_idx:])
        stop = _HEADING_STOP.search(rest)
        block = rest[: stop.start()] if stop else rest
        if block.strip():
            return block

    # else fall back: return full page text
    return page_text

def extract_abstract(pdf_path: str, max_pages: int = 25, max_chars: int = 3000) -> Optional[str]:
    """
    Extract Abstract using a cascade of strategies:
      1) Outline/TOC entry named 'Abstract'
      2) Style-aware heading detection (font size/bold) on 'Abstract'
      3) Standalone 'Abstract' line -> until next canonical heading
      4) Inline 'Abstract:' form -> until blank/Keywords/next heading
    """
    doc = fitz.open(pdf_path)
    try:
        n = min(max_pages, len(doc))

        # 1) TOC/outline
        t = _find_outline_abstract(doc, n)
        if t:
            return _norm(t)[:max_chars] or None

        # 2) Style-aware
        t = _largest_font_heading_extract(doc, n)
        if t and t.strip():
            return _norm(t)[:max_chars] or None

        # 3) Standalone heading in joined text
        joined = _join_pages(doc, n)

        # some PDFs have numbering like "0 Abstract" or "Abstract 1"
        m = re.search(r"(?im)^\s*(\d+[\.\)]\s+)?abstract\s*(\d+[\.\)]\s*)?$", joined)
        if m:
            rest = joined[m.end():]
            stop = _HEADING_STOP.search(rest)
            block = rest[: stop.start()] if stop else rest
            if block.strip():
                return _norm(block)[:max_chars] or None

        # 4) Inline 'Abstract:'
        inline = re.search(
            r"(?is)\babstract\s*[:\-]\s*(.+?)(?:\n{2,}|keywords?\s*[:\-]|"
            r"introduction\b|background\b|related work\b|literature review\b)",
            joined,
        )
        if inline:
            return _norm(inline.group(1))[:max_chars] or None

        # 5) Broader label variants: (executive summary, summary, etc.)
        for lab in _ABS_LABELS:
            m2 = re.search(rf"(?im)^\s*(\d+[\.\)]\s+)?{lab}\s*$", joined)
            if m2:
                rest = joined[m2.end():]
                stop = _HEADING_STOP.search(rest)
                block = rest[: stop.start()] if stop else rest
                if block.strip():
                    return _norm(block)[:max_chars] or None

        # 6) Nothing found
        return None
    finally:
        doc.close()

def extract_section(pdf_path: str, label: str, scan_pages: int = 25, max_chars: int = 4000) -> Optional[str]:
    """
    Generic section extractor. Heading like '1 Introduction' or 'Introduction'.
    Also tries inline 'Label:' as fallback.
    """
    if not label:
        return None
    doc = fitz.open(pdf_path)
    try:
        n = min(scan_pages, len(doc))
        joined = _join_pages(doc, n)

        # Heading line
        label_rx = re.compile(rf"(?im)^\s*(\d+[\.\)]\s+)?{re.escape(label)}\s*$")
        m = label_rx.search(joined)
        if m:
            rest = joined[m.end():]
            stop = _HEADING_STOP.search(rest)
            block = rest[: stop.start()] if stop else rest
            if block.strip():
                return _norm(block)[:max_chars] or None

        # Inline "Label: ..."
        m2 = re.search(rf"(?is)\b{re.escape(label)}\s*[:\-]\s*(.+?)\n{{2,}}", joined)
        if m2:
            return _norm(m2.group(1))[:max_chars] or None

        return None
    finally:
        doc.close()
