# -*- coding: utf-8 -*-
"""day11_pick3b.py — D11 护栏枚举（快速版）。

优化：先预计算每条 (got, exp) 的 norm 串和基线距离；
组合枚举时只对含「これ」的条目重算（约 300 条），而不是 1000 条。
"""
import itertools
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


S = "\u0001K"

ELEMENTS = {
    "見": r"これ(?=を見)",
    "言": r"これ(?=を言)",
    "adv": r"これ(?=より|まで|から)",
    "emph": r"これ(?=[ぞこそさへすらだけのみ])",
    "dupe": r"これこれ",
    "yotte": r"これ(?=を以て|に由りて)",
}


def main():
    with open(os.path.join(EV, "day10_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]

    # 预计算
    items = []   # (got, exp, base_dist)
    untouched = 0
    for r in rows:
        g, e = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        bd = lev(g, e)
        if "これ" in g:
            items.append((g, e, bd))
        else:
            untouched += bd
    print("含これ条目 %d / %d（其余 %d 条基线距离合计 %d 不变）"
          % (len(items), len(rows), len(rows) - len(items), untouched), flush=True)
    base_avg = (untouched + sum(x[2] for x in items)) / len(rows)
    print("基线 avg %.3f\n" % base_avg, flush=True)

    def evalr(keys):
        rx = re.compile("|".join(ELEMENTS[k] for k in keys)) if keys else None
        ds, better, worse, changed = [], 0, 0, 0
        for g, e, bd in items:
            if rx is None:
                new = g.replace("これ", "之")
            else:
                new = rx.sub(S, g).replace("これ", "之").replace(S, "これ")
            if new != g:
                changed += 1
            nd = lev(new, e)
            ds.append(nd)
            if nd < bd:
                better += 1
            elif nd > bd:
                worse += 1
        avg = (untouched + sum(ds)) / len(rows)
        return changed, avg, avg - base_avg, better, worse

    results = []
    keys = list(ELEMENTS)
    for r_ in range(0, len(keys) + 1):
        for combo in itertools.combinations(keys, r_):
            ch, avg, d, b, w = evalr(combo)
            results.append({"guard": "+".join(combo) or "(none)", "changed": ch,
                            "avg": round(avg, 3), "delta": round(d, 3),
                            "better": b, "worse": w})
            print("%-22s 改写 %3d  avg %7.3f (%+.3f)  改善 %3d / 变差 %3d"
                  % (results[-1]["guard"], ch, avg, d, b, w), flush=True)

    results.sort(key=lambda x: (x["worse"], x["avg"]))
    print("\n=== 0 变差 且 改写最多 ===", flush=True)
    zero = [r_ for r_ in results if r_["worse"] == 0]
    zero.sort(key=lambda x: -x["changed"])
    for r_ in zero[:6]:
        print("  %-22s 改写 %3d  avg %.3f (%+.3f)"
              % (r_["guard"], r_["changed"], r_["avg"], r_["delta"]), flush=True)

    with open(os.path.join(EV, "day11_pick3.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"base_avg": round(base_avg, 3), "all": results}, f, ensure_ascii=False, indent=1)
    print("written: eval/day11_pick3.json", flush=True)


if __name__ == "__main__":
    main()
