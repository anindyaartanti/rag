import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

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

EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
EMBEDDING_DIMENSION = 768
PASSAGE_PREFIX = "passage: "
QUERY_PREFIX = "query: "

COLLECTION_NAME = "rag_ketenagakerjaan"
HNSW_SPACE = "cosine"
EMBED_BATCH_SIZE = 500

TOP_K_DEFAULT = 5

GEMINI_MODEL = "gemini-3.6-flash"
TEMPERATURE = 0.1
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
