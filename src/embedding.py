from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL, EMBEDDING_DIMENSION, PASSAGE_PREFIX, QUERY_PREFIX


class EmbeddingModel:
    def __init__(self, model_name: str = EMBEDDING_MODEL, device=None, batch_size: int = 32):
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = SentenceTransformer(model_name, device=device)

    @property
    def dimension(self) -> int:
        return EMBEDDING_DIMENSION

    def embed_passages(self, texts: list[str], batch_size: int | None = None) -> list[list[float]]:
        texts = [PASSAGE_PREFIX + t for t in texts]
        return self._model.encode(
            texts, batch_size=batch_size or self.batch_size, normalize_embeddings=True, show_progress_bar=True
        )

    def embed_query(self, query: str) -> list[float]:
        return self._model.encode([QUERY_PREFIX + query], normalize_embeddings=True, show_progress_bar=True)[0]

    def embed_queries(self, queries: list[str], batch_size: int | None = None) -> list[list[float]]:
        queries = [QUERY_PREFIX + q for q in queries]
        return self._model.encode(
            queries, batch_size=batch_size or self.batch_size, normalize_embeddings=True, show_progress_bar=True
        )
