# -*- coding: utf-8 -*-
"""night57_h2h.py — N57 新增段：规则 vs guwenbert 逐条对决 + error 行确认。"""
import io
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

r3k = json.load(io.open(r"D:\kanbun-kakikudashi\eval\night57_results_3000.json", encoding="utf-8"))
gw = json.load(io.open(r"D:\kanbun-kakikudashi\eval\night57_guwenbert_new1000.json", encoding="utf-8"))

rules_new = {r["id"]: r["edit_distance"] for r in r3k["results"][2000:]}
gw_map = {r["id"]: r["edit_distance"] for r in gw["results"]}
common = [i for i in gw_map if i in rules_new and rules_new[i] is not None and gw_map[i] is not None]
rb = sum(1 for i in common if rules_new[i] < gw_map[i])
gb = sum(1 for i in common if gw_map[i] < rules_new[i])
tie = len(common) - rb - gb
print("对决（%d 条共同有效）: 规则更好 %d | guwenbert 更好 %d | 持平 %d" % (len(common), rb, gb, tie))

for name, doc in (("规则", r3k), ("guwenbert", gw)):
    for r in doc["results"]:
        if r["edit_distance"] is None:
            print("%s error 行: %s | %r" % (name, r["id"], r.get("error", "")[:120]))
