import re
from typing import List
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
import nltk

# one-time setup (quiet download)
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

def textrankish_summary(text: str, max_sentences: int = 5) -> str:
    """
    A lightweight extractive summarizer inspired by TextRank.
    Scores sentences by term frequency and selects the top few.
    """
    sents = sent_tokenize(text)
    if len(sents) <= max_sentences:
        return text

    # count non-stopword frequencies
    words = re.findall(r"[A-Za-z]{2,}", text.lower())
    sw = set(stopwords.words("english"))
    freq = {}
    for w in words:
        if w not in sw:
            freq[w] = freq.get(w, 0) + 1

    # crude scoring: sum of word frequencies per sentence
    scored = [
        (sum(freq.get(w.lower(), 0) for w in re.findall(r"[A-Za-z]{2,}", s)) / (len(s.split()) + 1), s)
        for s in sents
    ]

    # take top N sentences by score, restore original order
    top = sorted(scored, key=lambda t: t[0], reverse=True)[:max_sentences]
    ordered = [s for _, s in sorted(top, key=lambda x: sents.index(x[1]))]
    return " ".join(ordered)
