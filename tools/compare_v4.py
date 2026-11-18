# -*- coding: utf-8 -*-
"""compare_v4.py — full_v4（guwenbert）vs 规则引擎各轮的同一把尺子对比。

用法:
  python tools/compare_v4.py 200
  python tools/compare_v4.py 500
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with open(os.path.join(ROOT, "eval", name), encoding="utf-8") as f:
        return {r["id"]: r for r in json.load(f)["results"]}


def stats(d):
    ds = [r["edit_distance"] for r in d.values() if r.get("edit_distance") is not None]
    ex = sum(1 for r in d.values() if r.get("exact_match"))
    return ex, len(d), sum(ds) / len(ds)


def bucket(s):
    n = len(s)
    if n <= 20:
        return "<=20"
    if n <= 40:
        return "20-40"
    return ">40"


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    if n == 200:
        base = load("night4_results_baseline.json")
        v1 = load("night4_results_full_v1.json")
        v2 = load("night4_results_full_v2.json")
        v3 = load("night5_results_full_v3.json")
        v4 = load("night21_results_full_v4.json")
    else:
        full = load("night21_results_full.json")
        v3 = full
        v4 = load("night21_results_full_v4_500.json")
        base = v2 = v1 = None

    print("=== %d 条总表 ===" % n)
    for name, d in [("baseline", base), ("v1", v1), ("v2", v2), ("v3", v3), ("v4", v4)]:
        if d is None:
            continue
        ex, tot, avg = stats(d)
        print("%-9s exact %d/%d  avgDist %.2f" % (name, ex, tot, avg))

    def cmp(label, a, b):
        better = sum(1 for k in a if b[k]["edit_distance"] < a[k]["edit_distance"])
        worse = sum(1 for k in a if b[k]["edit_distance"] > a[k]["edit_distance"])
        print("%s: 改善 %d / 变差 %d / 持平 %d"
              % (label, better, worse, len(a) - better - worse))
        return better, worse

    if base:
        cmp("v4 vs baseline", base, v4)
        cmp("v4 vs v1", v1, v4)
        cmp("v4 vs v2", v2, v4)
        cmp("v4 vs v3", v3, v4)

    print("\n=== 分档（白文字符长度）===")
    ids = list(v4)
    buckets = {}
    for k in ids:
        buckets.setdefault(bucket(v4[k]["hakubun"]), []).append(k)
    print("%-8s %4s %10s %10s %10s" % ("档", "n", "v3 avgDist", "v4 avgDist", "delta"))
    for bk in ["<=20", "20-40", ">40"]:
        ks = buckets.get(bk, [])
        if not ks:
            continue
        d3 = [v3[k]["edit_distance"] for k in ks if v3.get(k) and v3[k].get("edit_distance") is not None]
        d4 = [v4[k]["edit_distance"] for k in ks if v4[k].get("edit_distance") is not None]
        a3, a4 = sum(d3) / len(d3), sum(d4) / len(d4)
        print("%-8s %4d %10.2f %10.2f %+10.2f" % (bk, len(ks), a3, a4, a4 - a3))
        b = sum(1 for k in ks if v4[k]["edit_distance"] < v3[k]["edit_distance"])
        w = sum(1 for k in ks if v4[k]["edit_distance"] > v3[k]["edit_distance"])
        print("         改善 %d / 变差 %d / 持平 %d" % (b, w, len(ks) - b - w))

    print("\n=== v4 较 v3 变差最多的 15 条 ===")
    regs = sorted(((k, v3[k]["edit_distance"], v4[k]["edit_distance"]) for k in v3
                   if k in v4 and v4[k]["edit_distance"] is not None
                   and v4[k]["edit_distance"] > v3[k]["edit_distance"]),
                  key=lambda t: t[2] - t[1], reverse=True)
    for k, a, b in regs[:15]:
        print("  %-14s %3d -> %3d  (%+d)" % (k, a, b, b - a))
    if not regs:
        print("  (无)")

    print("\n=== v4 较 v3 改善最多的 15 条 ===")
    imps = sorted(((k, v3[k]["edit_distance"], v4[k]["edit_distance"]) for k in v3
                   if k in v4 and v4[k]["edit_distance"] is not None
                   and v4[k]["edit_distance"] < v3[k]["edit_distance"]),
                  key=lambda t: t[1] - t[2], reverse=True)
    for k, a, b in imps[:15]:
        print("  %-14s %3d -> %3d  (%+d)" % (k, a, b, b - a))
    if not imps:
        print("  (无)")


if __name__ == "__main__":
    main()
