# -*- coding: utf-8 -*-
"""compare3.py — 三份评测的编辑距离改善/变差计数（NIGHT4 报告数据）。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def m(name):
    with open(os.path.join(ROOT, "eval", name), encoding="utf-8") as f:
        return {r["id"]: r.get("edit_distance", 999) for r in json.load(f)["results"]}


def cmp(na, ma, nb, mb_):
    better = sum(1 for k in ma if mb_[k] < ma[k])
    worse = sum(1 for k in ma if mb_[k] > ma[k])
    print("%s vs %s: 改善 %d / 变差 %d / 持平 %d" % (nb, na, better, worse, len(ma) - better - worse))
    return better, worse


def main():
    mb = m("night4_results_baseline.json")
    m1 = m("night4_results_full_v1.json")
    m2 = m("night4_results_full_v2.json")
    cmp("baseline", mb, "full_v1", m1)
    cmp("full_v1", m1, "full_v2", m2)
    cmp("baseline", mb, "full_v2", m2)
    regs = sorted(((k, m1[k], m2[k]) for k in m1 if m2[k] > m1[k]),
                  key=lambda t: t[2] - t[1], reverse=True)
    print("v2 较 v1 变差最多的条目:", [(k, a, b) for k, a, b in regs[:10]])


if __name__ == "__main__":
    main()
