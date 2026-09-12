# RAG Ketenagakerjaan Indonesia — Data & Preprocessing

Bagian **Anggota 1 (Data & Preprocessing)**: dari datasource sampai `chunks.jsonl`
yang siap di-embedding oleh Anggota 2.

## 1. Ringkasan pipeline

```text
Peraturan.go.id (PDF resmi)          peraturan.go.id (halaman detail)
        │ unduh 11 dokumen terpilih                 │ scrape metadata
        ▼                                            ▼
data/raw/pdf/*.pdf                 data/selected/metadata.json
        │ pypdf → teks + pembersihan ringan
        ▼
data/selected/markdown/<id>.md  →  document_manifest.csv
        │                        └→ exploration_summary.md (Bab 20)
        │ RecursiveCharacterTextSplitter (baseline, custom separator)
        ▼
data/processed/chunks.jsonl        (+ chunks_a.jsonl untuk perbandingan baseline)
```

## 2. Datasource

- **Sumber resmi**: Direktorat Jenderal Peraturan Perundang-undangan,
  `https://peraturan.go.id` (unduhan PDF per dokumen + metadata halaman detail).
- **Deviasi dari plan 3.1**: repo GitHub `Open-Technology-Foundation/peraturan.go.id`
  TIDAK memuat data dokumen (`embed_data.text/`, `.db`, `.faiss` adalah artefak runtime
  yang tidak di-track di repo; README repo menyatakan kode `customkb`/exporter juga
  tidak ada). Sebagai pengganti, dilakukan **unduh bertarget 11 dokumen yang sudah
  dipilih** dari situs resmi — bukan crawling.
- Halaman detail `peraturan.go.id/id/<slug>` menyediakan metadata: jenis, nomor,
  tahun, tentang, tempat/tanggal penetapan, status, pengundangan.

## 3. Subset dokumen (11 dokumen)

Semua dokumen **berstatus Berlaku**. Kombinasi: 6 UU + 3 PP + 2 Permenaker.

Manifest resmi: `data/selected/document_manifest.csv` (kolom sesuai plan Bab 8.3).
Metadata lengkap: `data/selected/metadata.json`.

| dokumen | jenis | domain |
|---|---|---|
| uu-13-2003 (UU No. 13/2003 Ketenagakerjaan) | UU | ketenagakerjaan |
| uu-6-2023 (UU No. 6/2023 Cipta Kerja) | UU | ketenagakerjaan |
| pp-35-2021 (PKWT, Alih Daya, Waktu Kerja/Istirahat, PHK) | PP | ketenagakerjaan |
| pp-36-2021 (Pengupahan) | PP | pengupahan |
| pp-37-2021 (Jaminan Kehilangan Pekerjaan) | PP | jaminan-sosial |
| uu-40-2004 (Sistem Jaminan Sosial Nasional) | UU | jaminan-sosial |
| uu-24-2011 (Badan Penyelenggara Jaminan Sosial) | UU | jaminan-sosial |
| uu-21-2000 (Serikat Pekerja/Serikat Buruh) | UU | hubungan-industrial |
| uu-2-2004 (Penyelesaian Perselisihan HI) | UU | hubungan-industrial |
| permenaker-1-2017 (Struktur dan Skala Upah) | Permenaker | pengupahan |
| permenaker-10-2018 (Tata Cara Penggunaan TKA) | Permenaker | ketenagakerjaan |

Alasan pemilihan mengikuti plan Bab 3.4–3.5 (relevansi domain, keterkaitan
antarregulasi, variasi jenis). Dokumen `UU 11/2020` dan `PP 78/2015` TIDAK disertakan
karena sudah digantikan oleh `UU 6/2023` dan `PP 36/2021` (non-redundan), sedangkan
`PP 22/2009`, `UU 49/1999` dan sejenisnya tidak memenuhi prioritas topik.

## 4. Struktur markdown

Struktur setiap file di `data/selected/markdown/` mengikuti format repository
peraturan.go.id yang dirujuk plan Bab 9.4:

```text
# PERATURAN <JENIS> NOMOR <NOMOR> TAHUN <TAHUN>
## TENTANG
<subjek>
## JENIS
<jenis/bentuk>
## DOKUMEN
<nama file PDF sumber>
## KONTEN
<teks lengkap - body utama>
```

## 5. Preprocessing (plan Bab 9)

- Ekstraksi: `pypdf` (semua PDF born-digital, tidak perlu OCR).
- Pembersihan **ringan** (tidak mengubah istilah hukum, tidak menyatukan dokumen,
  tidak stemming/stopword agresif):
  - normalisasi CRLF, spasi berlebih, baris kosong berulang;
  - buang baris *footer/header*: nomor halaman, `www.peraturan.go.id`,
    path `file:///`, blok alamat `Ditjen PP`, label "Teks tidak dalam format asli.";
  - perbaikan artefak karakter yang **dapat dipastikan** tanpa mengubah makna
    (token map kecil + `O↔0` di sekitar angka); artefak ambigu dibiarkan (Bab 8);
  - huruf kapital & struktur `BAB/Bagian/Pasal/Ayat` dipertahankan.

## 6. Chunking (plan Bab 10)

- Splitter: `RecursiveCharacterTextSplitter` (langchain-text-splitters), length = karakter.
- **Baseline utama (B)**: `chunk_size=700`, `chunk_overlap=150` → `data/processed/chunks.jsonl`
- **Baseline pembanding (A)**: `chunk_size=500`, `chunk_overlap=100` → `data/processed/chunks_a.jsonl`
- **Custom separator sadar struktur hukum**:
  `["\n\nBAB ", "\n\nBagian ", "\n\n### ", "\n\n## ", "\n\nPasal ", "\n\n", "\n", " ", ""]`
- Metadata per chunk (plan Bab 7.3 & 10.4): `document_id, filename, chunk_id, source,
  document_type, document_number, document_year, title` + `bab, bagian, pasal, ayat`
  (kondisi heading yang memuat awal chunk).

Contoh record `chunks.jsonl`:

```json
{"text": "...", "metadata": {"document_id": "pp-35-2021", "filename": "pp-35-2021.md", "chunk_id": "pp-35-2021-0042", "source": "https://peraturan.go.id/id/pp-no-35-tahun-2021", "document_type": "PERATURAN PEMERINTAH", "document_number": "35", "document_year": "2021", "title": "...", "bab": "BAB IV PESANGON ...", "pasal": "Pasal 43", "ayat": "ayat (1)"}}
```

Statistik baseline B: **3.456 chunk / 11 dokumen**; median panjang chunk 678 karakter,
tidak ada chunk kosong, ~3.303 chunk membawa metadata `ayat`. Baseline A: 4.725 chunk.
Ringkasan lengkap per dokumen: `data/selected/exploration_summary.md` (Bab 20).

## 7. Reproducibility

Setup environment (sekali, setelah clone):

```bash
uv venv                          # buat .venv (otomatis dipakai uv run)
uv pip install -r requirements.txt
```

Perintah pipeline:

```bash
uv run python src/download_pdfs.py          # unduh PDF (idempoten) → data/raw/pdf
uv run python src/fetch_metadata.py         # scrape metadata → data/selected/metadata.json
uv run python src/build_markdown.py         # PDF → markdown → data/selected/markdown
uv run python src/build_manifest.py         # → data/selected/document_manifest.csv
uv run python src/summarize_dataset.py      # → data/selected/exploration_summary.md
uv run python src/chunk_documents.py --baseline b   # → data/processed/chunks.jsonl
uv run python src/chunk_documents.py --baseline a   # → data/processed/chunks_a.jsonl
```

Catatan: `data/raw/pdf` (PDF sumber, ±35 MB) tidak di-commit. Regenerasi opsional
via `src/download_pdfs.py`; seluruh output akhir sudah tersedia di `data/selected/`
dan `data/processed/`.

Konfigurasi & konvensi tercatat di `experiment_config.yaml` (Bab 42) dan
`requirements.txt` (Bab 43).

## 8. Keterbatasan

- Hanya teks utama (tidak termasuk lampiran penjelasan `*pjl`).
- Font custom di `UU 6/2023` menyebabkan sebagian artefak ejaan yang bersifat
  **ambiguous** tidak diperbaiki otomatis (contoh: `l7l`, `2O2O`->`2020` bersifat
  kontekstual; ada juga token yang memang sah seperti `SIP3MI`). Perbaikan hanya
  untuk kasus yang dapat dipastikan. Pengaruhnya terbatas dan tidak mengubah makna.
- `UU 6/2023` (1.127 halaman) merupakan dokumen omnibus besar; mayoritas chunk
  berasal dari dokumen ini (2.426 chunk).