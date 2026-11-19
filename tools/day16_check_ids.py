# -*- coding: utf-8 -*-
"""day16_check_ids.py — 检查候选池 id 与 golden_1000 是否冲突。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

g1 = json.load(open(os.path.join(EV, "golden_1000.json"), encoding="utf-8"))
pool = json.load(open(os.path.join(EV, "day16_pool.json"), encoding="utf-8"))
ids1 = {x["id"] for x in g1}
clash = [r for r in pool if r["id"] in ids1]
print("golden_1000 ids %d | pool %d | id 冲突 %d" % (len(ids1), len(pool), len(clash)))
for r in clash[:10]:
    print("  clash:", r["id"], r["_src"], r["hakubun"][:40])
import collections
print("\npool 按来源:", collections.Counter(r["_src"] for r in pool))
