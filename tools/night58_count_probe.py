# -*- coding: utf-8 -*-
"""night58_count_probe.py — 一次性：数 將/将/橫/横/處/処 在 N57 归档里的分布。"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(io.open(os.path.join(ROOT, "eval", "night57_results_3000.json"), encoding="utf-8"))
rows = [r for r in d["results"] if r.get("udkundoku_kakikudashi")]
for c in "將将橫横處処靑青":
    g = sum(re.sub(r"\s+", "", r["udkundoku_kakikudashi"]).count(c) for r in rows)
    e = sum(re.sub(r"\s+", "", r["expected_kakikudashi"]).count(c) for r in rows)
    print("%s got %d exp %d" % (c, g, e), flush=True)
