# -*- coding: utf-8 -*-
"""night25_genre_audit.py — Night 25：分文体 × 分档 × 错误类别 交叉审计。

回答 Night 23 §5 挂起的问题：20-40 档論語为什么比故事名言好、≤20 档为什么差。
分类器（tools/classify_errors.py）不改，import 其 classify_pair。
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
from classify_errors import classify_pair  # noqa: E402


def norm(s):
    return re.sub(r"\s+", "", s)


def bucket(src):
    n = len(norm(src))
    return "<=20" if n <= 20 else ("20-40" if n <= 40 else ">40")


def load(name):
    with open(os.path.join(ROOT, "eval", name), encoding="utf-8") as f:
        return json.load(f)["results"]


def audit(name, rows):
    print("\n=== %s ===" % name)
    cells = defaultdict(lambda: {"n": 0, "dist": [], "cats": Counter()})
    for r in rows:
        got = norm(r.get("udkundoku_kakikudashi") or "")
        exp = norm(r["expected_kakikudashi"])
        b = bucket(r["hakubun"])
        cell = cells[b]
        cell["n"] += 1
        d = r.get("edit_distance")
        if d is not None:
            cell["dist"].append(d)
        cats = classify_pair(got, exp)
        for c in cats:
            cell["cats"][c] += 1
    for b in ("<=20", "20-40", ">40"):
        cell = cells.get(b)
        if not cell:
            continue
        ds = cell["dist"]
        avg = sum(ds) / len(ds) if ds else -1
        cats = "  ".join("%s %d(%.0f%%)" % (c, n, 100.0 * n / cell["n"])
                         for c, n in cell["cats"].most_common(4))
        print("  %-6s n=%3d avgDist %6.2f | %s" % (b, cell["n"], avg, cats))


def examples(name, rows, bucket_name, k=4):
    print("\n--- %s %s 档对齐样本（got‖exp，取 dist 中位数附近）---" % (name, bucket_name))
    sel = []
    for r in rows:
        if bucket(r["hakubun"]) != bucket_name:
            continue
        d = r.get("edit_distance")
        if d is not None:
            sel.append((d, r))
    if not sel:
        return
    sel.sort(key=lambda t: t[0])
    mid = sel[len(sel) // 2:len(sel) // 2 + k]
    for d, r in mid:
        got = norm(r.get("udkundoku_kakikudashi") or "")
        exp = norm(r["expected_kakikudashi"])
        print("  %s dist=%d" % (r["id"], d))
        print("    got: %s" % got[:44])
        print("    exp: %s" % exp[:44])


def main():
    koji = load("night22_results_full.json")
    rongo = load("night23_results_rongo.json")
    audit("故事名言 500（night22_results_full）", koji)
    audit("論語 117（night23_results_rongo）", rongo)
    examples("論語", rongo, "<=20")
    examples("論語", rongo, "20-40")
    examples("故事名言", koji, "<=20")


if __name__ == "__main__":
    main()
