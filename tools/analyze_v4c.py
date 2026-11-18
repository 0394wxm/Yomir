# -*- coding: utf-8 -*-
"""analyze_v4c.py — 「而して 后处理规则」在 v4 上的潜在收益（只做量化，不上线）。"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with open(os.path.join(ROOT, "eval", name), encoding="utf-8") as f:
        return {r["id"]: r for r in json.load(f)["results"]}


def lev(a, b):
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def norm(s):
    return re.sub(r"\s+", "", s)


def bucket(s):
    n = len(s)
    return "<=20" if n <= 20 else ("20-40" if n <= 40 else ">40")


def evaluate(v4, label):
    base = [v4[k]["edit_distance"] for k in v4]
    new = []
    for k in v4:
        g = norm(v4[k]["udkundoku_kakikudashi"]).replace("而して", "")
        e = norm(v4[k]["expected_kakikudashi"])
        new.append(lev(g, e))
    b = sum(1 for i, k in enumerate(v4) if new[i] < base[i])
    w = sum(1 for i, k in enumerate(v4) if new[i] > base[i])
    print("%s  原 avgDist %.2f -> 去而して %.2f  改善 %d / 变差 %d / 持平 %d"
          % (label, sum(base) / len(base), sum(new) / len(new), b, w, len(base) - b - w))
    buckets = {}
    for i, k in enumerate(v4):
        buckets.setdefault(bucket(v4[k]["hakubun"]), []).append(i)
    for bk in ["<=20", "20-40", ">40"]:
        idx = buckets.get(bk, [])
        if not idx:
            continue
        print("   %-6s n=%3d  %.2f -> %.2f (%+.2f)"
              % (bk, len(idx), sum(base[i] for i in idx) / len(idx),
                 sum(new[i] for i in idx) / len(idx),
                 (sum(new[i] - base[i] for i in idx)) / len(idx)))
    return new


def main():
    v4 = load("night21_results_full_v4.json")
    print("=== 200 条 ===")
    evaluate(v4, "v4")
    big4 = load("night21_results_full_v4_500.json")
    print("\n=== 500 条 ===")
    evaluate(big4, "v4")

    print("\n=== 单句影响（200 条，去而して后变化最大的 10 条）===")
    rows = []
    for k in v4:
        g = norm(v4[k]["udkundoku_kakikudashi"])
        if "而して" not in g:
            continue
        e = norm(v4[k]["expected_kakikudashi"])
        rows.append((k, v4[k]["edit_distance"], lev(g.replace("而して", ""), e), g.count("而して")))
    for k, a, b, c in sorted(rows, key=lambda t: t[1] - t[2], reverse=True)[:10]:
        print("  %-14s %3d -> %3d  (而して×%d)" % (k, a, b, c))


if __name__ == "__main__":
    main()
