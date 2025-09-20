import re
from typing import Optional, Tuple

YEAR_TOKEN = re.compile(r"\b(19|20)\d{2}\b")

def parse_structured(text: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """
    Parse pages that look like:
      Title: ...
      Author: ...
      Year: 2009
    Returns (title, authors, year) or None where not found.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    title = authors = None
    year: Optional[int] = None
    for ln in lines:
        low = ln.lower()
        if low.startswith("title:"):
            title = ln.split(":", 1)[1].strip()
        elif low.startswith("author:"):
            authors = ln.split(":", 1)[1].strip()
        elif low.startswith("year:"):
            m = re.search(r"\d{4}", ln)
            if m:
                try:
                    year = int(m.group(0))
                except Exception:
                    pass
    return title, authors, year

def parse_heuristic(text: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """
    Fallback heuristics for publisher PDFs without explicit labels.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # title: first non-all-caps line with >= 3 words
    title = None
    for ln in lines[:50]:
        if len(ln) >= 10 and len(ln.split()) >= 3 and not ln.isupper():
            title = ln
            break

    # authors: line with comma/semicolon and few digits; or 2–6 Capitalized tokens
    authors = None
    for ln in lines[:100]:
        digits = sum(c.isdigit() for c in ln)
        if ("," in ln or ";" in ln) and digits <= 4 and len(ln) < 200:
            authors = re.sub(r"\s{2,}", " ", ln)
            break
        tokens = ln.split()
        caps = sum(1 for t in tokens if t[:1].isupper())
        if 2 <= caps <= 6 and digits == 0 and len(tokens) <= 12:
            authors = ln
            break

    # year: first 4-digit year token
    year = None
    m = YEAR_TOKEN.search(" ".join(lines[:200]))
    if m:
        try:
            year = int(m.group(0))
        except Exception:
            pass

    return title, authors, year
