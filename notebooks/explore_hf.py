import duckdb

URL = "https://huggingface.co/datasets/Azzindani/ID_REG_MD_RAG/resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet"
con = duckdb.connect()

targets = [
    ('UU 13/2003 Ketenagakerjaan', "year='2003'"),
    ('UU 11/2020 Cipta Kerja', "year='2020' AND LOWER(about) LIKE '%cipta%'"),
    ('UU 6/2023 Cipta Kerja', "year='2023' AND LOWER(about) LIKE '%cipta%'"),
    ('PP 35/2021 PKWT', "year='2021' AND regulation_type LIKE '%PEMERINTAH%'"),
    ('PP 36/2021 Pengupahan', "year='2021' AND LOWER(about) LIKE '%pengupahan%'"),
    ('PP 37/2021 JKP', "year='2021' AND LOWER(about) LIKE '%kehilangan%'"),
    ('UU 40/2004 SJSN', "year='2004' AND LOWER(about) LIKE '%jaminan%'"),
]

for name, cond in targets:
    try:
        rows = con.execute(f"""
            SELECT regulation_type, regulation_number, year, ANY_VALUE(about) a, COUNT(*) n
            FROM '{URL}'
            WHERE {cond}
            GROUP BY regulation_type, regulation_number, year
            ORDER BY n DESC
        """).fetchall()
        print(f"### {name}: {len(rows)} matches")
        for r in rows:
            print(f"    {r[0]:<12} {r[1]:<12} {r[2]:<6} n={r[4]:<6} | {r[3][:90]}")
    except Exception as e:
        print(f"### {name}: ERROR {e}")