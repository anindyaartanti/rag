# RAG Ketenagakerjaan Indonesia

Prototype Retrieval-Augmented Generation (RAG) untuk menjawab pertanyaan seputar
regulasi ketenagakerjaan Indonesia. Sistem mencari potongan teks relevan dari
11 peraturan (6 UU, 3 PP, 2 Permenaker) dengan pencarian semantik, lalu menyusun
jawaban memakai LLM Gemini disertai sitasi sumber.

> Sistem ini merupakan prototype RAG untuk tujuan pembelajaran dan bukan pengganti konsultasi hukum.

## Fitur

- Knowledge base 11 peraturan ketenagakerjaan (UU 13/2003, UU 6/2023, PP 35/2021, dst.).
- Embedding lokal `intfloat/multilingual-e5-base` (dimensi 768, prefix `passage:`/`query:`).
- Vector store ChromaDB persisten dengan metrik cosine.
- Chunking sadar struktur hukum (BAB/Bagian/Pasal/Ayat) via `RecursiveCharacterTextSplitter`.
- Guardrail anti-halusinasi dan source attribution `[S1]`, `[S2]`, ... .
- Antarmuka CLI dan GUI Streamlit.

## Struktur Proyek

```text
.
├── src/
│   ├── config.py              # konfigurasi terpusat
│   ├── dataset.py             # daftar 11 dokumen
│   ├── download_pdfs.py       # unduh PDF -> data/raw/pdf
│   ├── fetch_metadata.py      # scrape metadata -> data/selected/metadata.json
│   ├── build_markdown.py      # PDF -> markdown
│   ├── build_manifest.py      # -> document_manifest.csv
│   ├── summarize_dataset.py   # -> exploration_summary.md
│   ├── chunk_documents.py     # markdown -> chunks.jsonl
│   ├── embedding.py           # model embedding
│   ├── vectorstore.py         # wrapper ChromaDB
│   ├── build_vectorstore.py   # CLI build/verifikasi index
│   ├── retriever.py           # retrieve(query, k)
│   ├── evaluate_retrieval.py  # Recall@k
│   ├── generator.py           # wrapper Gemini
│   ├── prompt.py              # prompt, context, source attribution
│   └── rag_pipeline.py        # pipeline end-to-end
├── app.py                     # CLI demo
├── app_streamlit.py           # GUI Streamlit
├── data/                      # dokumen & chunk
├── evaluation/questions.json  # test set evaluasi
└── experiment_config.yaml     # ringkasan konfigurasi & hasil
```

## Prasyarat

- Python 3.12
- [`uv`](https://docs.astral.sh/uv/) (disarankan) atau `pip` + `venv`
- Google API key untuk Gemini

## Setup

```bash
uv venv
uv pip install -r requirements.txt
```

Buat file `.env` di root proyek, lalu isi API key:

```env
GOOGLE_API_KEY=isi_api_key_anda
```

## Cara Menjalankan

### 1. Pipeline data (opsional)

Hasil pemrosesan sudah tersedia di `data/selected/` dan `data/processed/`.
Jalankan ulang hanya bila ingin regenerasi:

```bash
uv run python src/download_pdfs.py
uv run python src/fetch_metadata.py
uv run python src/build_markdown.py
uv run python src/build_manifest.py
uv run python src/summarize_dataset.py
uv run python src/chunk_documents.py --baseline b   # chunks.jsonl
uv run python src/chunk_documents.py --baseline a   # chunks_a.jsonl
```

### 2. Bangun index vector

```bash
uv run python src/build_vectorstore.py            # idempotent
uv run python src/build_vectorstore.py --force    # rebuild dari nol
uv run python src/build_vectorstore.py --check    # verifikasi index
```

### 3. Evaluasi retrieval

```bash
uv run python src/evaluate_retrieval.py
```

Hasil ditulis ke `evaluation/retrieval_results.json`.

### 4. CLI

```bash
uv run python app.py            # mode interaktif
uv run python app.py --demo     # 4 skenario demo
uv run python app.py -k 3       # ubah top-k
```

### 5. GUI Streamlit

```bash
uv run streamlit run app_streamlit.py
```

## Konfigurasi

- `src/config.py` - model embedding, model LLM, temperature, dan path.
- `experiment_config.yaml` - ringkasan konfigurasi pipeline dan hasil evaluasi.
- `.env` - berisi `GOOGLE_API_KEY`.

## Catatan

- `data/raw/`, `vectorstore/`, `logs/`, dan output `evaluation/` di-gitignore serta dapat diregenerasi.
- Kualitas jawaban bergantung pada kualitas retrieval; pertanyaan di luar knowledge base ditolak oleh guardrail prompt.

---
*Sistem ini merupakan prototype RAG untuk tujuan pembelajaran dan bukan pengganti konsultasi hukum.*
