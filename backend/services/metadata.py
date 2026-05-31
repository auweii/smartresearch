import re
import requests
import fitz
from difflib import SequenceMatcher


def clean_title_text(text: str) -> str:
    text = text.replace("￾", "")
    text = re.sub(r"-\s+", "-", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_bad_title_line(line: str) -> bool:
    low = line.lower()

    bad_terms = [
        "doi", "issn", "received", "accepted", "keywords", "key words",
        "abstract", "references", "copyright", "creative commons", "license",
        "published under", "downloaded from", "orcid", "http://", "https://",
        "www.", "@", "journal", "zoology", "bulletin", "proceedings", "transactions"
    ]

    if any(term in low for term in bad_terms):
        return True
    if re.search(r"\b\d{4}\b", line) and re.search(r"\b\d+\s*[-–]\s*\d+\b", line):
        return True
    if len(re.findall(r"[A-Za-z]", line)) < 5:
        return True
    if re.search(r"arxiv:\d+\.\d+", line, re.IGNORECASE):
        return True
    if any(term in low for term in [
        "university", "faculty", "department", "institute", "college",
        "sveučilište", "filozofski fakultet", "address:", "croatia", "osijek", "zagreb",
    ]):
        return True
    if any(term in low for term in ["phd", "prof.", "assist. prof", "full prof"]):
        return True
    if line.isupper() and len(line.split()) <= 4:
        return True

    return False


def score_title_candidate(line: str, index: int) -> int:
    line = clean_title_text(line)
    words = line.split()
    score = 0

    if is_bad_title_line(line):
        return -100

    word_count = len(words)

    if 4 <= word_count <= 18:
        score += 30
    elif 2 <= word_count <= 25:
        score += 10
    else:
        score -= 25

    if index <= 8:
        score += 20
    elif index <= 18:
        score += 10
    else:
        score -= 5

    letters = [c for c in line if c.isalpha()]
    if letters:
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if upper_ratio > 0.55:
            score += 15

    if ":" in line:
        score += 8
    if line.endswith("."):
        score -= 20
    if any(phrase in line.lower() for phrase in [
        "this paper", "this article", "this special edition",
        "humanistic disciplines have", "separation of natural sciences",
    ]):
        score -= 40

    return score


def _looks_like_person_name(text: str) -> bool:
    words = text.split()
    if len(words) > 5:
        return False
    alpha_words = [w for w in words if w.isalpha()]
    if len(alpha_words) != len(words):
        return False
    if not all(w[0].isupper() for w in alpha_words):
        return False
    connecting = {"in", "on", "of", "the", "a", "an", "and", "with", "for", "to", "is", "are"}
    if any(w.lower() in connecting for w in words):
        return False
    return True


def extract_title_from_pdf(pdf_path: str):
    try:
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            return None

        page = doc[0]
        page_height = page.rect.height
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

                if y0 < page_height * 0.03:
                    continue

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

        lines.sort(key=lambda l: (l["y0"], l["x0"]))

        max_size = max(l["size"] for l in lines)
        large_lines = [l for l in lines if l["size"] >= max_size - 1.2]

        if not large_lines:
            return None

        start = large_lines[0]
        title_lines = [start]
        prev = start

        for line in lines:
            if line["y0"] <= start["y0"]:
                continue
            if line["size"] < start["size"] - 1.2:
                break
            vertical_gap = line["y0"] - prev["y1"]
            if vertical_gap > 18:
                break
            if _looks_like_person_name(line["text"]):
                break
            if abs(line["size"] - start["size"]) <= 1.2:
                title_lines.append(line)
                prev = line
            if len(title_lines) >= 4:
                break

        title = clean_title_text(" ".join(l["text"] for l in title_lines))
        words = title.split()

        if len(words) > 30:
            return None
        if _looks_like_person_name(title):
            return None

        return title if len(words) >= 2 else None

    except Exception:
        return None


def looks_like_author_line(text: str) -> bool:
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

    alpha_words = [w for w in words if re.search(r"[A-Za-zÀ-ž]", w)]

    if len(alpha_words) < 2:
        return False

    title_case_count = sum(
        1 for w in alpha_words
        if len(w) > 1 and w[0].isupper()
    )

    if title_case_count / len(alpha_words) < 0.6:
        return False
    if text.endswith("."):
        return False

    return True


def split_author_line(text: str):
    text = clean_title_text(text)
    text = re.sub(r"[*†‡§]+", "", text)
    text = text.replace(" and ", ", ").replace(" & ", ", ").replace(";", ",")

    parts = [p.strip() for p in text.split(",") if p.strip()]
    authors = []

    for part in parts:
        part = re.sub(r"\d+", "", part).strip()
        part = re.sub(r"\s+", " ", part)
        words = part.split()
        if 2 <= len(words) <= 5:
            authors.append(part)

    return authors


def extract_authors_from_pdf(pdf_path: str, title: str = None):
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
                avg_size = sum(span.get("size", 0) for span in spans) / len(spans)
                clean = clean_title_text(text)

                lines.append({
                    "text": clean,
                    "size": avg_size,
                    "x0": x0, "y0": y0,
                    "x1": x1, "y1": y1,
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

        if title_bottom_y is None:
            max_size = max(l["size"] for l in lines)
            title_lines = [l for l in lines if l["size"] >= max_size - 1.2]
            if title_lines:
                title_bottom_y = max(l["y1"] for l in title_lines)

        if title_bottom_y is None:
            return []

        candidates = [
            l for l in lines
            if l["y0"] > title_bottom_y and l["y0"] < title_bottom_y + 120
        ]

        all_authors = []
        for c in candidates:
            if looks_like_author_line(c["text"]):
                all_authors.extend(split_author_line(c["text"]))

        return list(dict.fromkeys(all_authors))

    except Exception:
        return []


def extract_title_from_text(text: str):
    if not text or not text.strip():
        return None

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    first_lines = lines[:45]
    candidates = []

    for i, line in enumerate(first_lines):
        clean_line = clean_title_text(line)
        score = score_title_candidate(clean_line, i)
        if score > 0:
            candidates.append((score, clean_line))

    # 2-line combinations
    for i in range(len(first_lines) - 1):
        line1 = clean_title_text(first_lines[i])
        line2 = clean_title_text(first_lines[i + 1])
        if is_bad_title_line(line1) or is_bad_title_line(line2):
            continue
        combined = clean_title_text(line1 + " " + line2)
        score = score_title_candidate(combined, i) + 8
        if score > 0:
            candidates.append((score, combined))

    # 3-line combinations
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

    # 4-line combinations — handles multi-line titles in two-column layouts
    for i in range(len(first_lines) - 3):
        line1 = clean_title_text(first_lines[i])
        line2 = clean_title_text(first_lines[i + 1])
        line3 = clean_title_text(first_lines[i + 2])
        line4 = clean_title_text(first_lines[i + 3])
        if any(is_bad_title_line(l) for l in [line1, line2, line3, line4]):
            continue
        combined = clean_title_text(line1 + " " + line2 + " " + line3 + " " + line4)
        score = score_title_candidate(combined, i) + 3
        if score > 0:
            candidates.append((score, combined))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    best = candidates[0][1]
    return best if len(best.split()) >= 2 else None


def _is_plausible(crossref_title: str, local_title: str) -> bool:
    if not crossref_title or not local_title:
        return False
    sim = SequenceMatcher(None, crossref_title.lower(), local_title.lower()).ratio()
    return sim > 0.7


def _query_crossref(title: str, detected_authors: list) -> dict:
    try:
        r = requests.get(
            "https://api.crossref.org/works",
            params={"query.title": title, "rows": 1},
            timeout=3,
        )
        data = r.json().get("message", {}).get("items", [])

        if not data:
            return None

        it = data[0]
        crossref_title = (it.get("title") or [None])[0]

        if not _is_plausible(crossref_title, title):
            return None

        crossref_authors = [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in it.get("author", [])
        ]

        doi = it.get("DOI")
        if doi and not re.match(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$", doi):
            doi = None

        return {
            "title": crossref_title or title,
            "authors": detected_authors or crossref_authors,
            "year": it.get("issued", {}).get("date-parts", [[None]])[0][0],
            "doi": doi,
            "venue": (it.get("container-title") or [None])[0],
            "publisher": it.get("publisher"),
        }

    except Exception:
        return None


def enrich_from_text(text: str, pdf_path: str = None):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    detected_title = None
    detected_authors = []

    if pdf_path:
        detected_title = extract_title_from_pdf(pdf_path)

    if not detected_title:
        detected_title = extract_title_from_text(text)

    # extract DOI from first 2 pages only to avoid matching reference DOIs
    detected_doi = None
    if pdf_path:
        try:
            doc = fitz.open(pdf_path)
            for page in list(doc)[:2]:
                page_text = page.get_text()
                doi_match = re.search(
                    r'(?:^|\n)\s*DOI:\s*(10\.\d{4,9}/\S+)',
                    page_text,
                    re.IGNORECASE | re.MULTILINE
                )
                if doi_match:
                    detected_doi = doi_match.group(1).rstrip('.,;)')
                    break
            doc.close()
        except Exception:
            pass

    if pdf_path:
        detected_authors = extract_authors_from_pdf(pdf_path, detected_title)

    if not lines:
        return None

    if detected_title:
        result = _query_crossref(detected_title, detected_authors)
        if result:
            if not result.get("doi") and detected_doi:
                result["doi"] = detected_doi
            return result

    # fallback: try first few lines as title queries
    for line in lines[:10]:
        if not line or len(line.split()) < 3:
            continue
        if re.search(r"(copyright|all rights reserved|reproduction|isbn|contents)", line, re.I):
            continue
        result = _query_crossref(line, detected_authors)
        if result:
            if not result.get("doi") and detected_doi:
                result["doi"] = detected_doi
            return result

    if detected_title:
        return {
            "title": detected_title,
            "authors": detected_authors,
            "year": None,
            "doi": detected_doi,
            "venue": None,
            "publisher": None,
        }

    return None