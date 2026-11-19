# -*- coding: utf-8 -*-
"""day11_diag.py — 诊断：为什么 keiko-1 在部分替换时变差、全替换时不变差。

keiko-1 的 got 里有 3 个「これ」、exp 里有 1 个「之」。
全替换：3 个都变 之，dist 110->109（改善）
部分替换（护栏挡住其中 2 个）：只剩 1 个变，dist 110->111（变差）

这说明 keiko-1 的编辑距离对「改几个字」不敏感——它整句已经严重错位
（dist 110 / 197 字）。全替换多改两个字反而"歪打正着"降低距离。

这种样本正是「编辑距离在某一句上非单调」的典型：不能拿它当规则好坏判据。
本脚本量化：有多少条目的变异是这种非单调（改得越多反而越接近）。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def lev(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def main():
    with open(os.path.join(EV, "day10_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]

    r = [x for x in rows if x["id"] == "keiko-1"][0]
    g, e = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
    print("keiko-1: got %d 字, exp %d 字, dist %d" % (len(g), len(e), lev(g, e)))
    print("  「これ」出现位置：", [m.start() for m in re.finditer("これ", g)])
    print("  exp 里「之」位置：", [m.start() for m in re.finditer("之", e)])

    # 逐个替换：只换第 1/2/3 个
    pos = [m.start() for m in re.finditer("これ", g)]
    for k in range(len(pos)):
        parts = list(g)
        newg = ""
        idx = 0
        for i, ch in enumerate(g):
            if i == pos[k]:
                newg += "之"
                idx += 1
            elif i in [p + 1 for p in pos] and g[i - 1:i] == "こ":
                continue
            else:
                pass
        # 简单做法：按顺序切分重建
        chunks = re.split("これ", g)
        rebuilt = chunks[0]
        for i, c in enumerate(chunks[1:]):
            rebuilt += ("之" if i == k else "これ") + c
        print("  只替换第 %d 个: dist %d" % (k + 1, lev(rebuilt, e)))

    print("  全替换:        dist %d" % lev(g.replace("これ", "之"), e))

    # 统计：有多少条目「全替换」与「部分替换」方向相反
    print("\n=== 非单调性统计（Guard 版 vs 全替换，方向相反的条目） ===")
    from day11_final import style_kore_to_shi
    opp = []
    for x in rows:
        gg = norm(x["udkundoku_kakikudashi"])
        ee = norm(x["expected_kakikudashi"])
        if "これ" not in gg:
            continue
        b = lev(gg, ee)
        full = lev(gg.replace("これ", "之"), ee)
        guard = lev(style_kore_to_shi(gg), ee)
        if (full - b) * (guard - b) < 0:
            opp.append((x["id"], b, full, guard))
    print("方向相反的条目：%d" % len(opp))
    for o in opp[:10]:
        print("  %s base %d full %d guard %d" % o)


if __name__ == "__main__":
    main()
