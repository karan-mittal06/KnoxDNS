import numpy as np
import torch
import re
import tldextract
from urllib.parse import urlparse
from sklearn.neighbors import NearestNeighbors
from torch_geometric.data import Data
import pickle
import joblib
import os
import pandas as pd

class URLProcessor:
    def __init__(self, tfidf_vectorizer_path="tfidf_vectorizer.pkl", 
                 tfidf_reducer_path="tfidf_reducer.pkl",
                 embedding_reducer_path="embedding_reducer.pkl",
                 stored_features_path=None):
      
        with open(tfidf_vectorizer_path, "rb") as f:
            self.tfidf_vectorizer = pickle.load(f)
        with open(tfidf_reducer_path, "rb") as f:
            self.tfidf_reducer = pickle.load(f)
        with open(embedding_reducer_path, "rb") as f:
            self.embedding_reducer = pickle.load(f)

        if stored_features_path and os.path.exists(stored_features_path):
            self.stored_features = np.load(stored_features_path)
        else:
            self.stored_features = None

    def extract_lexical_features(self, url):
        """Extract lexical features from a single URL."""
        return [
            len(url),  
            sum(c.isdigit() for c in url),  
            url.count('-'),
            url.count('_'), 
            url.count('.'),  
            url.count('/'),  
            url.count('?'),  
            url.count('='), 
            url.count('@'),  
            len(set(url))  
        ]

    def extract_domain_features(self, url):
        """Extract domain-related features from a single URL."""
        ext = tldextract.extract(url)
        domain, subdomain, tld = ext.domain, ext.subdomain, ext.suffix

        phishing_keywords = ['login', 'secure', 'banking', 'account', 'update', 'verify']
        contains_phishing_words = int(any(word in url for word in phishing_keywords))

        return [
            len(domain), len(subdomain), len(tld), contains_phishing_words, 
            domain.count('-'), domain.count('.'), domain.count('/'), domain.count('_'), 
            subdomain.count('-'), subdomain.count('.') 
        ]

    def transform_tfidf(self, url):
        """Transforms a single URL into TF-IDF reduced vector (uses trained TF-IDF & SVD models)."""
        tfidf_matrix = self.tfidf_vectorizer.transform([url])
        return self.tfidf_reducer.transform(tfidf_matrix)

    def transform_embeddings(self, url):
        """Generates a simulated embedding for the URL and reduces it using PCA."""
        embedding_vector = np.random.rand(1, 100) 
        return self.embedding_reducer.transform(embedding_vector)

    def transform_url(self, url):
        """Extracts all features from a single URL and returns a combined feature vector."""
        lexical_features = np.array(self.extract_lexical_features(url)).reshape(1, -1)
        domain_features = np.array(self.extract_domain_features(url)).reshape(1, -1)
        tfidf_features = self.transform_tfidf(url)
        embedding_features = self.transform_embeddings(url)

        return np.hstack([lexical_features, domain_features, tfidf_features, embedding_features])


