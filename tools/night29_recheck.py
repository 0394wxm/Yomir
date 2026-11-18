# -*- coding: utf-8 -*-
"""night29_recheck.py — 平行语料上的精确命中清单 + して系全量计数复核。"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(s):
    return re.sub(r"\s+", "", s)


with open(os.path.join(ROOT, "eval", "night29_results_parallel.json"), encoding="utf-8") as f:
    doc = json.load(f)
rows = doc["results"]

print("=== 精确命中 %d 条 ===" % doc["exact_match_count"])
for r in rows:
    if r.get("exact_match"):
        print("  ", r["id"], "|", r["hakubun"], "->", r["expected_kakikudashi"])

# して系计数（got / exp 两侧，全语料）
patts = [("にして", "にして"), ("して", "して"), ("而して", "而して"), ("て而して", "て而して")]
print("\n=== して系计数（1705 对，normalize 后）===")
print("%-10s %10s %10s" % ("pattern", "got", "exp"))
for label, pat in patts:
    rx = re.compile(pat)
    g = sum(len(rx.findall(norm(r.get("udkundoku_kakikudashi") or ""))) for r in rows)
    e = sum(len(rx.findall(norm(r["expected_kakikudashi"]))) for r in rows)
    print("%-10s %10d %10d" % (label, g, e))

# 独立新增的精确命中（与 night26 比对）
with open(os.path.join(ROOT, "eval", "night26_results_full.json"), encoding="utf-8") as f:
    n26 = {r["id"] for r in json.load(f)["results"] if r.get("exact_match")}
print("\nnight26 已知精确:", sorted(n26))
print("night29 全部精确:", sorted(r["id"] for r in rows if r.get("exact_match")))
