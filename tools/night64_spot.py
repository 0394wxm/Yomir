# -*- coding: utf-8 -*-
"""night64_spot.py — 抽查组合改写行（人工核对用，随机 14 条）。"""
import json
import os
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rs = json.load(open(os.path.join(ROOT, "eval", "night64_combo_changed_rows.json"),
                    encoding="utf-8"))
print("total", len(rs))
random.seed(7)
for r in random.sample(rs, 14):
    print("--- %s %d -> %d" % (r["id"], r["old_dist"], r["new_dist"]))
    print("  new: %s" % r["new_text"][:72])
    print("  exp: %s" % r["expected"][:72])
