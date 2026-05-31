import re
import requests
from difflib import SequenceMatcher
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
import nltk
import os

nltk.data.path.append(os.path.expanduser("~/.nltk_data"))

# regex for detecting metadata, headers, and boilerplate lines
_NOISE_PATTERNS = re.compile(
    r'@|'
    r'\d+\(\d+\)|'
    r'\.{2,}|'
    r'^\s*\d+\s*$|'
    r'sveučilište|filozofski|'
    r'©|creative commons|'
    r'http[s]?://',
    re.IGNORECASE
)

_PROSE_MIN_WORDS = 8


def clean_summary_text(text: str) -> str:
    text = text.replace("￾", "")
    text = re.sub(r"-\s+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r'\b\d{3}\b', '', text)
    text = re.sub(r'\[[\d\s,]+\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def deduplicate_lines(lines: list) -> list:
    seen = set()
    result = []
    for line in lines:
        normalized = re.sub(r'\d+', '', line.strip().lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        if normalized not in seen:
            seen.add(normalized)
            result.append(line)
    return result


def _is_noise(line: str) -> bool:
    low = line.lower()
    if _NOISE_PATTERNS.search(line):
        return True
    if line.isupper() and len(line.split()) <= 5:
        return True
    if line.startswith("©"):
        return True
    if line.endswith("...") or line.endswith("…"):
        return True
    if "creative commons" in low or "license" in low or "noncommercial" in low:
        return True
    return False


def _fetch_semantic_abstract(doi: str) -> str:
    if not doi:
        return ""
    try:
        res = requests.get(
            f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}",
            params={"fields": "abstract"},
            timeout=5,
        )
        if res.status_code == 200:
            abstract = res.json().get("abstract") or ""
            return abstract.strip()
    except Exception:
        pass
    return ""


def _truncate(text: str, max_sentences: int = 3) -> str:
    sentences = sent_tokenize(text)
    return " ".join(sentences[:max_sentences])


def extract_abstract_summary(text: str) -> str:
    if not text or not text.strip():
        return ""

    clean = text.replace("\r", "\n")
    clean = "\n".join(deduplicate_lines(clean.splitlines()))

    # match explicit ABSTRACT section including spaced variants like A B S T R A C T
    pattern = re.compile(
        r"\bA[\s]*B[\s]*S[\s]*T[\s]*R[\s]*A[\s]*C[\s]*T\b\s*"
        r"(.*?)"
        r"(?=\b(Keywords?|Key\s+words?|Introduction|1\.?\s+Introduction)\b)",
        re.IGNORECASE | re.DOTALL,
    )

    match = pattern.search(clean)
    if match:
        abstract = clean_summary_text(match.group(1))
        if len(abstract.split()) >= 40:
            return _truncate(abstract, max_sentences=5)

    # fallback: extract text before keywords/introduction marker
    doc_len = len(clean)
    search_window = clean[:max(doc_len // 4, 3000)]

    key_match = re.search(r"\b(Key\s*words?|Keywords?)\s*:", search_window, re.IGNORECASE)

    if key_match:
        before_marker = search_window[:key_match.start()]
    else:
        stop_match = re.search(
            r"\n\s*(1\.?\s+Introduction|Introduction)\b",
            search_window,
            re.IGNORECASE,
        )
        before_marker = search_window[:stop_match.start()] if stop_match else search_window[:len(search_window) // 2]

    lines = [l.strip() for l in before_marker.splitlines() if l.strip()]
    lines = deduplicate_lines(lines)
    lines = [l for l in lines if not _is_noise(l) and len(l.split()) > 3]

    if not lines:
        return ""

    candidate = clean_summary_text(" ".join(lines))
    if len(candidate.split()) >= 40:
        return _truncate(candidate)

    return ""


def _extract_body_text(text: str) -> str:
    # find where body prose begins — first line with enough words and no noise
    lines = text.splitlines()
    body_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if (
            len(stripped.split()) >= _PROSE_MIN_WORDS
            and not _is_noise(stripped)
            and not stripped.endswith(":")
        ):
            body_start = i
            break

    return "\n".join(lines[body_start:])


def textrankish_summary(text: str, max_sentences: int = 5, doi: str = None) -> str:
    # prefer Semantic Scholar abstract when DOI is available
    semantic_abstract = _fetch_semantic_abstract(doi) if doi else ""

    local_abstract = extract_abstract_summary(text)

    if semantic_abstract:
        return _truncate(semantic_abstract)

    if local_abstract:
        return local_abstract

    # fall back to TextRank scoring on body text
    body_text = _extract_body_text(text)
    sents = sent_tokenize(body_text)
    sents = deduplicate_lines(sents)
    sents = [s for s in sents if not _is_noise(s) and len(s.split()) >= 5]

    if not sents:
        return clean_summary_text(text[:500])

    if len(sents) <= max_sentences:
        return clean_summary_text(" ".join(sents))

    sw = set(stopwords.words("english"))
    words = re.findall(r"[A-Za-z]{2,}", body_text.lower())
    freq = {}
    for w in words:
        if w not in sw:
            freq[w] = freq.get(w, 0) + 1

    # score by word frequency, penalise very short or very long sentences
    scored = []
    for s in sents:
        s_words = re.findall(r"[A-Za-z]{2,}", s)
        word_score = sum(freq.get(w.lower(), 0) for w in s_words) / (len(s_words) + 1)
        length_penalty = 1.0 if 10 <= len(s_words) <= 40 else 0.5
        scored.append((word_score * length_penalty, s))

    top = sorted(scored, key=lambda t: t[0], reverse=True)[:max_sentences]
    ordered = [s for _, s in sorted(top, key=lambda x: sents.index(x[1]))]

    return clean_summary_text(" ".join(ordered))