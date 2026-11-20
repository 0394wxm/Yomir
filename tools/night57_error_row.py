# -*- coding: utf-8 -*-
"""n57_error_row.py — 找出 3000 条里唯一一条 error 行。"""
import io
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

d = json.load(io.open(r"D:\kanbun-kakikudashi\eval\night57_results_3000.json", encoding="utf-8"))
for r in d["results"]:
    if r["edit_distance"] is None:
        print(json.dumps(r, ensure_ascii=False, indent=1)[:800])
