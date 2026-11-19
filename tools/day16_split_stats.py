# -*- coding: utf-8 -*-
"""day16_split_stats.py — 把 2000 条结果拆成「旧 1000 / 新增 1000」两段对比。"""
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def bucket_of(hb):
    n = len(norm(hb))
    return "≤20字" if n <= 20 else "21-40字" if n <= 40 else "41-60字" if n <= 60 else ">60字"


def genre_of(url):
    u = (url or "").lower()
    if "/keibu/daigaku" in u:
        return "大学"
    if "/keibu/kokyo" in u:
        return "孝経"
    if "/keibu/rongo" in u:
        return "論語"
    if "/koji/" in u:
        return "故事"
    return "その他"


def show(rows, label):
    ok = [r for r in rows if r["edit_distance"] is not None]
    exact = sum(1 for r in ok if r["exact_match"])
    avg = sum(r["edit_distance"] for r in ok) / len(ok)
    print("\n=== %s ===" % label)
    print("n %d | 精确 %d | avgDist %.3f" % (len(ok), exact, avg))
    by_b = collections.defaultdict(list)
    by_g = collections.defaultdict(list)
    for r in ok:
        by_b[bucket_of(r["hakubun"])].append(r)
        by_g[genre_of(r.get("source_url", ""))].append(r)
    print("  %-9s %5s %8s %6s" % ("分档", "n", "avg", "精确"))
    for b in ["≤20字", "21-40字", "41-60字", ">60字"]:
        rs = by_b.get(b, [])
        if rs:
            print("  %-9s %5d %8.3f %6d"
                  % (b, len(rs), sum(x["edit_distance"] for x in rs) / len(rs),
                     sum(1 for x in rs if x["exact_match"])))
    print("  %-9s %5s %8s %6s" % ("文体", "n", "avg", "精确"))
    for g, rs in sorted(by_g.items(), key=lambda kv: -len(kv[1])):
        print("  %-9s %5d %8.3f %6d"
              % (g, len(rs), sum(x["edit_distance"] for x in rs) / len(rs),
                 sum(1 for x in rs if x["exact_match"])))
    return {"n": len(ok), "exact": exact, "avg": round(avg, 3)}


def main():
    d = json.load(open(os.path.join(EV, "day16_results_2000.json"), encoding="utf-8"))
    res = d["results"]
    old = show(res[:1000], "旧 1000（golden_1000 原文）")
    new = show(res[1000:], "新增 1000（parallel 575 + 大学/孝経 336 + 截断补抓 89）")
    print("\n=== 两段对比 ===")
    print("旧  n=%d  avg %.3f  exact %d" % (old["n"], old["avg"], old["exact"]))
    print("新  n=%d  avg %.3f  exact %d" % (new["n"], new["avg"], new["exact"]))
    print("Δ   %+.3f" % (new["avg"] - old["avg"]))

    # 新增段的来源分组（按 id 前缀/URL 判断）
    src = collections.Counter()
    for r in res[1000:]:
        u = r.get("source_url", "")
        if "/keibu/daigaku" in u:
            src["大学"] += 1
        elif "/keibu/kokyo" in u:
            src["孝経"] += 1
        elif "-x" in r["id"]:
            src["截断补抓"] += 1
        else:
            src["平行语料"] += 1
    print("\n新增来源:", dict(src))

    # 精确命中的 9 条
    print("\n=== 精确命中（9 条）===")
    for r in res:
        if r["exact_match"]:
            print("  %-22s %-6s %s"
                  % (r["id"][:22], genre_of(r.get("source_url", "")), r["hakubun"][:46]))


if __name__ == "__main__":
    main()
