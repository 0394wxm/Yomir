# -*- coding: utf-8 -*-
"""night22_sodashite_scan.py — Night 22：「而して」去留判别的数据解剖。

数据源：eval/night21_results_full.json（500 条，当前生产线语义，Night 21 产出）。
问题：引擎在 151 条里输出了 expected 不含的「而して」；无条件剔除净赚 -0.84 avgDist
但会弄坏「顧みて而して他を言う」这类规范训读（Night 7 撤销 Rule C 的原因）。
本脚本回答：
  1) 四象限计数（输出有/无 × expected 有/无）
  2) keep 类（expected 含而して）与 delete 类（输出含、expected 不含）在白文层的
     表面特征分布：而 的个数、首个 而 前一字符类别、句长
  3) keep 类里引擎是否已经输出了而して（判断「全删规则」的真实代价）
输出：stdout + eval/night22_sodashite_scan.json
"""
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PUNCT = "、。．，,.;:：；！？「」『』()（）・\n "


def char_class(c):
    if c is None:
        return "BOS"
    if c in PUNCT:
        return "punct"
    if re.match(r"[ぁ-ゖァ-ヺ]", c):
        return "kana"
    if re.match(r"[㆐-㆓ㆠ㆟㆑一二三四五六七八九十上中下]", c):
        return "kaeriten"
    return "kanji"


def main():
    with open(os.path.join(ROOT, "eval", "night21_results_full.json"), encoding="utf-8") as f:
        results = json.load(f)["results"]

    quad = Counter()
    keep_cases, delete_cases = [], []
    for r in results:
        out = r["udkundoku_kakikudashi"]
        exp = r["expected_kakikudashi"]
        src = r["hakubun"]
        o, e = "而して" in out, "而して" in exp
        quad[(o, e)] += 1
        feat = {
            "id": r["id"],
            "n_eru": src.count("而"),
            "len": len(re.sub(r"\s+", "", src)),
            "prev1": char_class(src[src.index("而") - 1]) if "而" in src else "no而",
            "dist": r["edit_distance"],
        }
        if e:
            keep_cases.append({**feat, "src": src, "exp": exp, "out_has": o})
        elif o:
            delete_cases.append({**feat, "src": src, "exp": exp})

    print("=== 1) 四象限（输出含而して? × expected含而します?）===")
    for (o, e), n in sorted(quad.items(), reverse=True):
        print("  out=%-5s exp=%-5s : %4d" % (o, e, n))

    print("\n=== 2) keep 类（expected 含而して，n=%d）===" % len(keep_cases))
    print("  引擎也输出而而して 的：%d / %d" % (sum(1 for k in keep_cases if k["out_has"]), len(keep_cases)))
    for k in keep_cases:
        print("  %-14s 而x%d prev=%-8s len=%3d dist=%3d out_has=%s | %s"
              % (k["id"], k["n_eru"], k["prev1"], k["len"], k["dist"], k["out_has"], k["src"][:24]))

    print("\n=== 3) 两类的表面特征分布 ===")
    for name, cases in [("keep", keep_cases), ("delete", delete_cases)]:
        pc = Counter(c["prev1"] for c in cases)
        nc = Counter(c["n_eru"] for c in cases)
        print("  %-6s n=%3d  prev1: %s" % (name, len(cases), dict(pc.most_common())))
        print("  %-6s         而的个数: %s" % (name, dict(sorted(nc.items()))))

    print("\n=== 4) delete 类按 prev1 细分（找可分的表面特征）===")
    for cls in ["BOS", "punct", "kana", "kaeriten", "kanji", "no而"]:
        sub = [c for c in delete_cases if c["prev1"] == cls]
        if sub:
            print("  prev1=%-8s n=%3d  平均dist=%.1f" % (cls, len(sub), sum(c["dist"] for c in sub) / len(sub)))

    # 找经典句
    classic = [r for r in results if "顧左右而言他" in r["hakubun"] or "顧みて而して" in r["expected_kakikudashi"]]
    print("\n=== 5) 经典句定位 ===")
    for r in classic:
        print("  %s | 白文 %s | expected %s | 输出 %s | dist %s"
              % (r["id"], r["hakubun"], r["expected_kakikudashi"],
                 r["udkundoku_kakikudashi"].replace("\n", "/"), r["edit_distance"]))

    out = {
        "quadrant": {"%s_%s" % (o, e): n for (o, e), n in quad.items()},
        "keep_n": len(keep_cases),
        "keep_out_has": sum(1 for k in keep_cases if k["out_has"]),
        "delete_n": len(delete_cases),
        "keep_prev1": dict(Counter(k["prev1"] for k in keep_cases)),
        "delete_prev1": dict(Counter(c["prev1"] for c in delete_cases)),
        "keep_ids": [k["id"] for k in keep_cases],
        "delete_ids": [c["id"] for c in delete_cases],
    }
    with open(os.path.join(ROOT, "eval", "night22_sodashite_scan.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\n写入 eval/night22_sodashite_scan.json")


if __name__ == "__main__":
    main()
