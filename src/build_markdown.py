import json
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import DOCS_BY_ID

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "pdf"
OUT = ROOT / "data" / "selected" / "markdown"
OUT.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("build_markdown")

BOILER_LINES = {
    "Teks tidak dalam format asli.",
    "Teks Tidak dalam Format Asli.",
    "Bahan Hukumonline.com",
    "PRESIDEN REPUBLIK INDONESIA,",
    "SEKRETARIS NEGARA REPUBLIK INDONESIA,",
    "MENTERI KETENAGAKERJAAN REPUBLIK INDONESIA,",
}
FOOTER_PATTERNS = [
    re.compile(r"^\d+$"),
    re.compile(r"^\d+ of \d+"),
    re.compile(r"^\d{4}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}\s*(AM|PM|WIB|WITA|WIT)?$"),
    re.compile(r"^www\.[\w.\-]+\.(go\.id|com|id)$", re.I),
    re.compile(r"file:///"),
    re.compile(r"^\d{4},\s*No\.\d+\s*-\d+-\s*$"),
    re.compile(r"^ditjen (pp|peraturan perundang-undangan)", re.I),
    re.compile(r"^2007\s+.*ditjen", re.I),
    re.compile(r"^\d+\.md$"),
]
HEADER_PREFIXES = ("Departemen Hukum", "Direktorat Jenderal Peraturan", "Jln. Rasuna", "Faks:", "Website:", "Email:", "http://")

TOKEN_FIXES = {
    "pen5rusunan": "penyusunan",
    "Pen5rusunan": "Penyusunan",
    "men5rusun": "menyusun",
    "pen5rusun": "penyusun",
    "je1as": "jelas",
}


def fix_artifacts(text: str) -> str:
    for bad, good in TOKEN_FIXES.items():
        text = text.replace(bad, good)
    text = re.sub(r"(?<=\d)O|O(?=\d)", "0", text)
    return text


def clean_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if s in BOILER_LINES:
        return False
    if any(p.search(s) for p in FOOTER_PATTERNS):
        return False
    if s.startswith(HEADER_PREFIXES):
        return False
    return True


def normalize(text: str) -> str:
    text = text.replace("\r", "")
    lines = text.split("\n")
    kept = []
    for ln in lines:
        if not clean_line(ln):
            continue
        kept.append(ln.rstrip())
    body = "\n".join(kept)
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"(?m)^\s+", "", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return fix_artifacts(body)


def extract_pdf(pdf: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception as e:
            logger.warning("  halaman gagal diekstrak: %s", e)
    return normalize("\n".join(pages))


def main() -> None:
    with open(ROOT / "data" / "selected" / "metadata.json", encoding="utf-8") as f:
        metadata = json.load(f)

    for doc_id, meta in metadata.items():
        doc = DOCS_BY_ID[doc_id]
        pdf = RAW / doc["pdf_file"]
        doc_type = meta.get("Jenis/Bentuk Peraturan", "PERATURAN")
        number = meta.get("Nomor", "")
        year = meta.get("Tahun", "")
        tentang = meta.get("Tentang", "")
        title = meta.get("title", "")

        konten = extract_pdf(pdf)
        if not konten:
            logger.warning("KONTEN KOSONG: %s", doc_id)
            continue

        md = [f"# PERATURAN {doc_type} NOMOR {number} TAHUN {year}",
              "",
              "## TENTANG",
              tentang,
              "",
              "## JENIS",
              doc_type,
              "",
              "## DOKUMEN",
              doc["pdf_file"],
              "",
              "## KONTEN",
              "",
              konten,
              ""]
        out = OUT / f"{doc_id}.md"
        out.write_text("\n".join(md), encoding="utf-8")
        logger.info("%-20s %5d chars | %s", doc_id, len(konten), title[:55])


if __name__ == "__main__":
    main()