# -*- coding: utf-8 -*-
"""analyze_v4b.py — 分档统计（对当前生产线口径 v2 / night21-500）与失败模式粗分。"""
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


def bucket(s):
    n = len(s)
    return "<=20" if n <= 20 else ("20-40" if n <= 40 else ">40")


def table(title, ref, v4):
    print("=== %s ===" % title)
    buckets = {}
    for k in v4:
        buckets.setdefault(bucket(v4[k]["hakubun"]), []).append(k)
    print("%-8s %4s %10s %10s %10s %-24s" % ("档", "n", "ref", "v4", "delta", "改善/变差/持平"))
    for bk in ["<=20", "20-40", ">40"]:
        ks = buckets.get(bk, [])
        if not ks:
            continue
        dr = [ref[k]["edit_distance"] for k in ks]
        d4 = [v4[k]["edit_distance"] for k in ks]
        b = sum(1 for k in ks if v4[k]["edit_distance"] < ref[k]["edit_distance"])
        w = sum(1 for k in ks if v4[k]["edit_distance"] > ref[k]["edit_distance"])
        print("%-8s %4d %10.2f %10.2f %+10.2f %d/%d/%d"
              % (bk, len(ks), sum(dr) / len(dr), sum(d4) / len(d4),
                 (sum(d4) - sum(dr)) / len(dr), b, w, len(ks) - b - w))
    tot_r = sum(ref[k]["edit_distance"] for k in v4) / len(v4)
    tot_4 = sum(v4[k]["edit_distance"] for k in v4) / len(v4)
    print("%-8s %4d %10.2f %10.2f %+10.2f" % ("合计", len(v4), tot_r, tot_4, tot_4 - tot_r))
    print()


def main():
    v2 = load("night4_results_full_v2.json")
    v3 = load("night5_results_full_v3.json")
    v4 = load("night21_results_full_v4.json")
    big3 = load("night21_results_full.json")
    big4 = load("night21_results_full_v4_500.json")

    table("200 条：v4 vs v2（=Night7 后当前生产线语义）", v2, v4)
    table("200 条：v4 vs v3（历史口径，含已撤销 Rule C）", v3, v4)
    table("500 条：v4 vs 规则引擎（night21_results_full，当前生产线语义）", big3, big4)

    print("=== 500 条档位分布（v4 输出长度无关，用白文长度）===")
    c = Counter(bucket(big4[k]["hakubun"]) for k in big4)
    print(dict(c))

    print("\n=== 500 条：v4 每个档的精确匹配 ===")
    for bk in ["<=20", "20-40", ">40"]:
        ks = [k for k in big4 if bucket(big4[k]["hakubun"]) == bk]
        print("%-6s exact %d/%d" % (bk, sum(1 for k in ks if big4[k]["exact_match"]), len(ks)))

    print("\n=== 失败模式粗分（500 条 v4 输出 vs expected，字符串级不计语义）===")
    pat = {
        "多出而して": lambda g, e: "而して" in g and "而して" not in e,
        "多出は": lambda g, e: g.count("は") > e.count("は"),
        "缺は": lambda g, e: g.count("は") < e.count("は"),
        "多出を": lambda g, e: g.count("を") > e.count("を"),
        "缺を": lambda g, e: g.count("を") < e.count("を"),
        "多出に": lambda g, e: g.count("に") > e.count("に"),
        "缺に": lambda g, e: g.count("に") < e.count("に"),
        "未做ふ→う(输出含ふ)": lambda g, e: "ふ" in g and "ふ" not in e,
    }
    for name, fn in pat.items():
        n4 = sum(1 for k in big4 if fn(re.sub(r"\s+", "", big4[k]["udkundoku_kakikudashi"]),
                                        re.sub(r"\s+", "", big4[k]["expected_kakikudashi"])))
        n3 = sum(1 for k in big3 if fn(re.sub(r"\s+", "", big3[k]["udkundoku_kakikudashi"]),
                                        re.sub(r"\s+", "", big3[k]["expected_kakikudashi"])))
        print("%-20s v3 %3d 条 / v4 %3d 条" % (name, n3, n4))

    print("\n=== 长度极值 ===")
    ks = sorted(big4, key=lambda k: len(big4[k]["hakubun"]))
    for k in ks[:3] + ks[-3:]:
        print("%-14s 白文%3d字 v3=%3d v4=%3d" % (k, len(big4[k]["hakubun"]),
                                                big3[k]["edit_distance"], big4[k]["edit_distance"]))


if __name__ == "__main__":
    main()
