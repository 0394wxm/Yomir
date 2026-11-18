# -*- coding: utf-8 -*-
"""night22_exact.py — 打印 night22_results_full.json 里的精确命中条目。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "eval", "night22_results_full.json"), encoding="utf-8") as f:
    rs = json.load(f)["results"]
for r in rs:
    if r["exact_match"]:
        print(r["id"], "|", r["hakubun"], "->", r["expected_kakikudashi"])
