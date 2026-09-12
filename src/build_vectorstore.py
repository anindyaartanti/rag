"""CLI: bangun/verifikasi index vector ChromaDB dari chunks.jsonl (plan Bab 24).

Contoh:
  uv run python src/build_vectorstore.py                # build bila belum ada (idempotent)
  uv run python src/build_vectorstore.py --force        # rebuild dari nol
  uv run python src/build_vectorstore.py --check        # verifikasi buka-ulang
  uv run python src/build_vectorstore.py --chunks data/processed/chunks_a.jsonl
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import CHUNKS_PATH, PERSIST_DIR
from embedding import EmbeddingModel
from vectorstore import VectorStore, build_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Bangun/verifikasi ChromaDB dari chunks.jsonl")
    parser.add_argument("--chunks", type=Path, default=CHUNKS_PATH)
    parser.add_argument("--force", action="store_true", help="hapus index lama lalu build ulang")
    parser.add_argument("--check", action="store_true", help="hanya verifikasi index yang sudah ada")
    args = parser.parse_args()

    embedder = EmbeddingModel()
    if args.check:
        store = VectorStore()
        print(f"collection={store.collection_name} count={store.count()} path={store.persist_dir}")
        sample = store.collection.get(limit=1)
        print(f"sample metadata: {sample['metadatas'][0]}")
        return

    store = build_index(
        chunks_path=args.chunks,
        persist_dir=PERSIST_DIR,
        embedder=embedder,
        force=args.force,
    )
    print(f"OK: collection={store.collection_name} count={store.count()} (dimensi {embedder.dimension})")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()