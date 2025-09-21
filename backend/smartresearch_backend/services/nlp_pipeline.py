# smartresearch_backend/services/nlp_pipeline.py
from __future__ import annotations
from typing import List, Tuple
import re
import numpy as np

# NLTK + spaCy
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import spacy

# sklearn
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.cluster import KMeans

# ---------- init NLP ----------
NLP = spacy.load("en_core_web_sm")
STOP = set(stopwords.words("english"))
ALNUM = re.compile(r"[A-Za-z0-9]+")

# ---------- basic normalization ----------
def normalize(text: str) -> List[str]:
    toks = [t.lower() for t in word_tokenize(text) if ALNUM.fullmatch(t)]
    toks = [t for t in toks if t not in STOP and len(t) > 2]
    doc = NLP(" ".join(toks))
    return [t.lemma_ for t in doc if t.lemma_ and t.lemma_ not in STOP and len(t.lemma_) > 2]

# ---------- topic modeling (sklearn LDA) ----------
def build_lda_sklearn(docs_tokens: List[List[str]], num_topics: int = 8):
    # safer defaults for small corpora; can be made configurable
    docs_joined = [" ".join(toks) for toks in docs_tokens]
    vectorizer = CountVectorizer(max_df=1.0, min_df=1, max_features=5000)
    X = vectorizer.fit_transform(docs_joined)

    k = min(num_topics, max(1, X.shape[0]))
    lda = LatentDirichletAllocation(n_components=k, learning_method="batch", random_state=42)
    doc_topic = lda.fit_transform(X)  # dense [n_docs, n_topics]
    return lda, vectorizer, doc_topic

def cluster_docs(vectors: np.ndarray, k: int | None = None) -> Tuple[np.ndarray, int]:
    n = len(vectors)
    k = k or max(1, min(5, n))
    labels = KMeans(n_clusters=k, n_init="auto", random_state=42).fit_predict(vectors)
    return labels, k

def topic_label_sklearn(lda: LatentDirichletAllocation, vectorizer: CountVectorizer, topic_id: int, topn: int = 4) -> str:
    terms = np.array(vectorizer.get_feature_names_out())
    comps = lda.components_[topic_id]
    top = terms[np.argsort(comps)[::-1][:topn]]
    return " / ".join(top) if len(top) else f"Topic {topic_id}"

# ---------- extractive summarizer (sklearn TF-IDF) ----------
def _tfidf_sentence_matrix(sentences: List[str]) -> np.ndarray:
    vect = TfidfVectorizer(stop_words="english", max_features=5000)
    X = vect.fit_transform(sentences)
    return X.toarray()

def summarize_extractive_sklearn(text: str, max_sentences: int = 5, max_chars: int | None = 900) -> str:
    """
    Split into sentences, TF-IDF each sentence, score by cosine to centroid,
    take top-N and keep original order. Fast + dependency-light.
    """
    sentences = [s.strip() for s in sent_tokenize(text) if s.strip()]
    if not sentences:
        return ""
    if len(sentences) > 3000:
        sentences = sentences[:3000]

    X = _tfidf_sentence_matrix(sentences)  # shape [n, d]
    if X.size == 0:
        return ""

    centroid = X.mean(axis=0, keepdims=True)             # [1, d]
    norms = (np.linalg.norm(X, axis=1) * np.linalg.norm(centroid)).clip(min=1e-8)
    scores = (X @ centroid.T).ravel() / norms            # cosine similarity

    n = max(1, min(max_sentences, len(sentences)))
    top_idx = np.argsort(-scores)[:n]
    top_idx_sorted = sorted(top_idx.tolist())
    summary = " ".join(sentences[i] for i in top_idx_sorted)

    if max_chars and len(summary) > max_chars:
        out, total = [], 0
        for i in top_idx_sorted:
            s = sentences[i]
            if total + len(s) + 1 > max_chars:
                break
            out.append(s); total += len(s) + 1
        summary = " ".join(out) if out else sentences[top_idx_sorted[0]][:max_chars]

    return summary
