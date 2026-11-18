# -*- coding: utf-8 -*-
"""night22_compare.py — Night22 上线后真机评测 vs 前线归档对比 + 护栏审计。

对比 eval/night22_results_full.json（Rule C' 上线，真机 500 条）
与 eval/night21_results_full.json（上线前同一引擎 500 条）。
另：审计 archive 里 顧みて而して 的出现情况（护栏在真实语料里的足迹）。
"""
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with open(os.path.join(ROOT, "eval", name), encoding="utf-8") as f:
        return {r["id"]: r for r in json.load(f)["results"]}


def norm(s):
    return re.sub(r"\s+", "", s)


def lev(a, b):
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def bucket(src):
    n = len(norm(src))
    return "<=20" if n <= 20 else ("20-40" if n <= 40 else ">40")


def main():
    old = load("night21_results_full.json")
    new = load("night22_results_full.json")
    assert set(old) == set(new), "id 集不一致"
    n = len(new)
    imp = wor = fla = 0
    tot_old = tot_new = 0
    per_bucket = {}
    worst_changes = []
    for k in new:
        d_o = lev(norm(old[k]["udkundoku_kakikudashi"]), norm(old[k]["expected_kakikudashi"]))
        d_n = lev(norm(new[k]["udkundoku_kakikudashi"]), norm(new[k]["expected_kakikudashi"]))
        b = bucket(new[k]["hakubun"])
        pb = per_bucket.setdefault(b, [0, 0.0, 0.0, 0, 0, 0])
        pb[0] += 1
        pb[1] += d_o
        pb[2] += d_n
        if d_n < d_o:
            imp += 1
            pb[3] += 1
        elif d_n > d_o:
            wor += 1
            pb[4] += 1
        else:
            fla += 1
            pb[5] += 1
        tot_old += d_o
        tot_new += d_n
        if d_n != d_o:
            worst_changes.append((k, d_o, d_n))
    print("=== 真机 500 条：上线前 vs 上线后 ===")
    print("avgDist %.2f -> %.2f (%+.2f)  改善 %d / 变差 %d / 持平 %d (n=%d)"
          % (tot_old / n, tot_new / n, (tot_new - tot_old) / n, imp, wor, fla, n))
    for b in ("<=20", "20-40", ">40"):
        cnt, so, sn, i2, w2, f2 = per_bucket[b]
        print("  %-6s n=%3d avgDist %6.2f -> %6.2f (%+6.2f) 改善 %d / 变差 %d / 持平 %d"
              % (b, cnt, so / cnt, sn / cnt, (sn - so) / cnt, i2, w2, f2))
    print("\n=== 变差条目（若有，逐条列出）===")
    for k, d_o, d_n in sorted(worst_changes, key=lambda t: t[2] - t[1], reverse=True):
        if d_n > d_o:
            print("  %s %+d (%d->%d)" % (k, d_n - d_o, d_o, d_n))

    ex_o = sum(1 for r in old.values() if r["exact_match"])
    ex_n = sum(1 for r in new.values() if r["exact_match"])
    print("\n精确匹配 %d/%d -> %d/%d" % (ex_o, n, ex_n, n))

    # 护栏足迹：archive 里 顧みて而して
    cg_out = cg_exp = 0
    other_mite = 0
    for r in new.values():
        cg_out += r["udkundoku_kakikudashi"].count("顧みて而して")
        cg_exp += r["expected_kakikudashi"].count("顧みて而して")
        other_mite += len(re.findall(r"(?<!顧)みて而して", r["udkundoku_kakikudashi"]))
    print("\n=== 护栏足迹（500 条）===")
    print("输出含「顧みて而して」%d 处 / expected 含 %d 处；非顧み的「みて而して」输出 %d 处（已删）"
          % (cg_out, cg_exp, other_mite))

    # 与离线模拟的对账
    print("\n=== 与离线模拟对账 ===")
    print("模拟预测：avgDist 26.21 (-0.81)，改善 107 / 变差 0")
    print("真机实测：avgDist %.2f (%+.2f)，改善 %d / 变差 %d"
          % (tot_new / n, (tot_new - tot_old) / n, imp, wor))


if __name__ == "__main__":
    main()
