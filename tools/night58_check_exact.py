# -*- coding: utf-8 -*-
"""night58_check_exact.py — 一次性：找出 N58 新增的精确命中行。"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")


def norm(s):
    return re.sub(r"\s+", "", s or "")


old = json.load(io.open(os.path.join(EV, "night57_results_3000.json"), encoding="utf-8"))["results"]
new = json.load(io.open(os.path.join(EV, "night58_results_3000.json"), encoding="utf-8"))["results"]
old_exact = {r["id"] for r in old if r.get("exact_match")}
new_exact = {r["id"] for r in new if r.get("exact_match")}
print("old exact %d, new exact %d" % (len(old_exact), len(new_exact)))
print("新晋精确:", sorted(new_exact - old_exact))
print("丢失精确:", sorted(old_exact - new_exact))
for r in new:
    if r["id"] in (new_exact - old_exact):
        print("id:", r["id"])
        print("  hakubun:", r["hakubun"][:60])
        print("  got     :", norm(r["udkundoku_kakikudashi"]))
        print("  expected:", norm(r["expected_kakikudashi"]))
