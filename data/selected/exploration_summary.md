# Ringkasan Eksplorasi Dataset (Bab 20 - Tahap 2)

## Metrik umum

| Metrik | Hasil |
|---|---|
| Jumlah dokumen | 11 |
| Total karakter (KONTEN) | 1,894,886 |
| Rata-rata panjang | 172,262 karakter |
| Dokumen terpendek | permenaker-1-2017.md (9,641 karakter) |
| Dokumen terpanjang | uu-6-2023.md (1,331,631 karakter) |
| Total chunk (baseline B, 700/150) | 3456 |
| Chunk per dokumen | {'uu-13-2003': 220, 'uu-6-2023': 2426, 'pp-35-2021': 97, 'pp-36-2021': 99, 'pp-37-2021': 57, 'uu-40-2004': 95, 'uu-24-2011': 132, 'uu-21-2000': 68, 'uu-2-2004': 174, 'permenaker-1-2017': 18, 'permenaker-10-2018': 70} |

## Per dokumen

| file | karakter | baris | BAB | Bagian | Pasal | Ayat | chunk (B) |
|---|---|---|---|---|---|---|---|
| permenaker-1-2017.md | 9,641 | 255 | 7 | 0 | 15 | 30 | 18 |
| permenaker-10-2018.md | 38,384 | 966 | 10 | 12 | 44 | 118 | 70 |
| pp-35-2021.md | 52,952 | 1,409 | 9 | 10 | 78 | 142 | 97 |
| pp-36-2021.md | 54,266 | 1,426 | 15 | 14 | 93 | 223 | 99 |
| pp-37-2021.md | 31,215 | 800 | 9 | 9 | 54 | 104 | 57 |
| uu-13-2003.md | 120,289 | 1,706 | 18 | 13 | 199 | 424 | 220 |
| uu-2-2004.md | 95,411 | 1,605 | 8 | 11 | 255 | 204 | 174 |
| uu-21-2000.md | 37,102 | 919 | 16 | 0 | 112 | 49 | 68 |
| uu-24-2011.md | 72,287 | 2,202 | 23 | 29 | 165 | 141 | 132 |
| uu-40-2004.md | 51,708 | 1,259 | 13 | 6 | 120 | 125 | 95 |
| uu-6-2023.md | 1,331,631 | 42,499 | 19 | 48 | 2864 | 2252 | 2426 |

## Pemeriksaan kualitas

- Dokumen kosong: **0** - tidak ada
- Judul/duplikat file: **tidak ada duplikat**
- Struktur heading (BAB/Bagian/Pasal/Ayat) dipertahankan dan terdeteksi pada semua dokumen.
- Artefak karakter: tetap tersisa token ambigu hasil ekstraksi font custom UU 6/2023 (mis. 'SIP3MI' legit; token rusak seperti 'l7l'). Perbaikan hanya untuk kasus yang dapat dipastikan; sisanya dicatat di README Bab 8.
