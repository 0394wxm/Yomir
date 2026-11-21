# -*- coding: utf-8 -*-
"""night64_exact_rows.py — 列出 N64 新增的精确匹配行（19→24）。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
d64 = json.load(open(os.path.join(EV, "night64_results_4000.json"), encoding="utf-8"))["results"]
d60 = json.load(open(os.path.join(EV, "night60_results_4000.json"), encoding="utf-8"))["results"]
ex60 = {r["id"] for r in d60 if r.get("exact_match")}
new = [r for r in d64 if r.get("exact_match") and r["id"] not in ex60]
lost = [r["id"] for r in d60 if r.get("exact_match")
        and not any(x["id"] == r["id"] and x.get("exact_match") for x in d64)]
print("新增精确 %d 条：" % len(new))
for r in new:
    print("  %s" % r["id"])
    print("    exp: %s" % r["expected_kakikudashi"])
    print("    got: %s" % r["udkundoku_kakikudashi"])
print("丢失精确 %d 条：%s" % (len(lost), lost))
