from sklearn.cluster import KMeans

class Clusterer:
    """
    Wraps sklearn KMeans for simple clustering of embedded document vectors.
    """

    def __init__(self, k=4, random_state=42):
        self.km = KMeans(n_clusters=k, random_state=random_state, n_init=10)

    def fit(self, X):
        """Fit and return predicted cluster labels."""
        return self.km.fit_predict(X).tolist()

    def centroids(self):
        """Return cluster centroids as Python lists."""
        return self.km.cluster_centers_.tolist()
