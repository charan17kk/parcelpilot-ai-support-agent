from fastembed import TextEmbedding


class LocalEmbeddingService:
    """Small CPU-only embedding adapter shared by ingestion and retrieval."""

    def __init__(self, model_name: str):
        self._model = TextEmbedding(model_name=model_name)

    def embed_one(self, text: str) -> list[float]:
        vector = next(iter(self._model.embed([text])))
        return vector.tolist()
