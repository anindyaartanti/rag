import json
import logging
from pathlib import Path

import chromadb

from config import (
    CHUNKS_PATH,
    COLLECTION_NAME,
    EMBED_BATCH_SIZE,
    HNSW_SPACE,
    PERSIST_DIR,
)

logger = logging.getLogger("vectorstore")


def sanitize_metadata(meta: dict) -> dict:
    out = {}
    for k, v in meta.items():
        if v is None:
            out[k] = ""
        elif isinstance(v, (str, int, float, bool)):
            out[k] = v
        else:
            out[k] = str(v)
    return out


class VectorStore:
    def __init__(self, persist_dir: Path = PERSIST_DIR, collection_name: str = COLLECTION_NAME):
        self.persist_dir = Path(persist_dir)
        self.collection_name = collection_name
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(
            collection_name, metadata={"hnsw:space": HNSW_SPACE}
        )

    def count(self) -> int:
        return self.collection.count()

    def clear(self) -> None:
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            self.collection_name, metadata={"hnsw:space": HNSW_SPACE}
        )
        logger.info("collection '%s' dihapus dan dibuat ulang", self.collection_name)

    def add_record(self, record: dict, embedding: list[float]) -> None:
        self.collection.add(
            ids=[record["metadata"]["chunk_id"]],
            embeddings=[embedding],
            documents=[record["text"]],
            metadatas=[sanitize_metadata(record["metadata"])],
        )

    def add_records(self, records: list[dict], embeddings: list[list[float]]) -> None:
        ids = [r["metadata"]["chunk_id"] for r in records]
        docs = [r["text"] for r in records]
        metas = [sanitize_metadata(r["metadata"]) for r in records]
        for i in range(0, len(records), EMBED_BATCH_SIZE):
            end = min(i + EMBED_BATCH_SIZE, len(records))
            self.collection.add(
                ids=ids[i:end],
                embeddings=embeddings[i:end],
                documents=docs[i:end],
                metadatas=metas[i:end],
            )
            logger.info("added %d/%d", end, len(records))


def load_records(chunks_path: Path = CHUNKS_PATH) -> list[dict]:
    records = []
    with open(chunks_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    logger.info("loaded %d records dari %s", len(records), chunks_path.name)
    return records


def build_index(
    chunks_path: Path = CHUNKS_PATH,
    persist_dir: Path = PERSIST_DIR,
    collection_name: str = COLLECTION_NAME,
    embedder=None,
    force: bool = False,
) -> VectorStore:
    if embedder is None:
        from embedding import EmbeddingModel

        embedder = EmbeddingModel()

    store = VectorStore(persist_dir=persist_dir, collection_name=collection_name)
    if force and store.count() > 0:
        store.clear()

    if store.count() > 0:
        logger.info("index sudah ada (%d vector) di %s -> skip", store.count(), store.persist_dir)
        return store

    records = load_records(chunks_path)
    texts = [r["text"] for r in records]
    embeddings = embedder.embed_passages(texts, batch_size=32)
    store.add_records(records, embeddings)

    actual = store.count()
    expected = len(records)
    if actual != expected:
        raise RuntimeError(f"verifikasi gagal: count={actual} != chunks={expected}")
    logger.info("vektor terverifikasi: count==chunks==%d", actual)
    return store
