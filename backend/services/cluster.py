from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter


class Clusterer:
    def __init__(self, random_state=42, outlier_threshold=0.20):
        self.random_state = random_state
        self.outlier_threshold = outlier_threshold
        self.labels_ = None
        self.km = None

    def _best_k(self, X):
        n = len(X)
        if n <= 2:
            return n
        max_k = min(6, max(2, n // 2))
        best_k, best_score = 2, -1
        for k in range(2, min(max_k, n) + 1):
            labels = KMeans(n_clusters=k, random_state=self.random_state, n_init=10).fit_predict(X)
            if len(set(labels)) < 2:
                continue
            score = silhouette_score(X, labels)
            if score > best_score:
                best_score = score
                best_k = k
        return best_k

    def fit(self, X):
        k = self._best_k(X)
        self.km = KMeans(n_clusters=k, random_state=self.random_state, n_init=15, max_iter=400)
        labels = self.km.fit_predict(X)
        centroids = self.km.cluster_centers_
        final_labels = labels.copy()

        for i, x in enumerate(X):
            centroid = centroids[labels[i]]
            sim = cosine_similarity([x], [centroid])[0][0]
            if sim < self.outlier_threshold:
                final_labels[i] = -1

        # merge singletons into the outlier group
        counts = Counter(final_labels)
        for label, count in counts.items():
            if label != -1 and count == 1:
                final_labels[final_labels == label] = -1

        self.labels_ = final_labels
        return final_labels

    def centroids(self):
        if self.km is None:
            return []
        return self.km.cluster_centers_.tolist()