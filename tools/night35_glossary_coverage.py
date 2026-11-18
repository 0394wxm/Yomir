# -*- coding: utf-8 -*-
"""night35_glossary_coverage.py — D3 词库（500 条）在 1705 语料上的命中率测量。

只测量，不改词库：/api/kundoku 响应的 glossary 字段（NIGHT8/D3 管线），
统计命中条数、命中词 top、按长度分档命中率。为将来词库扩充提供证据。
"""
import json
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def norm(s):
    return re.sub(r"\s+", "", s) if True else s


import re


def main():
    from fastapi.testclient import TestClient
    from backend.main import app
    import backend.db as dbmod

    with open(os.path.join(ROOT, "eval", "kanbun_parallel.json"), encoding="utf-8") as f:
        golden = json.load(f)
    print("corpus:", len(golden))

    hit_rows = 0
    hit_words = Counter()
    per_bucket = {"<=20": [0, 0], "20-40": [0, 0], ">40": [0, 0]}
    src_counter = Counter()
    results = []
    with TestClient(app) as client:
        real = dbmod.save_kundoku
        dbmod.save_kundoku = lambda *a, **k: 1
        try:
            for i, g in enumerate(golden, start=1):
                r = client.post("/api/kundoku", json={"text": g["hakubun"]})
                if r.status_code != 200:
                    continue
                body = r.json()
                gl = body.get("glossary") or []
                ln = len(norm(g["hakubun"]))
                b = "<=20" if ln <= 20 else ("20-40" if ln <= 40 else ">40")
                per_bucket[b][1] += 1
                hit = [x for x in gl if x.get("source") == "lexicon" and x.get("word")]
                if hit:
                    hit_rows += 1
                    per_bucket[b][0] += 1
                    for x in hit:
                        hit_words[x["word"]] += 1
                        src_counter[x.get("source")] += 1
                results.append({"id": g["id"], "hits": [x.get("word") for x in hit]})
                if i % 200 == 0:
                    print("  %d/%d" % (i, len(golden)))
        finally:
            dbmod.save_kundoku = real

    n = sum(v[1] for v in per_bucket.values())
    print("\n=== D3 词库命中率（1705 语料）===")
    print("命中行 %d/%d (%.1f%%)" % (hit_rows, n, 100.0 * hit_rows / n if n else 0))
    for b, (h, t) in per_bucket.items():
        print("  %-6s %3d/%3d (%.1f%%)" % (b, h, t, 100.0 * h / t if t else 0))
    print("命中词 top20:", hit_words.most_common(20))

    with open(os.path.join(ROOT, "eval", "night35_glossary_coverage.json"), "w", encoding="utf-8") as f:
        json.dump({"total": n, "hit_rows": hit_rows,
                   "buckets": {k: v for k, v in per_bucket.items()},
                   "top_words": hit_words.most_common(50),
                   "per_entry": results}, f, ensure_ascii=False, indent=1)
    print("written: eval/night35_glossary_coverage.json")


if __name__ == "__main__":
    main()
