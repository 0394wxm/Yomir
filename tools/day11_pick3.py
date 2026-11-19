# -*- coding: utf-8 -*-
"""day11_pick3.py — D11：最终定选。逐条检查护栏成本，找 0 变差 + 最大收益的护栏。

策略：从 D1（全替换，0 变差、-0.889）出发，**反向**找出需要护栏的地方。
D1 的唯一问题是语料外风险（现代和文「これ」）。语料内 0 变差已经证明：
单就本语料，全替换是安全的。

所以护栏设计只需满足两个条件：
  a) 语料内 0 变差（挡掉的必须是语料里确实存在的「必须保留」形态）
  b) 语料外能挡住真指示代词

本脚本枚举「挡什么」的组合，找出「语料内 0 变差 且 改写数最多」的护栏。
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

# 候选护栏元素（各自独立可开关）
ELEMENTS = {
    "looks1": r"これ(?=[を見])",           # これを見 / これを見よ
    "looks2": r"これ(?=[聞言思])",
    "adv":    r"これ(?=より|まで|から)",
    "emph":   r"これ(?=[ぞこそさへすらだけのみ])",
    "dupe":   r"これこれ",
    "yotte":  r"これ(?=を以て|に由りて)",
}


def build(rx_str):
    rx = re.compile(rx_str) if rx_str else None

    def fn(t):
        if rx is None:
            return t.replace("これ", "之")
        t2 = rx.sub(S, t)
        t2 = t2.replace("これ", "之")
        return t2.replace(S, "これ")
    return fn


def main():
    with open(os.path.join(EV, "day10_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]
    base = [lev(norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])) for r in rows]
    base_avg = sum(base) / len(base)

    def evalr(keys):
        rx = "|".join(ELEMENTS[k] for k in keys) if keys else ""
        fn = build(rx)
        ds, better, worse, changed = [], 0, 0, 0
        for r, bd in zip(rows, base):
            g, e = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
            new = fn(g)
            if new != g:
                changed += 1
            nd = lev(new, e)
            ds.append(nd)
            if nd < bd:
                better += 1
            elif nd > bd:
                worse += 1
        avg = sum(ds) / len(ds)
        return changed, avg, avg - base_avg, better, worse

    results = []
    keys = list(ELEMENTS)
    for r_ in range(0, len(keys) + 1):
        for combo in itertools.combinations(keys, r_):
            ch, avg, d, b, w = evalr(combo)
            results.append({"guard": "+".join(combo) or "(none)", "changed": ch,
                            "avg": round(avg, 3), "delta": round(d, 3),
                            "better": b, "worse": w})

    results.sort(key=lambda x: (x["worse"], x["avg"]))
    print("%-28s %5s %8s %8s %5s %5s" % ("护栏", "改写", "avg", "delta", "改善", "变差"))
    for r_ in results[:16]:
        print("%-28s %5d %8.3f %+8.3f %5d %5d"
              % (r_["guard"], r_["changed"], r_["avg"], r_["delta"],
                 r_["better"], r_["worse"]))

    print("\n=== 0 变差 且 改写数最多 的候选 ===")
    zero = [r_ for r_ in results if r_["worse"] == 0]
    zero.sort(key=lambda x: -x["changed"])
    for r_ in zero[:8]:
        print("  %-28s 改写 %3d  avg %.3f (%+.3f)  改善 %d"
              % (r_["guard"], r_["changed"], r_["avg"], r_["delta"], r_["better"]))

    with open(os.path.join(EV, "day11_pick3.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"base_avg": round(base_avg, 3), "all": results}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
