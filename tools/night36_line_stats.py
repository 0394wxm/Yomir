# -*- coding: utf-8 -*-
"""night36_line_stats.py — 统计每页非 junk 可用行数，给 GT 抽样做预算（NIGHT36）。"""
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GT36 = os.path.join(ROOT, "eval", "ocr_samples", "gt36")

rows = []
for d in sorted(glob.glob(os.path.join(GT36, "*", "boxes.json"))):
    with open(d, encoding="utf-8") as f:
        b = json.load(f)
    ok = [l["line_no"] for l in b["lines"] if not l["junk"]]
    rows.append((b["file"], b["n_lines"], len(ok), b["pid"]))

by_book = {}
for f, tot, nok, pid in rows:
    print("%-28s total=%-3d usable=%-3d pid=%s" % (f, tot, nok, pid))
    by_book.setdefault(pid, []).append(nok)

print("\n--- per book ---")
for pid, lst in by_book.items():
    print("pid %-10s pages=%d usable_sum=%d" % (pid, len(lst), sum(lst)))
