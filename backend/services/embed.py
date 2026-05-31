from sklearn.feature_extraction.text import TfidfVectorizer


class Embedder:
    def __init__(self, max_features: int = 5000, ngram_range=(1, 2)):
        self.vectorizer = TfidfVectorizer(max_features=max_features, ngram_range=ngram_range)

    def fit_transform(self, docs):
        return self.vectorizer.fit_transform(docs)

    def transform(self, docs):
        return self.vectorizer.transform(docs)