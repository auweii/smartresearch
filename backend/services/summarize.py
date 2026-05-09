import re
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
import nltk
import os

nltk.data.path.append(os.path.expanduser("~/.nltk_data"))


def clean_summary_text(text: str) -> str:
    text = text.replace("￾", "")
    text = re.sub(r"-\s+", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    # common PDF extraction word breaks
    replacements = {
        "em pirical": "empirical",
        "pro pose": "propose",
        "cul tures": "cultures",
        "misunderstand ings": "misunderstandings",
        "T homas": "Thomas",
        "A quinas": "Aquinas",
    }

    for bad, good in replacements.items():
        text = text.replace(bad, good)

    return text

def extract_abstract_summary(text: str) -> str:
    """
    Extract the real abstract/lead summary section if it exists.
    Handles:
    1. ABSTRACT ... keywords/introduction
    2. No ABSTRACT heading, but lead abstract before Key words
    3. No keywords, but lead abstract before epigraph/first body paragraph
    """
    if not text or not text.strip():
        return ""

    clean = text.replace("\r", "\n")
    first_part = clean[:5000]

    # Case 1: normal ABSTRACT heading
    pattern = re.compile(
        r"\bABSTRACT\b\s*(.*?)(?=\b(Keywords|Keyword|Key words|Introduction|1\.?\s+Introduction)\b)",
        re.IGNORECASE | re.DOTALL,
    )

    match = pattern.search(first_part)
    if match:
        abstract = clean_summary_text(match.group(1))
        if len(abstract.split()) >= 40:
            return abstract

    # Case 2: abstract before Key words / Keywords
    key_match = re.search(
        r"\b(Key words|Keywords|Keyword)\s*:",
        first_part,
        re.IGNORECASE,
    )

    if key_match:
        before_marker = first_part[:key_match.start()]
    else:
        # Case 3: no keyword marker. Stop before obvious body/epigraph start.
        stop_match = re.search(
            r"\n\s*(I can think of no better expression|No one who is wise|1\.?\s+Introduction|Introduction)\b",
            first_part,
            re.IGNORECASE,
        )
        if stop_match:
            before_marker = first_part[:stop_match.start()]
        else:
            before_marker = first_part[:2500]

    lines = [line.strip() for line in before_marker.splitlines() if line.strip()]

    filtered = []
    for line in lines:
        low = line.lower()

        if "@" in line:
            continue
        if "orcid" in low:
            continue
        if "doi" in low or "https://" in low or "http://" in low:
            continue
        if "creative commons" in low or "license" in low:
            continue
        if "downloaded from" in low:
            continue
        if "published under" in low:
            continue
        if "received" in low or "accepted" in low:
            continue
        if "issn" in low:
            continue
        if len(line.split()) <= 3:
            continue
        if line.isupper():
            continue

        # Skip known title/header style lines
        if "philosophy in dialogue" in low:
            continue
        if "example of albert" in low:
            continue
        if "the life of freedom" in low:
            continue
        if "philosophy, the humanities" in low:
            continue
        if "thomas aquinas" in low and len(line.split()) < 12:
            continue

        filtered.append(line)

    start_idx = 0
    for i, line in enumerate(filtered):
        words = line.split()

        if len(words) >= 7:
            letters = [c for c in line if c.isalpha()]
            lower_letters = [c for c in letters if c.islower()]
            lower_ratio = len(lower_letters) / max(len(letters), 1)

            if lower_ratio > 0.55:
                start_idx = i
                break

    candidate = " ".join(filtered[start_idx:])
    candidate = clean_summary_text(candidate)

    if len(candidate.split()) >= 40:
        return candidate

    return ""

def textrankish_summary(text: str, max_sentences: int = 5) -> str:
    """
    A lightweight extractive summarizer inspired by TextRank.
    First tries to use the real abstract section.
    If no abstract is found, it falls back to sentence scoring.
    """
    abstract = extract_abstract_summary(text)
    if abstract:
        return abstract

    sents = sent_tokenize(text)
    if len(sents) <= max_sentences:
        return clean_summary_text(text)

    words = re.findall(r"[A-Za-z]{2,}", text.lower())
    sw = set(stopwords.words("english"))
    freq = {}

    for w in words:
        if w not in sw:
            freq[w] = freq.get(w, 0) + 1

    scored = [
        (
            sum(
                freq.get(w.lower(), 0)
                for w in re.findall(r"[A-Za-z]{2,}", s)
            ) / (len(s.split()) + 1),
            s,
        )
        for s in sents
    ]

    top = sorted(scored, key=lambda t: t[0], reverse=True)[:max_sentences]
    ordered = [s for _, s in sorted(top, key=lambda x: sents.index(x[1]))]

    return clean_summary_text(" ".join(ordered))
