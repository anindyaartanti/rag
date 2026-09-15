import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import LOGS_DIR, TOP_K_DEFAULT
from generator import GeminiGenerator
from prompt import (
    DISCLAIMER,
    build_context,
    build_prompt,
    format_sources_footer,
    parse_sources_from_answer,
)
from retriever import Retriever

logger = logging.getLogger("rag_pipeline")


class RAGPipeline:
    def __init__(self, top_k: int = TOP_K_DEFAULT):
        self.retriever = Retriever()
        self.generator = GeminiGenerator()
        self.top_k = top_k
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

    def answer_question(self, question: str, k: int | None = None) -> dict:
        k = k or self.top_k

        retrieved = self.retriever.retrieve(question, k=k)

        context = build_context(retrieved)

        prompt = build_prompt(question, context)

        answer = self.generator.generate(prompt)

        sources = parse_sources_from_answer(answer, retrieved)

        self._log_query(question, retrieved, prompt, answer, sources)

        return {
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": retrieved,
        }

    def _log_query(
        self,
        question: str,
        retrieved: list[dict],
        prompt: str,
        answer: str,
        sources: list[dict],
    ) -> None:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "question": question,
            "retrieved_document_ids": [
                r["metadata"].get("document_id", "") for r in retrieved
            ],
            "retrieved_scores": [round(r["score"], 4) for r in retrieved],
            "prompt_length": len(prompt),
            "answer": answer,
            "sources": sources,
        }
        log_path = LOGS_DIR / "query_log.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def answer_question(question: str, k: int = TOP_K_DEFAULT) -> dict:
    pipeline = RAGPipeline(top_k=k)
    return pipeline.answer_question(question)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RAG pipeline end-to-end")
    parser.add_argument("question", nargs="?", help="Pertanyaan (jika tidak diisi, masuk mode interaktif)")
    parser.add_argument("-k", type=int, default=TOP_K_DEFAULT, help="Top-k chunks (default 5)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.question:
        result = answer_question(args.question, k=args.k)
        print("\n" + "=" * 60)
        print("JAWABAN:")
        print("=" * 60)
        print(result["answer"])
        print()
        print(format_sources_footer(result["sources"]))
        print(DISCLAIMER)
    else:
        print("=" * 60)
        print("RAG KETENAGAKERJAAN INDONESIA — End-to-End Pipeline")
        print("=" * 60)
        print("Ketik pertanyaan (ketik 'quit' untuk keluar):\n")
        pipeline = RAGPipeline(top_k=args.k)
        while True:
            try:
                q = input("Pertanyaan: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not q or q.lower() in ("quit", "exit", "q"):
                break
            result = pipeline.answer_question(q)
            print("\n" + "-" * 60)
            print("JAWABAN:")
            print(result["answer"])
            print()
            print(format_sources_footer(result["sources"]))
            print(DISCLAIMER)
            print("-" * 60 + "\n")
