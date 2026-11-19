# -*- coding: utf-8 -*-
"""day11_check_bug.py — 核对 pick2 / pick3b 在 keiko-1 上的差异，定位哪个是错的。"""
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
        rows = json.load(f)["results"]
    r = [x for x in rows if x["id"] == "keiko-1"][0]
    g = norm(r["udkundoku_kakikudashi"])
    e = norm(r["expected_kakikudashi"])
    bd = lev(g, e)
    new = g.replace("これ", "之")
    nd = lev(new, e)
    print("keiko-1")
    print("  got len %d, exp len %d, base dist %d" % (len(g), len(e), bd))
    print("  new dist %d  (%s)" % (nd, "变差" if nd > bd else ("改善" if nd < bd else "持平")))
    print("  got これ 次数 %d, exp 之 次数 %d" % (g.count("これ"), e.count("之")))
    print()
    print("  got: %s" % g)
    print()
    print("  exp: %s" % e)

    # 全量核对：逐个含これ条目，看有没有任何一条 nd > bd
    print("\n=== 全量核对（每条含これ的条目） ===")
    bad = []
    for x in rows:
        gg = norm(x["udkundoku_kakikudashi"] or "")
        ee = norm(x["expected_kakikudashi"] or "")
        if "これ" not in gg:
            continue
        b = lev(gg, ee)
        n2 = lev(gg.replace("これ", "之"), ee)
        if n2 > b:
            bad.append((x["id"], b, n2))
    print("变差条目数：%d" % len(bad))
    for b in bad:
        print("  ", b)


if __name__ == "__main__":
    main()
