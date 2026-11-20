# -*- coding: utf-8 -*-
"""night60_error_row.py — 一次性：新 error 行 toushisen043-16 的详情（N59 ⑬ 论据补强）。"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
res = json.load(io.open(os.path.join(EV, "night60_results_4000.json"), encoding="utf-8"))["results"]
for r in res:
    if r.get("udkundoku_kakikudashi") is None:
        print("id:", r["id"])
        print("  source :", r["source_url"])
        print("  hakubun:", r["hakubun"])
        print("  expected:", r["expected_kakikudashi"])
        print("  error  :", r.get("error"))
