import fitz, re
from typing import Optional, Dict

# Common academic headings (case-insensitive, with optional numbering)
HEADINGS = [
    r"abstract",
    r"introduction",
    r"related work|literature review",
    r"method|methods|methodology",
    r"results|experiments",
    r"discussion",
    r"conclusion|conclusions|summary",
]

def _normalize(s: str) -> str:
    return re.sub(r"[ \t]+", " ", s.strip())

def _find_heading_spans(text: str) -> Dict[str, int]:
    """Return {normalized_heading: char_index} for the first match of each known heading."""
    spans = {}
    for pat in HEADINGS:
        m = re.search(rf"(?im)^\s*(\d+\.?\s+)?({pat})\s*$", text, flags=re.M)
        if m:
            spans[pat] = m.start()
    return spans

def extract_abstract(pdf_path: str, max_pages: int = 20) -> Optional[str]:
    """
    Heuristics:
    - Scan first few pages
    - Try TOC/outline; else regex heading; else 'Abstract:' inline
    - Return up to ~3k chars of the abstract block
    """
    doc = fitz.open(pdf_path)
    try:
        n = min(max_pages, len(doc))
        text = "\n".join((doc[i].get_text("text") or "") for i in range(n))

        # 1) TOC/outline if available
        toc = doc.get_toc(simple=True) or []
        for lvl, title, page in toc[:10]:
            if re.search(r"(?i)\babstract\b", title or "") and page <= max_pages:
                t = doc[page-1].get_text("text") or ""
                return _normalize(t)[:3000] or None

        # 2) Block heading “Abstract” on its own line
        m = re.search(r"(?im)^\s*abstract\s*$", text)
        if m:
            # grab until next heading-ish line
            rest = text[m.end():]
            stop = re.search(r"(?im)^\s*(\d+\.?\s+)?(introduction|related work|method|results|discussion|conclusion)\s*$", rest)
            block = rest[:stop.start()] if stop else rest
            return _normalize(block)[:3000] or None

        # 3) Inline “Abstract:” form
        m = re.search(r"(?is)\babstract\s*[:\-]\s*(.+?)(?:\n{2,}|keywords?:|introduction\b)", text)
        if m:
            return _normalize(m.group(1))[:3000] or None
        return None
    finally:
        doc.close()

def extract_section(pdf_path: str, label: str, scan_pages: int = 8) -> Optional[str]:
    """
    Generic section grabber. label examples: 'introduction', 'conclusion'
    """
    doc = fitz.open(pdf_path)
    try:
        n = min(scan_pages, len(doc))
        text = "\n".join((doc[i].get_text("text") or "") for i in range(n))

        # exact heading line first
        m = re.search(rf"(?im)^\s*(\d+\.?\s+)?({re.escape(label)})\s*$", text)
        if not m:
            # fuzzy OR patterns from our list (e.g., 'related work|literature review')
            m = re.search(rf"(?im)^\s*(\d+\.?\s+)?({label})\s*$", text)
        if m:
            rest = text[m.end():]
            # stop at next heading-like line
            stop = re.search(r"(?im)^\s*(\d+\.?\s+)?([A-Z][A-Za-z ]{{3,}})\s*$", rest)
            block = rest[:stop.start()] if stop else rest
            return _normalize(block)[:6000] or None
        return None
    finally:
        doc.close()
