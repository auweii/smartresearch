from sklearn.feature_extraction.text import TfidfVectorizer

class Embedder:
    """
    Simple TF-IDF embedder for bag-of-words style document vectors.
    Useful when transformer embeddings are overkill.
    """

    def __init__(self, max_features: int = 5000, ngram_range=(1, 2)):
        self.vectorizer = TfidfVectorizer(max_features=max_features, ngram_range=ngram_range)

    def fit_transform(self, docs):
        """Fit the model on docs and return transformed vectors."""
        return self.vectorizer.fit_transform(docs)

    def transform(self, docs):
        """Transform new documents using the fitted model."""
        return self.vectorizer.transform(docs)
