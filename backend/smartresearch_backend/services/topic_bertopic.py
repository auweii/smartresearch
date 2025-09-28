from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from ..libs.logger import logger

def _umap_hdbscan_for(n_docs: int) -> Tuple[Optional[object], Optional[object]]:
    try:
        import umap  # type: ignore
        import hdbscan  # type: ignore
    except Exception as e:
        logger.warning(f"UMAP/HDBSCAN unavailable ({e}); using KMeans in BERTopic")
        return None, None

    if n_docs < 10:
        return None, None

    n_neighbors = min(15, max(2, n_docs - 1))
    n_components = min(5, max(2, n_docs - 1))
    umap_model = umap.UMAP(
        n_neighbors=n_neighbors,
        n_components=n_components,
        min_dist=0.0,
        metric="cosine",
        random_state=42,
    )
    min_cluster_size = max(3, int(np.ceil(np.log2(max(4, n_docs)))))
    hdb_model = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,
    )
    return umap_model, hdb_model


def _build_topics_info(topic_model, unique_topics: List[int]) -> List[Dict[str, Any]]:
    topics_info = []
    label_map = {}
    try:
        info_df = topic_model.get_topic_info()
        label_map = {int(row.Topic): str(row.Name) for _, row in info_df.iterrows()}
    except Exception:
        pass

    for t in unique_topics:
        try:
            words = topic_model.get_topic(t) or []
            top_words = [w for (w, _w) in words[:6]]
        except Exception:
            top_words = []
        label = label_map.get(int(t)) or (" / ".join(top_words) if top_words else f"Topic {t}")
        topics_info.append({"topic_id": int(t), "label": label, "top_words": top_words})
    return topics_info


def build_topics_bertopic(
    texts: List[str],
    model_name: str = "all-MiniLM-L6-v2",
    min_topic_size: int = 3,
) -> Dict[str, Any]:
    """
    Cluster texts using BERTopic with robust fallbacks:
      - If UMAP/HDBSCAN produce only outliers (k=0), re-run with KMeans.
      - For very small corpora, use KMeans directly.
    Returns:
      { "labels": np.ndarray[int], "k": int, "topics_info": [...] }
    """
    # Filter empties but keep original indices
    idx_map = [i for i, t in enumerate(texts) if t and t.strip()]
    clean_texts = [texts[i] for i in idx_map]
    n_docs = len(clean_texts)

    if n_docs == 0:
        return {"labels": np.array([], dtype=int), "k": 0, "topics_info": []}

    try:
        from bertopic import BERTopic
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        raise RuntimeError(f"BERTopic dependencies missing: {e}")

    embedder = SentenceTransformer(model_name)

    # 1) Try UMAP+HDBSCAN when reasonable, else KMeans mode
    umap_model, hdb_model = _umap_hdbscan_for(n_docs)
    mode = "umap+hdbscan" if (umap_model and hdb_model) else "kmeans"

    # NOTE: cluster_model is only used when hdbscan_model=None
    cluster_model = None
    if mode == "kmeans":
        # heuristic: k ~ sqrt(n), between 2 and 8 (but < n_docs)
        from sklearn.cluster import KMeans
        k_guess = max(2, min(8, int(np.ceil(np.sqrt(n_docs)))))
        if k_guess >= n_docs:
            k_guess = max(2, n_docs - 1)
        cluster_model = KMeans(n_clusters=k_guess, n_init="auto", random_state=42)

    logger.info(f"BERTopic mode={mode} (n_docs={n_docs})")

    topic_model = BERTopic(
        embedding_model=embedder,
        umap_model=umap_model if mode == "umap+hdbscan" else None,
        hdbscan_model=hdb_model if mode == "umap+hdbscan" else None,
        cluster_model=cluster_model,          # KMeans instance if using KMeans mode
        calculate_probabilities=False,
        verbose=False,
        nr_topics=None,
        min_topic_size=max(min_topic_size, 2),
    )

    topics, _ = topic_model.fit_transform(clean_texts)
    unique_topics = sorted(t for t in set(topics) if t != -1)
    k = len(unique_topics)

    # 2) Fallback if HDBSCAN yielded only outliers (k==0)
    if k == 0:
        logger.warning("All documents marked as outliers; retrying with KMeans clustering")
        from sklearn.cluster import KMeans
        k_guess = max(2, min(8, int(np.ceil(np.sqrt(n_docs)))))
        if k_guess >= n_docs:
            k_guess = max(2, n_docs - 1)

        # Rebuild model forcing KMeans (no UMAP/HDBSCAN)
        topic_model = BERTopic(
            embedding_model=embedder,
            umap_model=None,
            hdbscan_model=None,
            cluster_model=KMeans(n_clusters=k_guess, n_init="auto", random_state=42),
            calculate_probabilities=False,
            verbose=False,
            nr_topics=None,
            min_topic_size=2,
        )
        topics, _ = topic_model.fit_transform(clean_texts)
        unique_topics = sorted(t for t in set(topics) if t != -1)
        k = len(unique_topics)

    topics_info = _build_topics_info(topic_model, unique_topics)

    # Re-expand labels to original length (-1 for empties)
    labels = np.full(len(texts), -1, dtype=int)
    for j, i_orig in enumerate(idx_map):
        labels[i_orig] = int(topics[j])

    return {
        "labels": labels,
        "k": k,
        "topics_info": topics_info,
    }






