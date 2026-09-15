import logging
from pathlib import Path

from config import HNSW_SPACE, PERSIST_DIR, TOP_K_DEFAULT
from embedding import EmbeddingModel
from vectorstore import VectorStore

logger = logging.getLogger("retriever")


class Retriever:
    def __init__(self, persist_dir: Path = PERSIST_DIR, embedder: EmbeddingModel | None = None):
        self.embedder = embedder or EmbeddingModel()
        self.store = VectorStore(persist_dir=persist_dir)
        self.collection = self.store.collection

    def retrieve(self, query: str, k: int = TOP_K_DEFAULT) -> list[dict]:
        qv = self.embedder.embed_query(query)
        res = self.collection.query(query_embeddings=[qv], n_results=k, include=["documents", "metadatas", "distances"])
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        distances = res["distances"][0]
        hits = []
        for text, meta, dist in zip(docs, metas, distances):
            score = 1.0 - float(dist) if HNSW_SPACE == "cosine" else float(dist)
            hits.append({"text": text, "metadata": meta, "score": score})
        return hits

    def debug_retrieve(self, query: str, k: int = TOP_K_DEFAULT) -> list[dict]:
        hits = self.retrieve(query, k=k)
        print("=" * 70)
        print(f"QUERY: {query}\n")
        print(f"RETRIEVED DOCUMENTS (top-{k}):\n")
        for i, h in enumerate(hits, 1):
            m = h["metadata"]
            src = m.get("document_id", "")
            pasal = m.get("pasal", "") or "-"
            bab = m.get("bab", "") or "-"
            ayat = m.get("ayat", "") or "-"
            title = m.get("title", "") or ""
            print(f"[{i}] similar={h['score']:.4f}")
            print(f"    source: {src} | {title}")
            print(f"    {bab} | {pasal} {ayat}")
            print(f"    text: {h['text'][:200].replace(chr(10), ' ')}...")
            print()
        return hits


def retrieve(query: str, k: int = TOP_K_DEFAULT, retriever: Retriever | None = None) -> list[dict]:
    r = retriever or Retriever()
    return r.retrieve(query, k=k)
