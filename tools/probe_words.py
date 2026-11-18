# -*- coding: utf-8 -*-
"""probe_words.py — 检查一批词是否出现在 200 条语料里，并给出首次出现处。"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

with io.open(os.path.join(ROOT, "eval", "night5_results_full_v3.json"), encoding="utf-8") as f:
    items = json.load(f)["results"]

for w in sys.argv[1:]:
    found = None
    for r in items:
        for seg in (r["hakubun"], r["expected_kakikudashi"]):
            if w in seg:
                i = seg.find(w)
                found = (r["id"], seg[max(0, i - 8):i + len(w) + 8])
                break
        if found:
            break
    print("%-8s %s" % (w, found if found else "ABSENT"))
