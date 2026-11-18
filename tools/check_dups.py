# -*- coding: utf-8 -*-
"""check_dups.py — 评测文件的 id 唯一性/真实均值检查（防止按 id 建字典时静默合并）。"""
import collections
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES = [
    "night4_results_baseline.json",
    "night4_results_full_v1.json",
    "night4_results_full_v2.json",
    "night5_results_full_v3.json",
    "night4_results_full_v4_ge.json",
    "night21_results_full.json",
    "night21_results_full_v4_500.json",
]

for f in FILES:
    p = os.path.join(ROOT, "eval", f)
    if not os.path.exists(p):
        print("%-36s MISSING" % f)
        continue
    rs = json.load(open(p, encoding="utf-8"))["results"]
    c = collections.Counter(r["id"] for r in rs)
    dups = [k for k, v in c.items() if v > 1]
    ds = [r["edit_distance"] for r in rs if r.get("edit_distance") is not None]
    ex = sum(1 for r in rs if r.get("exact_match"))
    print("%-36s n=%3d unique=%3d dups=%s avg=%.3f exact=%d"
          % (f, len(rs), len(c), (dups[:5] if dups else "none"), sum(ds) / len(ds) if ds else -1, ex))
