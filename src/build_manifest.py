import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import DOCS_BY_ID

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "selected" / "document_manifest.csv"

COLUMNS = [
    "filename",
    "document_type",
    "document_number",
    "document_year",
    "title",
    "domain",
    "selection_reason",
]


def main() -> None:
    with open(ROOT / "data" / "selected" / "metadata.json", encoding="utf-8") as f:
        metadata = json.load(f)

    rows = []
    for doc_id, doc in DOCS_BY_ID.items():
        meta = metadata.get(doc_id, {})
        rows.append({
            "filename": f"{doc_id}.md",
            "document_type": meta.get("Jenis/Bentuk Peraturan", ""),
            "document_number": meta.get("Nomor", ""),
            "document_year": meta.get("Tahun", ""),
            "title": meta.get("title", ""),
            "domain": doc["domain"],
            "selection_reason": doc["selection_reason"],
        })

    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Ditulis {len(rows)} baris ke {OUT}")


if __name__ == "__main__":
    main()