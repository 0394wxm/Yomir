# -*- coding: utf-8 -*-
"""night26_exact.py — 打印指定归档里的精确命中条目（默认 night26_results_full.json）。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name = sys.argv[1] if len(sys.argv) > 1 else "night26_results_full.json"
with open(os.path.join(ROOT, "eval", name), encoding="utf-8") as f:
    doc = json.load(f)
for r in doc["results"]:
    if r.get("exact_match"):
        print(r["id"], "|", r["hakubun"], "->", r["expected_kakikudashi"])
