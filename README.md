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

---

# RAG Ketenagakerjaan Indonesia — Embedding, Vector DB & Retrieval

Bagian **Anggota 2 (Embedding, Vector DB & Retrieval)**: dari `chunks.jsonl` sampai
`retrieve(query, k)` + evaluasi retrieval. **Tidak menggunakan LLM sama sekali** pada
bagian ini (plan Bab 25).

## 1. Ringkasan pipeline

```text
chunks.jsonl (3.456 chunk, baseline B)
        │ embedding lokal (intfloat/multilingual-e5-base, dimensi 768)
        ▼
vectorstore/chroma (collection rag_ketenagakerjaan, hnsw:space=cosine)
        │ similarity search: query → embedding → top-k
        ▼
retrieve(query, k) → [{text, metadata, score}, ...]    ← kontrak ke Anggota 3
        │
        ▼ (evaluasi)
evaluation/retrieval_results.json (Recall@k + relevance)
```

## 2. Model embedding (plan Bab 6)

- Model final: **`intfloat/multilingual-e5-base`** (dimensi 768, multilingual,
  mendukung Bahasa Indonesia, prefix resmi `passage:`/`query:` sesuai Bab 6.5).
- Kandidat `BAAI/bge-m3` dievaluasi tetapi **ditolak karena lambat di CPU-only**
  (560M param); e5-base memberi throughput ±11.6 chunk/s → 3.456 chunk ≈ 5 menit,
  sedangkan embedding query berjalan cepat.
- Tanpa fine-tuning (Bab 6.3); dokumen dan query memakai **model yang sama**
  (Bab 6.4); embedding dinormalisasi.
- Konfigurasi: `src/config.py` dan `experiment_config.yaml`.

## 3. Vector store & metadata (plan Bab 7)

- **ChromaDB** persistent di `vectorstore/chroma`, collection `rag_ketenagakerjaan`,
  metric **cosine** (`hnsw:space=cosine`).
- Setiap vektor: `id = chunk_id`, embedding (768), text, metadata dari `chunks.jsonl`:
  `document_id, filename, source, document_type, document_number, document_year,
  title` + `bab, bagian, pasal, ayat` (kondisi heading awal chunk).
- Verifikasi saat build: **count == chunks == 3.456**; index dapat dibuka ulang
  (`--check`) dan di-query tanpa build ulang (Bab 24).

## 4. Retrieval (plan Bab 11/25)

Fungsi kontrak antaranggota (Bab 47.2):

```python
from retriever import retrieve
hits = retrieve("Apa hak pekerja ketika mengalami PHK?", k=5)
# -> [{"text": ..., "metadata": {...}, "score": ...}, ...]   score = cosine (0..1)
```

Contoh kutipan hasil `debug_retrieve(query, k=3)`:

```text
QUERY: Berapa besaran pesangon untuk masa kerja 5 tahun?

[1] similar=0.8611
    source: uu-6-2023   | BAB IV | Pasal 156  | (Perubahan UU 13/2003)
[2] similar=0.8599
    source: uu-13-2003  | BAB XII | Pasal 156 | (Perhitungan pesangon)
[3] similar=0.8550
    source: pp-35-2021   | BAB V | Pasal 40  | (PP pelaksana PHK)
```

Debug mode (Bab 11.5) menampilkan rank/sumber/pasal/score sehingga retrieval dapat
diperiksa dan diuji **tanpa LLM** via `Retriever().debug_retrieve(query, k)`.

## 5. Reproducibility

Setup environment (sekali, setelah clone):

```bash
uv venv                          # buat .venv (otomatis dipakai uv run)
uv pip install -r requirements.txt
```

Perintah pipeline:

```bash
uv run python src/build_vectorstore.py            # build index (idempotent) → vectorstore/chroma
uv run python src/build_vectorstore.py --force    # rebuild dari nol
uv run python src/build_vectorstore.py --check    # verifikasi buka-ulang / cek count
uv run python src/evaluate_retrieval.py           # evaluasi → evaluation/retrieval_results.json
```

Catatan: `vectorstore/` tidak di-commit (gitignored) dan dapat dibuat ulang dari
`chunks.jsonl` kapan saja. Konfigurasi & hasil tercatat di `experiment_config.yaml`
(Bab 42).

## 6. Hasil evaluasi retrieval (plan Bab 29–33)

Dataset: 20 pertanyaan (5 easy / 8 medium / 4 hard / 3 out-of-domain) + ground truth
`document_id` di `evaluation/questions.json`; detail per-query di
`evaluation/retrieval_results.json`.

| Metrik | Nilai |
|---|---|
| Recall@5 (document-level) | **17/17 = 100%** |
| Mean recall support | 0.76 |
| easy | 5/5 |
| medium | 8/8 |
| hard | 4/4 |

Catatan: pada engine retrieval murni, pertanyaan **out-of-domain tetap menarik chunk**
(top-k terisi dokumen yang tidak relevan); penolakan/tidak-menjawab adalah tanggung
jawab **prompt guardrail Anggota 3** (plan Bab 14), bukan retriever.

## 7. Keterbatasan

- Retriever berbasis cosine similarity murni; tanpa hybrid BM25, metric learning,
  atau reranker (sesuai plan Bab 59 — tidak dikerjakan).
- `UU 6/2023` mendominasi index (2.426 dari 3.456 chunk) sehingga query yang
  menyerempet topik omnibus cenderung menarik chunk dokumen ini.
- Batas chunk dapat memotong Pasal; metadata `pasal/ayat` mengacu heading yang
  memuat awal chunk, bukan seluruh isi chunk.
- Retrieval bagus ≠ jawaban benar: validasi akhir jawaban bergantung pada generation
  (Anggota 3).

---

## 8. Anggota 3 — LLM, RAG Pipeline & Evaluasi Generation

### 8.1 Komponen

| File | Fungsi |
|---|---|
| `src/config.py` | Konfigurasi sentral: model, temperature, path |
| `src/generator.py` | Wrapper Gemini (`google.genai` SDK), retry + backoff |
| `src/prompt.py` | System prompt, context builder, source parser, source attribution |
| `src/rag_pipeline.py` | End-to-end `answer_question()` + logging JSONL |
| `src/retriever.py` | Semantic retrieval — `retrieve(query, k)` + `debug_retrieve()` |
| `app.py` | CLI demo interaktif + 4 skenario Bab 62 |
| `app_streamlit.py` | GUI Streamlit chatbot (localhost:8501) |

### 8.2 Model & Konfigurasi

- **LLM**: Gemini 3.6 Flash (`gemini-3.6-flash`)
- **Temperature**: 0.1 (konservatif, mengurangi hallucination)
- **API key**: dari environment variable `GOOGLE_API_KEY`
- **SDK**: `google-genai>=2.23.0` (bukan `google-generativeai` yang deprecated)
- **Rate limit**: 20 req/hari per model (free tier). Script auto-retry dengan backoff.

### 8.3 Cara Menjalankan

```bash
# Setup
cp .env.example .env   # isi GOOGLE_API_KEY
uv venv && uv pip install -r requirements.txt

# Build vectorstore (jika belum ada)
uv run python src/build_vectorstore.py --force

# Demo interaktif
uv run python app.py

# Demo 4 skenario
uv run python app.py --demo

# Debug retrieval
uv run python app.py --debug

# GUI Streamlit (browser, localhost:8501)
uv run streamlit run app_streamlit.py
```

### 8.4 Prompt Design

- System prompt memaksa model hanya menggunakan context yang diberikan
- Larangan fabrikasi pasal/sumber yang tidak ada dalam context
- Out-of-context → `"Informasi yang diperlukan tidak ditemukan dalam dokumen yang tersedia."`
- Out-of-domain → penolakan dengan penjelasan di luar knowledge base
- Source attribution: `[S1]`, `[S2]`, ... di dalam jawaban + footer sumber
- Disclaimer: `"Sistem ini merupakan prototype RAG untuk tujuan pembelajaran dan bukan pengganti konsultasi hukum."`

### 8.5 Hasil Evaluasi Generation

| Difficulty | n | Faithfulness | Relevance | Source Correctness | Completeness |
|---|---|---|---|---|---|
| easy | 5 | 1.6 | 1.8 | 2.0 | 1.2 |
| medium | 8 | 1.8 | 1.9 | 2.0 | 1.4 |
| hard | 4 | 1.5 | 1.8 | 2.0 | 1.2 |
| out-of-domain | 3 | 2.0 | 2.0 | 2.0 | 2.0 |

Catatan:
- **Source correctness 2.0** di semua kategori: semua sumber yang dicantumkan benar-benar ada di retrieved chunks.
- **OOD 2.0**: semua pertanyaan di luar knowledge base berhasil ditolak.
- **Over-refusal diperbaiki**: `gemini-3.6-flash` menjawab Q14 (multi-dokumen PHK) dengan benar, tidak seperti `3.5-flash-lite` yang menolak.
- Q16 (hubungan UU Cipta Kerja) ditolak karena memang tidak ada perbandingan eksplisit di korpus — ini benar (bukan over-refusal).
- Skor adalah auto-draft (heuristik), perlu review manual.

### 8.6 Output Files

- `evaluation/evaluation_results.csv` — 20 baris, siap scoring manual
- `evaluation/generation_outputs.json` — jawaban lengkap + retrieved chunks + metadata
- `logs/query_log.jsonl` — log setiap query (timestamp, question, retrieved IDs, scores, answer)

### 8.7 Known Limitations (Anggota 3)

1. **Completeness rendah untuk easy questions**: Jawaban ringkas (definisi) skor completeness rendah karena heuristic word-count, tapi sebenarnya sudah benar dan cukup.
2. **Rate limit**: 20 req/hari per model. Evaluasi 20Q memakan seluruh kuota harian.
3. **Source parser**: Fix regex untuk format `[S1, S2]` (grouped citation) — sudah diperbaiki di sesi ini.