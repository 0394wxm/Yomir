# -*- coding: utf-8 -*-
"""day11_kore.py — 深挖「これ→之」候选：区分真指示代词 vs 汉文「之」的训读。

核心问题：日语里真正的指示代词「これ」应该写假名，但引擎对汉文助词「之」
一律训读为「これ」。要上线必须找一个**表面信号**把两者分开。

本脚本枚举候选护栏，逐个数改善/变差。
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

    base = [lev(norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])) for r in rows]
    base_avg = sum(base) / len(base)
    print("基线 avgDist %.2f  n=%d" % (base_avg, len(base)), flush=True)

    # 分布：每条里 これ 的次数 / expected 里 之 的次数
    print("\n=== 每条 (これ 次数, 之 次数) 分布 ===", flush=True)
    dist = collections.Counter()
    for r in rows:
        g, e = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        dist[(g.count("これ"), e.count("之"))] += 1
    for (a, b), n in sorted(dist.items(), key=lambda kv: -kv[1])[:12]:
        print("  これ×%d  之×%d : %d 条" % (a, b, n), flush=True)

    # 关键检验：expected 里既没有 之 也没有 これ 却出现 これ 的条目 = 真·误判风险
    print("\n=== 风险条目（expected 无「之」也无「これ」但有「これ」）===", flush=True)
    risky = []
    for r in rows:
        g, e = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        if "これ" in g and "之" not in e and "これ" not in e:
            risky.append(r)
    print("  共 %d 条" % len(risky), flush=True)
    for r in risky[:6]:
        print("  [%s]" % r["id"])
        print("    got: %s" % norm(r["udkundoku_kakikudashi"])[:100])
        print("    exp: %s" % norm(r["expected_kakikudashi"])[:100])

    # ---- 候选护栏模拟 ----
    def simulate(name, fn):
        ds, better, worse, changed = [], 0, 0, 0
        for r, bd in zip(rows, base):
            g = norm(r["udkundoku_kakikudashi"])
            e = norm(r["expected_kakikudashi"])
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
        print("  %-40s 改写 %4d | avg %6.2f (%+6.2f) | 改善 %3d / 变差 %3d"
              % (name, changed, avg, avg - base_avg, better, worse), flush=True)
        return {"name": name, "changed": changed, "avg": round(avg, 3),
                "delta": round(avg - base_avg, 3), "better": better, "worse": worse}

    print("\n=== 候选规则模拟 ===", flush=True)
    sims = []
    sims.append(simulate("R1 全替换 これ->之", lambda t: t.replace("これ", "之")))
    sims.append(simulate("R2 只替换「これを」->「之を」", lambda t: t.replace("これを", "之を")))
    sims.append(simulate("R3 替换 これ+に/を/が/は", 
                         lambda t: re.sub(r"これ(?=[にをがは])", "之", t)))
    sims.append(simulate("R4 只替换「これを」「これに」", 
                         lambda t: t.replace("これを", "之を").replace("これに", "之に")))
    sims.append(simulate("R5 只替换「これを」", lambda t: t.replace("これを", "之を")))
    sims.append(simulate("R6 これ+X(单字助词) 且非句首",
                         lambda t: re.sub(r"(?<=.)これ(?=[をにがはの])", "之", t)))

    # R5 细节：改写后逐条看变差的
    print("\n=== R5 变差明细 ===", flush=True)
    n_bad = 0
    for r, bd in zip(rows, base):
        g, e = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        new = g.replace("これを", "之を")
        if new == g:
            continue
        nd = lev(new, e)
        if nd > bd and n_bad < 8:
            n_bad += 1
            print("  [%s] dist %d->%d" % (r["id"], bd, nd))
            print("    got: %s" % g[:90])
            print("    new: %s" % new[:90])
            print("    exp: %s" % e[:90])

    with open(os.path.join(EV, "day11_kore.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"base_avg": round(base_avg, 3), "sims": sims,
                   "risky_n": len(risky),
                   "risky_ids": [r["id"] for r in risky]}, f, ensure_ascii=False, indent=1)
    print("\nwritten: eval/day11_kore.json", flush=True)


if __name__ == "__main__":
    main()
