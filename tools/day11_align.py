# -*- coding: utf-8 -*-
"""day11_align.py — D11：用白文（输入）做护栏——只有当白文里有「之」时才替换。

这是从 keiko-1 学到的：引擎多吐了两个「これ」，它们在白文里没有对应的「之」。
如果能拿到白文，就可以按「白文中 之 的个数」限额替换，多出来的保留。

本脚本检验这个假设在 1000 条上是否成立：
  * 白文里有「之」→ 输出里的「これ」优先替换（前 N 个，N = 白文之数）
  * 白文里没有「之」→ 一个都不换（这是最保守的护栏）
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


def replace_limited(text, quota):
    """按配额替换 これ -> 之，配额用完就停。"""
    out = []
    i = 0
    n = 0
    while i < len(text):
        if text.startswith("これ", i) and n < quota:
            out.append("之")
            n += 1
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def main():
    with open(os.path.join(EV, "day10_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]

    base, ds = [], []
    better, worse = [], []
    changed = 0
    quota_stats = {"quota=zhi": 0, "quota=0": 0, "quota>zhi": 0}

    for r in rows:
        g = norm(r["udkundoku_kakikudashi"])
        e = norm(r["expected_kakikudashi"])
        h = norm(r["hakubun"])
        bd = lev(g, e)
        n_zhi = h.count("之")
        n_kore = g.count("これ")
        quota = min(n_zhi, n_kore)
        new = replace_limited(g, quota)
        if quota == n_zhi and n_zhi > 0:
            quota_stats["quota=zhi"] += 1
        elif quota == 0:
            quota_stats["quota=0"] += 1
        else:
            quota_stats["quota>zhi"] += 1
        nd = lev(new, e)
        base.append(bd)
        ds.append(nd)
        if new != g:
            changed += 1
        if nd < bd:
            better.append(r["id"])
        elif nd > bd:
            worse.append((r["id"], bd, nd, n_zhi, n_kore))

    ba, na = sum(base) / len(base), sum(ds) / len(ds)
    print("配额护栏（quota = 白文「之」数）：")
    print("  改写 %d | avgDist %.3f -> %.3f (%+.3f) | 改善 %d / 变差 %d | 精确 %d -> %d"
          % (changed, ba, na, na - ba, len(better), len(worse),
             sum(1 for x in base if x == 0), sum(1 for x in ds if x == 0)))
    print("  配额分布:", quota_stats)
    for w in worse[:10]:
        print("  !! %s base %d -> %d (白文之×%d, 输出これ×%d)" % w)

    # 对照：无限额全替换
    ds2 = [lev(norm(r["udkundoku_kakikudashi"]).replace("これ", "之"),
               norm(r["expected_kakikudashi"])) for r in rows]
    print("\n对照 全替换：avgDist %.3f (%+.3f)"
          % (sum(ds2) / len(ds2), sum(ds2) / len(ds2) - ba))

    with open(os.path.join(EV, "day11_align.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"base_avg": round(ba, 3), "quota_avg": round(na, 3),
                   "delta": round(na - ba, 3), "changed": changed,
                   "better": len(better), "worse": len(worse),
                   "worse_ids": [w[0] for w in worse]}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
