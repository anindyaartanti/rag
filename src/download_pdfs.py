import json
import logging
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import DOCS_BY_ID

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "pdf"
RAW.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("download_pdfs")

BASE = "https://peraturan.go.id"


def main() -> None:
    with open(ROOT / "data" / "selected" / "metadata.json", encoding="utf-8") as f:
        metadata = json.load(f)

    sess = requests.Session()
    sess.headers["User-Agent"] = "Mozilla/5.0 (RAG-Ketenagakerjaan; project work)"

    for doc_id, doc in DOCS_BY_ID.items():
        goal = RAW / doc["pdf_file"]
        if goal.exists() and goal.stat().st_size > 0:
            logger.info("SKIP %-20s sudah ada (%d B)", doc_id, goal.stat().st_size)
            continue

        files = metadata.get(doc_id, {}).get("files", [])
        if not files:
            logger.warning("tidak ada file PDF untuk %s", doc_id)
            continue
        url = BASE + files[0]

        for attempt in range(5):
            try:
                r = sess.get(url, timeout=120)
                if r.status_code == 200 and r.content[:4] == b"%PDF" and len(r.content) > 1000:
                    goal.write_bytes(r.content)
                    logger.info("OK   %-20s %d B", doc_id, len(r.content))
                    break
                logger.warning("retry %s: status=%s len=%s", doc_id, r.status_code, len(r.content))
            except Exception as e:
                logger.warning("retry %s: %s", doc_id, type(e).__name__)
            time.sleep(8)
        time.sleep(3)


if __name__ == "__main__":
    main()