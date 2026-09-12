import argparse
import bisect
import json
import logging
import re
import sys
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import DOCS_BY_ID

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN = ROOT / "data" / "selected" / "markdown"
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("chunk_documents")

CHUNK_SIZE = 700
CHUNK_OVERLAP = 150
SEPARATORS = [
    "\n\nBAB ",
    "\n\nBagian ",
    "\n\n### ",
    "\n\n## ",
    "\n\nPasal ",
    "\n\n",
    "\n",
    " ",
    "",
]

HEADING_PATTERNS = [
    ("bab", re.compile(r"^BAB\s+([IVXLC]+)\s*(.*)$")),
    ("bagian", re.compile(r"^Bagian\s+(?:\w+\s+)?(.*)$", re.I)),
    ("pasal", re.compile(r"^Pasal\s+(\d+)\s*(.*)$")),
    ("ayat", re.compile(r"^\((\d+[a-z]?)\)")),
]


def collect_headings(body: str):
    heads = []
    for m in re.finditer(r"^BAB\s+[IVXLC]+.*$|^Bagian\s+.*$|^Pasal\s+\d+.*$|^\(\d+[a-z]?\).*$", body, re.M):
        line = m.group(0)
        offset = m.start()
        for level, pat in HEADING_PATTERNS:
            pm = pat.match(line)
            if pm:
                heads.append((offset, level, line.strip()))
                break
    heads.sort()
    return heads


def locate_chunks(chunks, full):
    pos = []
    p = 0
    for c in chunks:
        probe = c[:90]
        i = full.find(probe, p)
        if i < 0:
            i = full.find(probe[:50])
        if i < 0:
            i = p
        pos.append(i)
        p = max(p, i + max(1, len(c) - CHUNK_OVERLAP))
    return pos


def tag_metadata(chunk_start, heads, base):
    meta = dict(base)
    offs = [h[0] for h in heads]
    idx = bisect.bisect_right(offs, chunk_start) - 1
    if idx >= 0:
        for o, level, label in heads[: idx + 1]:
            meta[level] = label
    return meta


def main() -> None:
    import json as json_mod

    with open(ROOT / "data" / "selected" / "metadata.json", encoding="utf-8") as f:
        metadata = json.load(f)

    parser = argparse.ArgumentParser(description="Chunking dokumen terpilih ke chunks.jsonl")
    parser.add_argument("--baseline", choices=["a", "b"], default="b",
                        help="a: chunk_size=500 overlap=100, b: 700/150 (default b, plan Bab 10.5)")
    parser.add_argument("--out", default=None, help="nama file output di data/processed (default chunks.jsonl / chunks_a.jsonl)")
    args = parser.parse_args()

    chunk_size, chunk_overlap = (500, 100) if args.baseline == "a" else (700, 150)
    out_name = args.out or ("chunks_a.jsonl" if args.baseline == "a" else "chunks.jsonl")

    splitter = RecursiveCharacterTextSplitter(
        separators=SEPARATORS,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        keep_separator=True,
    )

    out_path = PROCESSED / out_name
    records = []
    total_stats = {}

    for doc_id, doc in DOCS_BY_ID.items():
        meta = metadata.get(doc_id, {})
        md = (MARKDOWN / f"{doc_id}.md").read_text(encoding="utf-8")

        head_m = re.search(r"(# PERATURAN .*?)\n## KONTEN\n(.*)$", md, re.S)
        body = head_m.group(2) if head_m else md

        base = {
            "document_id": doc_id,
            "filename": f"{doc_id}.md",
            "source": f"https://peraturan.go.id/id/{doc['slug']}",
            "document_type": meta.get("Jenis/Bentuk Peraturan", ""),
            "document_number": meta.get("Nomor", ""),
            "document_year": meta.get("Tahun", ""),
            "title": meta.get("title", ""),
        }
        heads = collect_headings(body)
        chunks = splitter.split_text(body)
        positions = locate_chunks(chunks, body)

        n = 0
        for i, (chunk, start) in enumerate(zip(chunks, positions)):
            if not chunk.strip():
                continue
            meta_full = tag_metadata(start, heads, base)
            meta_full["chunk_id"] = f"{doc_id}-{i:04d}"
            records.append({"text": chunk, "metadata": meta_full})
            n += 1
        total_stats[doc_id] = n
        logger.info("%-20s chunks=%-4d chars=%d", doc_id, n, len(body))

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json_mod.dumps(rec, ensure_ascii=False) + "\n")

    logger.info("baseline=%s total chunk=%d dokumen=%d -> %s",
                args.baseline, len(records), len(total_stats), out_path)


if __name__ == "__main__":
    main()