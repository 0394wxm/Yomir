# -*- coding: utf-8 -*-
"""show_v4_diff.py — 单条 v3/v4 輸出對照（REPORT_DAY9 取证用）。

python tools/show_v4_diff.py iaritake-1 imananji-1
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    p = os.path.join(ROOT, "eval", name)
    with open(p, encoding="utf-8") as f:
        return {r["id"]: r for r in json.load(f)["results"]}


v3 = load("night5_results_full_v3.json")
v4 = load("night21_results_full_v4.json")

ids = sys.argv[1:] or ["iaritake-1", "imananji-1", "itsuworo-2"]
for i in ids:
    a, b = v3[i], v4[i]
    print("=" * 100)
    print("%s  v3=%s  v4=%s" % (i, a["edit_distance"], b["edit_distance"]))
    print("白文    : %s" % a["hakubun"])
    print("期待    : %s" % a["expected_kakikudashi"])
    print("v3(规则): %s" % a["udkundoku_kakikudashi"].replace("\n", " / "))
    print("v4(古文BERT): %s" % b["udkundoku_kakikudashi"].replace("\n", " / "))
