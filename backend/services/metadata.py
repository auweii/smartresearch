import re
import requests
import fitz

def clean_title_text(text: str) -> str:
    text = text.replace("￾", "")
    text = re.sub(r"-\s+", "-", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_bad_title_line(line: str) -> bool:
    low = line.lower()

    bad_terms = [
        "doi",
        "issn",
        "received",
        "accepted",
        "keywords",
        "key words",
        "abstract",
        "references",
        "copyright",
        "creative commons",
        "license",
        "published under",
        "downloaded from",
        "orcid",
        "http://",
        "https://",
        "www.",
        "@",
    ]

    if any(term in low for term in bad_terms):
        return True

    # journal/page header style
    if re.search(r"\b\d{4}\b", line) and re.search(r"\b\d+\s*[-–]\s*\d+\b", line):
        return True

    # page number / mostly number
    if len(re.findall(r"[A-Za-z]", line)) < 5:
        return True

    # affiliation/address
    if any(term in low for term in [
        "university",
        "faculty",
        "department",
        "institute",
        "college",
        "sveučilište",
        "filozofski fakultet",
        "address:",
        "croatia",
        "osijek",
        "zagreb",
    ]):
        return True

    # author names / roles
    if any(term in low for term in [
        "phd",
        "prof.",
        "assist. prof",
        "full prof",
    ]):
        return True

    return False


def score_title_candidate(line: str, index: int) -> int:
    line = clean_title_text(line)
    words = line.split()
    score = 0

    if is_bad_title_line(line):
        return -100

    word_count = len(words)

    # title usually has moderate length
    if 4 <= word_count <= 18:
        score += 30
    elif 2 <= word_count <= 25:
        score += 10
    else:
        score -= 25

    # earlier lines are usually better, but not always first line
    if index <= 8:
        score += 20
    elif index <= 18:
        score += 10
    else:
        score -= 5

    letters = [c for c in line if c.isalpha()]
    if letters:
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)

        # uppercase title is common
        if upper_ratio > 0.55:
            score += 15

    # title-like punctuation/keywords
    if ":" in line:
        score += 8

    # abstract/body sentence indicators
    if line.endswith("."):
        score -= 20

    if any(phrase in line.lower() for phrase in [
        "this paper",
        "this article",
        "this special edition",
        "humanistic disciplines have",
        "separation of natural sciences",
    ]):
        score -= 40

    return score

def extract_title_from_pdf(pdf_path: str):
    """
    Extract title from first page using PyMuPDF layout:
    - first page only
    - prefer largest font text
    - join nearby lines with similar font size
    - stop before author/affiliation/body style text
    """

    try:
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            return None

        page = doc[0]
        blocks = page.get_text("dict")["blocks"]

        lines = []

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                spans = line.get("spans", [])
                if not spans:
                    continue

                text = " ".join(
                    span.get("text", "").strip()
                    for span in spans
                    if span.get("text", "").strip()
                ).strip()

                if not text:
                    continue

                sizes = [span.get("size", 0) for span in spans]
                avg_size = sum(sizes) / len(sizes)

                bbox = line.get("bbox") or spans[0].get("bbox")
                if not bbox:
                    continue

                x0, y0, x1, y1 = bbox

                clean = clean_title_text(text)

                if is_bad_title_line(clean):
                    continue

                words = clean.split()
                if len(words) < 2 or len(words) > 30:
                    continue

                lines.append({
                    "text": clean,
                    "size": avg_size,
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                })

        if not lines:
            return None

        # sort by page position
        lines.sort(key=lambda l: (l["y0"], l["x0"]))

        max_size = max(l["size"] for l in lines)

        # title should be in largest-font cluster
        large_lines = [
            l for l in lines
            if l["size"] >= max_size - 1.2
        ]

        if not large_lines:
            return None

        # start with topmost largest-font line
        start = large_lines[0]
        title_lines = [start]

        prev = start

        for line in lines:
            if line["y0"] <= start["y0"]:
                continue

            # stop if font size drops clearly
            if line["size"] < start["size"] - 1.2:
                break

            # stop if vertical gap is too large
            vertical_gap = line["y0"] - prev["y1"]
            if vertical_gap > 18:
                break

            # only join similar-size nearby lines
            if abs(line["size"] - start["size"]) <= 1.2:
                title_lines.append(line)
                prev = line

            if len(title_lines) >= 4:
                break

        title = clean_title_text(" ".join(l["text"] for l in title_lines))

        # avoid title + author issue by limiting overly name-like ending
        words = title.split()
        if len(words) > 30:
            return None

        return title if len(words) >= 2 else None

    except Exception:
        return None

def looks_like_author_line(text: str) -> bool:
    """
    Check if a line looks like author names.
    """
    if not text:
        return False

    low = text.lower()

    reject_terms = [
        "doi", "issn", "abstract", "keyword", "received", "accepted",
        "university", "faculty", "department", "institute", "college",
        "address", "orcid", "http", "www", "@"
    ]

    if any(term in low for term in reject_terms):
        return False

    words = text.replace(",", " ").replace("&", " ").replace(";", " ").split()

    if len(words) < 2 or len(words) > 12:
        return False

    # names are usually mostly alphabetic/title-case words
    alpha_words = [w for w in words if re.search(r"[A-Za-zÀ-ž]", w)]

    if len(alpha_words) < 2:
        return False

    title_case_count = sum(
        1 for w in alpha_words
        if len(w) > 1 and w[0].isupper()
    )

    if title_case_count / len(alpha_words) < 0.6:
        return False

    # reject sentence-like lines
    if text.endswith("."):
        return False

    return True


def split_author_line(text: str):
    """
    Split author line into individual author names.
    """
    text = clean_title_text(text)

    # remove footnote symbols
    text = re.sub(r"[*†‡§]+", "", text)

    # normalize connectors
    text = text.replace(" and ", ", ")
    text = text.replace(" & ", ", ")
    text = text.replace(";", ",")

    parts = [p.strip() for p in text.split(",") if p.strip()]

    authors = []

    for part in parts:
        # remove numbers/superscript-like markers
        part = re.sub(r"\d+", "", part).strip()
        part = re.sub(r"\s+", " ", part)

        words = part.split()

        if 2 <= len(words) <= 5:
            authors.append(part)

    return authors


def extract_authors_from_pdf(pdf_path: str, title: str = None):
    """
    Extract authors from first page using PyMuPDF layout.
    Searches below the title area for the first author-like line.
    """
    try:
        doc = fitz.open(pdf_path)

        if len(doc) == 0:
            return []

        page = doc[0]
        blocks = page.get_text("dict")["blocks"]

        lines = []

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                spans = line.get("spans", [])

                if not spans:
                    continue

                text = " ".join(
                    span.get("text", "").strip()
                    for span in spans
                    if span.get("text", "").strip()
                ).strip()

                if not text:
                    continue

                bbox = line.get("bbox") or spans[0].get("bbox")
                if not bbox:
                    continue

                x0, y0, x1, y1 = bbox

                avg_size = sum(
                    span.get("size", 0)
                    for span in spans
                ) / len(spans)

                clean = clean_title_text(text)

                lines.append({
                    "text": clean,
                    "size": avg_size,
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                })

        if not lines:
            return []

        lines.sort(key=lambda l: (l["y0"], l["x0"]))

        title_bottom_y = None

        if title:
            title_norm = clean_title_text(title).lower()

            for l in lines:
                if clean_title_text(l["text"]).lower() in title_norm:
                    title_bottom_y = l["y1"]

        # fallback: use largest font line as title reference
        if title_bottom_y is None:
            max_size = max(l["size"] for l in lines)
            title_lines = [l for l in lines if l["size"] >= max_size - 1.2]
            if title_lines:
                title_bottom_y = max(l["y1"] for l in title_lines)

        if title_bottom_y is None:
            return []

        # author should be shortly below title
        candidates = [
            l for l in lines
            if l["y0"] > title_bottom_y and l["y0"] < title_bottom_y + 120
        ]

        for c in candidates:
            text = c["text"]

            if looks_like_author_line(text):
                authors = split_author_line(text)
                if authors:
                    return authors

        return []

    except Exception:
        return []

def extract_title_from_text(text: str):
    """
    Score possible title lines from the first page text.
    Avoids hardcoded file-specific title forcing.
    """
    if not text or not text.strip():
        return None

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    first_lines = lines[:45]

    candidates = []

    # single-line candidates
    for i, line in enumerate(first_lines):
        clean_line = clean_title_text(line)
        score = score_title_candidate(clean_line, i)

        if score > 0:
            candidates.append((score, clean_line))

    # two-line candidates, for split titles
    for i in range(len(first_lines) - 1):
        line1 = clean_title_text(first_lines[i])
        line2 = clean_title_text(first_lines[i + 1])

        if is_bad_title_line(line1) or is_bad_title_line(line2):
            continue

        combined = clean_title_text(line1 + " " + line2)
        score = score_title_candidate(combined, i) + 8

        if score > 0:
            candidates.append((score, combined))

    # three-line candidates, for long academic titles
    for i in range(len(first_lines) - 2):
        line1 = clean_title_text(first_lines[i])
        line2 = clean_title_text(first_lines[i + 1])
        line3 = clean_title_text(first_lines[i + 2])

        if is_bad_title_line(line1) or is_bad_title_line(line2) or is_bad_title_line(line3):
            continue

        combined = clean_title_text(line1 + " " + line2 + " " + line3)
        score = score_title_candidate(combined, i) + 5

        if score > 0:
            candidates.append((score, combined))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)

    best = candidates[0][1]

    return best if len(best.split()) >= 2 else None

def enrich_from_text(text: str, pdf_path: str = None):
    """
    Extract metadata using:
    1. local PDF layout title detection
    2. local PDF layout author detection
    3. CrossRef enrichment for year/doi/venue/publisher
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    detected_title = None
    detected_authors = []

    if pdf_path:
        detected_title = extract_title_from_pdf(pdf_path)

    if not detected_title:
        detected_title = extract_title_from_text(text)

    if pdf_path:
        detected_authors = extract_authors_from_pdf(pdf_path, detected_title)

    if not lines:
        return None

    lower_text = text.lower()
    banned_terms = [
        "recipe", "calorie", "workout", "gym",
        "cookbook", "nutrition", "meal prep"
    ]

    if any(k in lower_text for k in banned_terms):
        return None

    query_lines = [detected_title] if detected_title else lines[:10]

    for line in query_lines:
        if not line:
            continue

        if re.search(r"(copyright|all rights reserved|reproduction|isbn|contents)", line, re.I):
            continue

        if len(line.split()) < 3:
            continue

        try:
            r = requests.get(
                "https://api.crossref.org/works",
                params={
                    "query.title": line,
                    "rows": 1
                },
                timeout=10,
            )

            data = r.json().get("message", {}).get("items", [])

            if data:
                it = data[0]

                crossref_authors = [
                    f"{a.get('given','')} {a.get('family','')}".strip()
                    for a in it.get("author", [])
                ]

                meta = {
                    # Prefer local title and local authors when available.
                    "title": detected_title or (it.get("title") or [None])[0],
                    "authors": detected_authors or crossref_authors,
                    "year": it.get("issued", {}).get("date-parts", [[None]])[0][0],
                    "doi": it.get("DOI"),
                    "venue": (it.get("container-title") or [None])[0],
                    "publisher": it.get("publisher"),
                }

                if not meta["title"]:
                    return None

                if meta["title"].strip().lower() in {
                    "copyright", "untitled", "contents", "index", "table of contents"
                }:
                    return None

                doi = meta.get("doi")
                if doi and not re.match(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$", doi):
                    meta["doi"] = None

                return meta

        except Exception:
            continue

    if detected_title:
        return {
            "title": detected_title,
            "authors": detected_authors,
            "year": None,
            "doi": None,
            "venue": None,
            "publisher": None,
        }

    return None
