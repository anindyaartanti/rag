"""Konfigurasi terpusat pipeline (plan Bab 17/42).

Target reproduktifitas: semua parameter penting di sini dan diekspor ke
experiment_config.yaml oleh build_vectorstore.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

# --- paths data ---
DATA_DIR = ROOT / "data"
SELECTED_DIR = DATA_DIR / "selected"
PROCESSED_DIR = DATA_DIR / "processed"
CHUNKS_PATH = PROCESSED_DIR / "chunks.jsonl"
CHUNKS_A_PATH = PROCESSED_DIR / "chunks_a.jsonl"
PERSIST_DIR = ROOT / "vectorstore" / "chroma"
EVALUATION_DIR = ROOT / "evaluation"
QUESTIONS_PATH = EVALUATION_DIR / "questions.json"
RETRIEVAL_RESULTS_PATH = EVALUATION_DIR / "retrieval_results.json"
LOGS_DIR = ROOT / "logs"

# --- embedding (plan Bab 6) ---
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
EMBEDDING_DIMENSION = 768
PASSAGE_PREFIX = "passage: "
QUERY_PREFIX = "query: "

# --- vector store (plan Bab 7) ---
COLLECTION_NAME = "rag_ketenagakerjaan"
HNSW_SPACE = "cosine"
EMBED_BATCH_SIZE = 500

# --- retrieval (plan Bab 11) ---
TOP_K_DEFAULT = 5

# --- LLM / Gemini (plan Bab 13) ---
GEMINI_MODEL = "gemini-3.6-flash"
TEMPERATURE = 0.1
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")