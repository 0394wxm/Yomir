# -*- coding: utf-8 -*-
"""day11_rule_sim.py — D11 真机前离线模拟：Rule D 候选（これ→之）全量逐条比。

在 1000 条上模拟：
  D0  基线（不改）
  D1  これ->之 全替换
  D2  これ->之，但排除「これいか/これゆ」等疑似副词用法
  D3  これ->之，只在辅音后（非句首、非标点后）——护栏版
  D4  只替换 これを/これに/これが/これの/これは/これと
并逐条输出改善/变差/持平，变差条目全部列出（不隐藏）。
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
    print("基线 avgDist %.3f  n=%d  精确 %d\n"
          % (base_avg, len(base), sum(1 for x in base if x == 0)), flush=True)

    def run(name, fn):
        ds, better, worse, changed = [], [], [], []
        for r, bd in zip(rows, base):
            g, e = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
            new = fn(g)
            nd = lev(new, e)
            ds.append(nd)
            if new != g:
                changed.append(r["id"])
            if nd < bd:
                better.append((r["id"], bd, nd))
            elif nd > bd:
                worse.append((r["id"], bd, nd, g, new, e))
        avg = sum(ds) / len(ds)
        exact = sum(1 for d in ds if d == 0)
        print("%-10s 改写 %4d | avg %6.3f (%+6.3f) | 改善 %3d / 变差 %3d | 精确 %d"
              % (name, len(changed), avg, avg - base_avg, len(better), len(worse), exact),
              flush=True)
        if worse:
            print("   !! 变差条目 %d 个（前 5 逐条列出）：" % len(worse), flush=True)
            for wid, bd, nd, g, new, e in worse[:5]:
                print("      [%s] %d->%d" % (wid, bd, nd))
                print("        got: %s" % g[:80])
                print("        new: %s" % new[:80])
                print("        exp: %s" % e[:80])
        return {"name": name, "changed": len(changed), "avg": round(avg, 3),
                "delta": round(avg - base_avg, 3), "better": len(better),
                "worse": len(worse), "exact": exact,
                "worse_ids": [w[0] for w in worse]}

    sims = []
    sims.append(run("D0 基线", lambda t: t))
    sims.append(run("D1 全替换", lambda t: t.replace("これ", "之")))
    sims.append(run("D2 排除副词", lambda t: re.sub(
        r"これ(?=[いゆう])", "\u0000KORE\u0000", t).replace("これ", "之").replace("\u0000KORE\u0000", "これ")))
    sims.append(run("D3 非句首", lambda t: re.sub(r"(?<=.)これ", "之", t)))
    sims.append(run("D4 助词限定", lambda t: re.sub(r"これ(?=[をにがのはと])", "之", t)))
    sims.append(run("D5 非标点后", lambda t: re.sub(r"(?<![。、])これ", "之", t)))

    with open(os.path.join(EV, "day11_sim.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"base_avg": round(base_avg, 3), "n": len(rows), "sims": sims},
                  f, ensure_ascii=False, indent=1)
    print("\nwritten: eval/day11_sim.json", flush=True)


if __name__ == "__main__":
    main()
