# -*- coding: utf-8 -*-
"""day11_align2.py — 验证护栏判据：白文无「之」的条目里，输出是否也真的没有「これ」。

如果「白文无之 ⇒ 输出无これ」在语料上成立，那么「只在白文含之的句子做替换」
就是一个零成本的精确护栏。还要检验护栏挡掉的比例。
"""
import collections
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

    tab = collections.Counter()
    viol = []
    for r in rows:
        g, e, h = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"]), norm(r["hakubun"])
        nz, nk = h.count("之"), g.count("これ")
        tab[(nz > 0, nk > 0)] += 1
        if nz == 0 and nk > 0:
            viol.append((r["id"], nz, nk, g[:70], h[:50]))

    print("=== (白文有之?, 输出有これ?) 交叉表 ===")
    for k, v in sorted(tab.items()):
        print("  白文有之=%s 输出有これ=%s : %d 条" % (k[0], k[1], v))

    print("\n=== 白文无之 但输出有これ（护栏会挡掉的）: %d 条 ===" % len(viol))
    for v in viol[:10]:
        print("  [%s]" % v[0])
        print("    hakubun: %s" % v[4])
        print("    got    : %s" % v[3])

    # 模拟：白文有之 才替换
    base, ds = [], []
    better, worse = [], []
    changed = 0
    for r in rows:
        g, e, h = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"]), norm(r["hakubun"])
        bd = lev(g, e)
        new = g.replace("これ", "之") if h.count("之") > 0 else g
        nd = lev(new, e)
        base.append(bd)
        ds.append(nd)
        if new != g:
            changed += 1
        if nd < bd:
            better.append(r["id"])
        elif nd > bd:
            worse.append((r["id"], bd, nd))
    ba, na = sum(base) / len(base), sum(ds) / len(ds)
    print("\n=== 规则「白文含之 → 全替换」===")
    print("  改写 %d | avgDist %.3f -> %.3f (%+.3f) | 改善 %d / 变差 %d"
          % (changed, ba, na, na - ba, len(better), len(worse)))
    for w in worse:
        print("  !! %s %d->%d" % w)

    with open(os.path.join(EV, "day11_align2.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"base": round(ba, 3), "new": round(na, 3), "delta": round(na - ba, 3),
                   "changed": changed, "better": len(better), "worse": len(worse),
                   "viol_n": len(viol), "viol_ids": [v[0] for v in viol]},
                  f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
