"""Evaluasi retrieval (plan Bab 29-33): Recall@k dokumen + tabel relevance.

Menjalankan retrieve(query, k=5) untuk setiap pertanyaan evaluasi,
menentukan relevansi berdasarkan expected_sources (document_id), menyimpan
hasil detail + ringkasan ke evaluation/retrieval_results.json.
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import QUESTIONS_PATH, RETRIEVAL_RESULTS_PATH
from retriever import Retriever

logger = logging.getLogger("evaluate_retrieval")


def main(k: int = 5) -> None:
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))["questions"]
    retriever = Retriever()

    details = []
    hits = 0
    set_recall_sum = 0.0
    n_in_domain = 0

    for q in questions:
        qid = q["id"]
        expected = set(q.get("expected_sources") or [])
        retrieved = retriever.retrieve(q["question"], k=k)

        rows = []
        seen = set()
        for rank, hit in enumerate(retrieved, 1):
            did = hit["metadata"].get("document_id", "")
            rows.append({
                "rank": rank,
                "document_id": did,
                "chunk_id": hit["metadata"].get("chunk_id", ""),
                "pasal": hit["metadata"].get("pasal", ""),
                "score": round(hit["score"], 4),
            })
            seen.add(did)

        found = sorted(expected & seen)
        hit_flag = bool(found)
        if expected:
            n_in_domain += 1
            if hit_flag:
                hits += 1
            set_recall_sum += len(found) / len(expected)

        details.append({
            "id": qid,
            "difficulty": q["difficulty"],
            "question": q["question"],
            "expected_sources": sorted(expected),
            "found_sources": found,
            "hit_top_k": hit_flag,
            "recall_support": round(len(found) / len(expected), 4) if expected else None,
            "retrieved": rows,
        })

    recall_at_k = hits / n_in_domain if n_in_domain else 0.0
    set_recall = set_recall_sum / n_in_domain if n_in_domain else 0.0

    by_difficulty = {}
    for d in ("easy", "medium", "hard"):
        sub = [x for x in details if x["difficulty"] == d]
        h = sum(1 for x in sub if x["hit_top_k"])
        by_difficulty[d] = {"n": len(sub), "hits": h} if sub else {"n": 0, "hits": 0}

    summary = {
        "model": retriever.embedder.model_name,
        "embedding_dimension": retriever.embedder.dimension,
        "chunks_total": retriever.store.count(),
        "top_k": k,
        "metric": "Recall@k (document-level, expected_sources di top-k)",
        "total_questions": len(details),
        "in_domain_questions": n_in_domain,
        "recall_at_k": round(recall_at_k, 4),
        "mean_recall_support": round(set_recall, 4),
        "by_difficulty": by_difficulty,
    }

    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "config": {
            "embedding_model": retriever.embedder.model_name,
            "vectorstore": str(retriever.store.persist_dir),
            "collection": retriever.store.collection_name,
            "top_k": k,
            "metric": "Recall@k document-level",
        },
        "summary": summary,
        "questions": details,
    }

    RETRIEVAL_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RETRIEVAL_RESULTS_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    logger.info("=== RINGKASAN RETRIEVAL EVALUATION ===")
    logger.info("Recall@%d = %d/%d = %.1f%%", k, hits, n_in_domain, recall_at_k * 100)
    logger.info("Mean recall support (rasio expected source ditemukan) = %.2f", set_recall)
    for d, s in by_difficulty.items():
        logger.info("  %-8s n=%d hit=%d", d, s["n"], s["hits"])
    logger.info("hasil -> %s", RETRIEVAL_RESULTS_PATH)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main(k=5)