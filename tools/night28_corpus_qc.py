# -*- coding: utf-8 -*-
"""night28_corpus_qc.py — 平行语料库质检（id 唯一/空字段/重复对/长度分布/与既有集重叠）。"""
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with open(os.path.join(ROOT, "eval", name), encoding="utf-8") as f:
        return json.load(f)


def main():
    doc = load("kanbun_parallel.json")
    rows = doc if isinstance(doc, list) else doc.get("results", doc)
    n = len(rows)
    print("corpus size:", n)

    ids = [r["id"] for r in rows]
    dup_ids = [k for k, v in Counter(ids).items() if v > 1]
    print("id 重复：%d" % len(dup_ids), dup_ids[:5])

    empty = [r["id"] for r in rows if not r.get("hakubun") or not r.get("expected_kakikudashi")]
    print("空字段：%d" % len(empty))

    pairs = Counter((r["hakubun"], r["expected_kakikudashi"]) for r in rows)
    dup_pairs = sum(v - 1 for v in pairs.values() if v > 1)
    print("完全重复对（去重将减少）：%d" % dup_pairs)

    paren = [r["id"] for r in rows if "（" in r["hakubun"] or "）" in r["hakubun"]]
    print("白文含注记括号（抓取器已滤，应为 0）：%d" % len(paren))

    lens = Counter()
    for r in rows:
        ln = len(re.sub(r"\s+", "", r["hakubun"]))
        lens["<=20" if ln <= 20 else ("20-40" if ln <= 40 else ">40")] += 1
    print("长度分布:", dict(lens))

    pages = Counter(r["source_url"] for r in rows)
    print("页面数 %d，单页最多对数 %d，页均 %.1f"
          % (len(pages), max(pages.values()), n / len(pages)))

    for name in ("golden.json", "golden_1000.json", "golden_rongo.json"):
        other = load(name)
        other = other if isinstance(other, list) else other.get("results", [])
        oid = {x["id"] for x in other}
        print("与 %-18s id 交集 %d" % (name, len(oid & set(ids))))

    # kundoku 侧：白文假名占比（引擎 kana 分流会在这些条目上早退）
    kana_rows = 0
    for r in rows:
        h = re.sub(r"\s+", "", r["hakubun"])
        if not h:
            continue
        kana = sum(1 for c in h if re.match(r"[ぁ-ゖァ-ヺ]", c))
        if kana / len(h) > 0.3:
            kana_rows += 1
    print("假名占比>30%%（引擎分流）：%d (%.1f%%)" % (kana_rows, 100.0 * kana_rows / n))


if __name__ == "__main__":
    main()
