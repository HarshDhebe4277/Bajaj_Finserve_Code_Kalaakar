# src/embeddings/embedding_model.py

from sentence_transformers import SentenceTransformer
from typing import List

class EmbeddingModel:
    _instance = None
    _model = None
    MODEL_NAME = 'all-MiniLM-L6-v2' # Our chosen embedding model

    def __new__(cls):
        """Ensures only one instance of EmbeddingModel is created (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(EmbeddingModel, cls).__new__(cls)
            print(f"Loading Sentence-Transformer model: {cls.MODEL_NAME}...")
            # Load the model only once
            cls._model = SentenceTransformer(cls.MODEL_NAME)
            print("Embedding model loaded successfully.")
        return cls._instance

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a list of text strings.
        """
        if not self._model:
            raise RuntimeError("Embedding model not loaded. Call EmbeddingModel() first.")
        
        # Sentence-Transformers' encode method handles lists and returns numpy arrays by default.
        # We convert to list of lists (float) for type hinting consistency and JSON serialization.
        embeddings = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()

# You can get the instance and generate embeddings like this:
# embedding_generator = EmbeddingModel()
# embeddings = embedding_generator.get_embeddings(["This is a test sentence.", "Another sentence."])