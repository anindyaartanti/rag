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
    return f"[S{idx}]"


def build_context(retrieved_chunks: list[dict]) -> str:
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
    import re
    found_labels = set()
    for match in re.finditer(r"\[S\d", answer):
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
