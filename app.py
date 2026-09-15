"""CLI Demo: RAG Ketenagakerjaan Indonesia (plan Bab 16 & 62).

Interface (plan Bab 16.1):
  Notebook atau CLI. Jangan mulai dari frontend.

4 skenario demo (plan Bab 62):
  Demo 1 — Simple: "Apa yang dimaksud dengan PKWT?"
  Demo 2 — Natural language: "Kalau seorang pekerja terkena PHK, hak apa saja yang mungkin diperoleh?"
  Demo 3 — Multi-document: "Bagaimana ketentuan PHK berdasarkan regulasi yang tersedia?"
  Demo 4 — Out of scope: "Bagaimana ketentuan pajak perusahaan tambang?"

Disclaimer (plan Bab 14.4):
  Sistem ini merupakan prototype RAG untuk tujuan pembelajaran dan bukan
  pengganti konsultasi hukum.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from prompt import DISCLAIMER, format_sources_footer
from rag_pipeline import RAGPipeline

DEMO_QUESTIONS = [
    {
        "label": "Demo 1 — Simple (retrieval dasar)",
        "question": "Apa yang dimaksud dengan PKWT?",
    },
    {
        "label": "Demo 2 — Natural language (semantic retrieval)",
        "question": "Kalau seorang pekerja terkena PHK, hak apa saja yang mungkin diperoleh?",
    },
    {
        "label": "Demo 3 — Multi-document (beberapa sumber)",
        "question": "Bagaimana ketentuan PHK berdasarkan regulasi yang tersedia?",
    },
    {
        "label": "Demo 4 — Out of scope (di luar knowledge base)",
        "question": "Bagaimana ketentuan pajak perusahaan tambang?",
    },
]


def print_banner():
    print("=" * 60)
    print("  RAG KETENAGAKERJAAN INDONESIA")
    print("  Prototype Retrieval-Augmented Generation")
    print("=" * 60)
    print()
    print(DISCLAIMER)
    print()


def print_result(result: dict, show_retrieved: bool = False):
    print("Asisten:")
    print(result["answer"])
    print()
    print("Sumber:")
    print(format_sources_footer(result["sources"]).replace("Sumber:", "").strip())
    print()

    if show_retrieved:
        print("-" * 60)
        print("RETRIEVED CHUNKS (debug):")
        print("-" * 60)
        for i, chunk in enumerate(result["retrieved_chunks"], 1):
            meta = chunk.get("metadata", {})
            score = chunk.get("score", 0)
            print(
                f"  [{i}] score={score:.4f} | "
                f"{meta.get('document_id', '')} | "
                f"{meta.get('pasal', '')}"
            )
            print(f"      {chunk['text'][:120].replace(chr(10), ' ')}...")
            print()

    print("-" * 60)
    print()


def run_demo_scenarios(pipeline: RAGPipeline):
    """Jalankan 4 skenario demo (plan Bab 62)."""
    print("\n" + "=" * 60)
    print("  DEMO SCENARIOS (plan Bab 62)")
    print("=" * 60)
    print()

    for scenario in DEMO_QUESTIONS:
        print(f"{scenario['label']}")
        print(f"Anda > {scenario['question']}")
        result = pipeline.answer_question(scenario["question"])
        print_result(result, show_retrieved=False)

    print("\nDemo selesai.\n")


def interactive_mode(pipeline: RAGPipeline):
    """Mode interaktif: ketik pertanyaan bebas."""
    print("Ketik pertanyaan (ketik 'quit' untuk keluar, 'debug' untuk toggle debug mode):\n")

    debug_mode = False
    while True:
        try:
            q = input("Anda > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q or q.lower() in ("quit", "exit", "q"):
            break
        if q.lower() == "debug":
            debug_mode = not debug_mode
            print(f"  Debug mode: {'ON' if debug_mode else 'OFF'}\n")
            continue
        result = pipeline.answer_question(q)
        print_result(result, show_retrieved=debug_mode)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="CLI Demo RAG Ketenagakerjaan Indonesia (plan Bab 16/62)"
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Jalankan 4 skenario demo (plan Bab 62)"
    )
    parser.add_argument(
        "-k", type=int, default=5,
        help="Top-k chunks (default 5)"
    )
    args = parser.parse_args()

    print_banner()

    try:
        pipeline = RAGPipeline(top_k=args.k)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if args.demo:
        run_demo_scenarios(pipeline)
    else:
        interactive_mode(pipeline)


if __name__ == "__main__":
    main()