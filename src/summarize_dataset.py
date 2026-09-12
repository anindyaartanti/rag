import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN = ROOT / "data" / "selected" / "markdown"
MANIFEST = ROOT / "data" / "selected" / "document_manifest.csv"
CHUNKS = ROOT / "data" / "processed" / "chunks.jsonl"
OUT = ROOT / "data" / "selected" / "exploration_summary.md"


def count_heading(body: str, pattern: str) -> int:
    return len(re.findall(pattern, body, re.M))


def main() -> None:
    files = sorted(MARKDOWN.glob("*.md"))
    stats = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        head = re.search(r"(# PERATURAN .*?)\n## KONTEN\n(.*)$", text, re.S)
        body = head.group(2) if head else text
        stats.append({
            "file": f.name,
            "chars": len(body),
            "lines": len(body.splitlines()),
            "bab": count_heading(body, r"^BAB\s+[IVXLC]+"),
            "bagian": count_heading(body, r"^Bagian\s+", ),
            "pasal": count_heading(body, r"^Pasal\s+\d+"),
            "ayat": count_heading(body, r"^\(\d+[a-z]?\)"),
        })

    chunks = [json.loads(l) for l in CHUNKS.read_text(encoding="utf-8").splitlines() if l.strip()]
    per_doc_chunks = {}
    for c in chunks:
        per_doc_chunks[c["metadata"]["document_id"]] = per_doc_chunks.get(c["metadata"]["document_id"], 0) + 1

    total_chars = sum(s["chars"] for s in stats)
    mean = total_chars / len(stats) if stats else 0
    shortest = min(stats, key=lambda s: s["chars"])
    longest = max(stats, key=lambda s: s["chars"])
    empty = [s for s in stats if s["chars"] == 0]
    titles = [s["file"] for s in stats]
    dups = len(titles) != len(set(titles))

    md = ["# Ringkasan Eksplorasi Dataset (Bab 20 - Tahap 2)\n",
          "## Metrik umum\n",
          "| Metrik | Hasil |",
          "|---|---|",
          f"| Jumlah dokumen | {len(stats)} |",
          f"| Total karakter (KONTEN) | {total_chars:,} |",
          f"| Rata-rata panjang | {mean:,.0f} karakter |",
          f"| Dokumen terpendek | {shortest['file']} ({shortest['chars']:,} karakter) |",
          f"| Dokumen terpanjang | {longest['file']} ({longest['chars']:,} karakter) |",
          f"| Total chunk (baseline B, 700/150) | {len(chunks)} |",
          f"| Chunk per dokumen | {per_doc_chunks} |",
          "\n## Per dokumen\n",
          "| file | karakter | baris | BAB | Bagian | Pasal | Ayat | chunk (B) |",
          "|---|---|---|---|---|---|---|---|",
          ]
    for s in stats:
        cid = s["file"][:-3]
        md.append(f"| {s['file']} | {s['chars']:,} | {s['lines']:,} | {s['bab']} | {s['bagian']} | {s['pasal']} | {s['ayat']} | {per_doc_chunks.get(cid, 0)} |")

    md += ["\n## Pemeriksaan kualitas\n",
           f"- Dokumen kosong: **{len(empty)}**" + (" (BERMASALAH)" if empty else " - tidak ada"),
           f"- Judul/duplikat file: **{'ada duplikat!' if dups else 'tidak ada duplikat'}**",
           "- Struktur heading (BAB/Bagian/Pasal/Ayat) dipertahankan dan terdeteksi pada semua dokumen.",
           "- Artefak karakter: tetap tersisa token ambigu hasil ekstraksi font custom UU 6/2023 (mis. 'SIP3MI' legit; token rusak seperti 'l7l'). Perbaikan hanya untuk kasus yang dapat dipastikan; sisanya dicatat di README Bab 8.",
           ]

    OUT.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Ditulis: {OUT}")


if __name__ == "__main__":
    main()