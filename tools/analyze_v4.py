# -*- coding: utf-8 -*-
"""analyze_v4.py — REPORT_DAY9 用的细项统计。

1) v4 相对「当前生产线同口径」的对比（v2，无 Rule C；v3 带 Rule C 作为历史参照单独列）
2) 而して 影响量化：v4 输出含「而して」且 expected 不含的条数
3) 500 条里唯一 exact 的是哪条
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


def norm(s):
    return re.sub(r"\s+", "", s)


def main():
    v2 = load("night4_results_full_v2.json")
    v3 = load("night5_results_full_v3.json")
    v4 = load("night21_results_full_v4.json")

    print("=== 1) 而して 影响（200 条）===")
    hit = [k for k in v4 if "而して" in v4[k]["udkundoku_kakikudashi"]
           and "而して" not in v4[k]["expected_kakikudashi"]]
    print("v4 输出含「而して」而 expected 不含：%d 条" % len(hit))
    hit_v3 = [k for k in v3 if "而して" in v3[k]["udkundoku_kakikudashi"]
              and "而して" not in v3[k]["expected_kakikudashi"]]
    print("v3 同样统计：%d 条" % len(hit_v3))
    # 去掉而して 再比（只看其余部分是否接近）
    better = 0
    worse = 0
    for k in v4:
        a = norm(v4[k]["udkundoku_kakikudashi"]).replace("而して", "")
        b = norm(v4[k]["expected_kakikudashi"])
        c = norm(v3[k]["udkundoku_kakikudashi"]).replace("而して", "")
        da, dc = lev(a, b), lev(c, b)
        if da < dc:
            better += 1
        elif da > dc:
            worse += 1
    print("把「而して」从两侧输出里剔除后：v4 vs v3 改善 %d / 变差 %d / 持平 %d"
          % (better, worse, len(v4) - better - worse))

    print("\n=== 2) 同口径对比：v4 vs v2（v2 = Night7 撤销 Rule C 后的生产线语义）===")
    for label, ref in [("v2", v2), ("v3", v3)]:
        d4 = [v4[k]["edit_distance"] for k in v4]
        dr = [ref[k]["edit_distance"] for k in v4]
        b = sum(1 for k in v4 if v4[k]["edit_distance"] < ref[k]["edit_distance"])
        w = sum(1 for k in v4 if v4[k]["edit_distance"] > ref[k]["edit_distance"])
        print("%s avgDist %.3f -> v4 %.3f (%+.3f)  改善 %d / 变差 %d / 持平 %d"
              % (label, sum(dr) / len(dr), sum(d4) / len(d4),
                 (sum(d4) - sum(dr)) / len(dr), b, w, len(v4) - b - w))

    print("\n=== 3) Rule C 的 26 条在 v4 下的表现 ===")
    rc = [k for k in v3 if "而して" in v2[k]["udkundoku_kakikudashi"]
          and "而して" not in v3[k]["udkundoku_kakikudashi"]]
    print("v3 相对 v2 去掉「而して」的条目：%d 条" % len(rc))
    if rc:
        d2 = sum(v2[k]["edit_distance"] for k in rc) / len(rc)
        d3 = sum(v3[k]["edit_distance"] for k in rc) / len(rc)
        d4 = sum(v4[k]["edit_distance"] for k in rc) / len(rc)
        print("这 %d 条 avgDist：v2 %.2f / v3 %.2f / v4 %.2f" % (len(rc), d2, d3, d4))

    print("\n=== 4) 500 条 exact 条目 ===")
    big3 = load("night21_results_full.json")
    big4 = load("night21_results_full_v4_500.json")
    ex = [k for k in big4 if big4[k]["exact_match"]]
    for k in ex:
        r = big4[k]
        print("%s  dist=%s" % (k, r["edit_distance"]))
        print("  白文: %s" % r["hakubun"])
        print("  期待: %s" % r["expected_kakikudashi"])
        print("  v4  : %s" % r["udkundoku_kakikudashi"].replace("\n", " / "))
        print("  v3  : %s" % big3[k]["udkundoku_kakikudashi"].replace("\n", " / "))

    print("\n=== 5) 500 条 而して 影响 ===")
    h4 = [k for k in big4 if "而して" in big4[k]["udkundoku_kakikudashi"]
          and "而して" not in big4[k]["expected_kakikudashi"]]
    h3 = [k for k in big3 if "而して" in big3[k]["udkundoku_kakikudashi"]
          and "而して" not in big3[k]["expected_kakikudashi"]]
    print("v3 %d 条 / v4 %d 条" % (len(h3), len(h4)))
    better = worse = 0
    for k in big4:
        a = norm(big4[k]["udkundoku_kakikudashi"]).replace("而して", "")
        b = norm(big4[k]["expected_kakikudashi"])
        c = norm(big3[k]["udkundoku_kakikudashi"]).replace("而して", "")
        da, dc = lev(a, b), lev(c, b)
        if da < dc:
            better += 1
        elif da > dc:
            worse += 1
    print("剔除「而して」后 v4 vs v3：改善 %d / 变差 %d / 持平 %d"
          % (better, worse, len(big4) - better - worse))


if __name__ == "__main__":
    main()
