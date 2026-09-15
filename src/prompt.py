"""Prompt RAG untuk asisten regulasi ketenagakerjaan Indonesia (plan Bab 12).

Prinsip prompt (plan Bab 12.2):
  1. menggunakan context
  2. tidak mengarang sumber
  3. mengakui jika context tidak cukup
  4. menyebutkan sumber

Guardrail hallucination (plan Bab 14):
  - LLM tidak boleh mengarang pasal, peraturan, nomor dokumen
  - Out-of-domain: katakan di luar knowledge base
  - Out-of-context: "Informasi yang diperlukan tidak ditemukan dalam dokumen yang tersedia."

Source attribution (plan Bab 15):
  - Identifier [S1], [S2], [S3]
  - Format: Nama dokumen, Nomor/Tahun, Pasal

Context conflict handling (plan Bab 40.2):
  - "Jika terdapat ketentuan yang berbeda dalam context, jelaskan perbedaannya dan sebutkan sumber masing-masing."
"""

SYSTEM_PROMPT = """\
Anda adalah asisten yang membantu menjelaskan regulasi ketenagakerjaan Indonesia.

ATURAN PENTING:
1. Jawab pertanyaan HANYA berdasarkan CONTEXT yang diberikan di bawah.
2. JANGAN menggunakan pengetahuan eksternal jika informasi tersebut tidak terdapat dalam CONTEXT.
3. JANGAN membuat nomor pasal, judul peraturan, atau sumber yang tidak terdapat dalam CONTEXT.
4. Jika CONTEXT tidak cukup untuk menjawab pertanyaan, katakan:
   "Informasi yang diperlukan tidak ditemukan dalam dokumen yang tersedia."
5. Jika pertanyaan berada di luar domain regulasi ketenagakerjaan, katakan bahwa pertanyaan berada di luar knowledge base.
6. Jika terdapat ketentuan yang berbeda dalam context, jelaskan perbedaannya dan sebutkan sumber masing-masing.
7. Berikan jawaban secara ringkas dan jelas.
8. Sertakan sumber yang menjadi dasar jawaban menggunakan format [S1], [S2], dst.

DISCLAIMER:
Sistem ini merupakan prototype RAG untuk tujuan pembelajaran dan bukan pengganti konsultasi hukum.
"""

DISCLAIMER = (
    "\n\n---\n"
    "*Sistem ini merupakan prototype RAG untuk tujuan pembelajaran dan bukan pengganti konsultasi hukum.*"
)


def format_source_label(idx: int) -> str:
    """Format source identifier: [S1], [S2], ... (plan Bab 15)."""
    return f"[S{idx}]"


def build_context(retrieved_chunks: list[dict]) -> str:
    """Susun context dari retrieved chunks untuk dimasukkan ke prompt (plan Bab 12.3).

    Format:
        [SOURCE 1]
        Dokumen: ...
        Pasal: ...
        Isi: ...

        [SOURCE 2]
        ...
    """
    parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        label = format_source_label(i)
        meta = chunk.get("metadata", {})
        doc_type = meta.get("document_type", "")
        doc_num = meta.get("document_number", "")
        doc_year = meta.get("document_year", "")
        title = meta.get("title", "")
        pasal = meta.get("pasal", "")
        bab = meta.get("bab", "")
        ayat = meta.get("ayat", "")
        text = chunk.get("text", "")

        # Susun info sumber
        source_info = f"{doc_type} Nomor {doc_num} Tahun {doc_year}" if doc_num else title
        section_info = " | ".join(filter(None, [bab, pasal, ayat]))

        header = f"Dokumen: {source_info}"
        if title:
            header += f"\nJudul: {title}"
        if section_info:
            header += f"\nLokasi: {section_info}"

        parts.append(f"{label}\n{header}\nIsi:\n{text}")

    return "\n\n".join(parts)


def build_prompt(question: str, context: str) -> str:
    """Susun prompt lengkap: system + context + question (plan Bab 12.3-12.4)."""
    return f"""{SYSTEM_PROMPT}

====================================
CONTEXT (Dokumen Regulasi):
====================================

{context}

====================================
PERTANYAAN:
====================================

{question}

====================================
JAWABAN:
====================================
"""


def parse_sources_from_answer(answer: str, retrieved_chunks: list[dict]) -> list[dict]:
    """Ekstrak sumber yang dirujuk dalam jawaban untuk source attribution (plan Bab 15).

    Returns list of {"label": "[S1]", "document_type": ..., "document_number": ..., ...}
    Handles both [S1] standalone and [S1, S2, S3] comma-separated formats.
    """
    import re
    # Find all source references in the answer
    # Handles: [S1], [S1, S2, S3], [S1,S2], [S1] ... [S2]
    found_labels = set()
    for match in re.finditer(r"\[S\d", answer):
        # From [S, grab all consecutive digits
        pos = match.start()
        nums = re.findall(r"\d+", answer[pos:pos+20])
        for n in nums:
            found_labels.add(n)
    sources = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        label = format_source_label(i)
        if str(i) in found_labels:
            meta = chunk.get("metadata", {})
            sources.append({
                "label": label,
                "document_type": meta.get("document_type", ""),
                "document_number": meta.get("document_number", ""),
                "document_year": meta.get("document_year", ""),
                "title": meta.get("title", ""),
                "pasal": meta.get("pasal", ""),
                "bab": meta.get("bab", ""),
            })
    return sources


def format_sources_footer(sources: list[dict]) -> str:
    """Format footer sumber untuk output (plan Bab 15)."""
    if not sources:
        return ""
    lines = ["Sumber:"]
    for s in sources:
        doc = f"{s['document_type']} Nomor {s['document_number']} Tahun {s['document_year']}"
        detail = s.get("pasal", "")
        entry = f"  {s['label']} {doc}"
        if detail:
            entry += f" — {detail}"
        lines.append(entry)
    return "\n".join(lines)
