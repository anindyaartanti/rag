import re
import glob
import collections

tokens = collections.Counter()
for p in glob.glob(r"data/selected/markdown/*.md"):
    t = open(p, encoding="utf-8").read()
    for m in re.finditer(r"(?<=[a-zA-Z])[0-9](?=[a-zA-Z])", t):
        tok = re.findall(r"[a-zA-Z]+[0-9][a-zA-Z]+", t[max(0, m.start() - 10):m.end() + 10])
        for x in tok:
            tokens[x] += 1

for tok, n in tokens.most_common(60):
    print(f"{n:>4}  {tok}")