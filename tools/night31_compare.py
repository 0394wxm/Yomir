# -*- coding: utf-8 -*-
"""night31_compare.py — 新正字化表下两套官方线的重基线对比。"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with open(os.path.join(ROOT, "eval", name), encoding="utf-8") as f:
        return {r["id"]: r for r in json.load(f)["results"]}


def main():
    for old_name, new_name, label in (
            ("night22_results_full.json", "night31_results_full.json", "故事名言500"),
            ("night23_results_rongo.json", "night31_results_rongo.json", "論語117")):
        old, new = load(old_name), load(new_name)
        common = sorted(set(old) & set(new))
        n = len(common)
        d_o = sum(old[k]["edit_distance"] for k in common) / n
        d_n = sum(new[k]["edit_distance"] for k in common) / n
        imp = sum(1 for k in common if new[k]["edit_distance"] < old[k]["edit_distance"])
        wor = sum(1 for k in common if new[k]["edit_distance"] > old[k]["edit_distance"])
        ex_o = sum(1 for k in common if old[k].get("exact_match"))
        ex_n = sum(1 for k in common if new[k].get("exact_match"))
        print("%s：%d 条交集 avgDist %.2f -> %.2f (%+.2f)  改善 %d / 变差 %d / 持平 %d  精确 %d -> %d"
              % (label, n, d_o, d_n, d_n - d_o, imp, wor, n - imp - wor, ex_o, ex_n))
        if wor:
            bad = sorted(((k, old[k]["edit_distance"], new[k]["edit_distance"]) for k in common
                          if new[k]["edit_distance"] > old[k]["edit_distance"]),
                         key=lambda t: t[2] - t[1], reverse=True)[:5]
            for k, a, b in bad:
                print("    变差 %s %+d (%d->%d)" % (k, b - a, a, b))


if __name__ == "__main__":
    main()
