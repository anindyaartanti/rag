import json
import logging
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import DOCS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "selected"
OUT.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("fetch_metadata")


def parse_meta_table(html: str) -> dict:
    data = {}
    for row in re.findall(r"<tr><th[^>]*>(.*?)</th><td>(.*?)</td></tr>", html, re.S):
        key = re.sub(r"<[^>]+>", "", row[0]).strip()
        val = re.sub(r"<[^>]+>", "", row[1]).strip()
        val = re.sub(r"\s+", " ", val)
        data[key] = val
    return data


def fetch_page(sess: requests.Session, slug: str) -> str:
    last = None
    for _ in range(5):
        try:
            r = sess.get(f"https://peraturan.go.id/id/{slug}", timeout=90)
            if r.status_code == 200 and "<html" in r.text.lower():
                return r.text
            last = f"status {r.status_code}"
        except Exception as e:
            last = type(e).__name__
        time.sleep(6)
    raise RuntimeError(f"gagal memuat halaman {slug}: {last}")


def main() -> None:
    sess = requests.Session()
    sess.headers["User-Agent"] = "Mozilla/5.0 (RAG-Ketenagakerjaan; +project work)"
    out = {}
    for doc in DOCS:
        html = fetch_page(sess, doc["slug"])
        meta = parse_meta_table(html)
        title_m = re.search(r"<h1>(.*?)</h1>", html, re.S)
        meta["title"] = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else ""
        meta["files"] = re.findall(r'<a href="(/files/[^"]+)"', html)
        meta["page_url"] = f"https://peraturan.go.id/id/{doc['slug']}"
        out[doc["id"]] = meta
        logger.info("%-20s Jenis=%-14s No=%-4s Tahun=%-4s Status=%s | %s",
                    doc["id"], meta.get("Jenis/Bentuk Peraturan", "?"),
                    meta.get("Nomor", "?"), meta.get("Tahun", "?"),
                    meta.get("Status", "?"), meta.get("title", "")[:60])
        time.sleep(3)

    with open(OUT / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    logger.info("Ditulis: %s", OUT / "metadata.json")


if __name__ == "__main__":
    main()