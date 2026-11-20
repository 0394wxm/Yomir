# -*- coding: utf-8 -*-
"""night49_pair_quality.py — 区分「真割注对」与「伪配对」，量真实颠倒率。

night49_diagnose 显示 56 个颠倒里 54 个同单元、多数 dy(L-R) = -1..-3
（两半顶端只差几个像素，单元内 sorted(key=y) 把左半排前面）。

但在设计修法前必须先回答：这些「对」有多少是真的割注？
Night48 的成对判据很松（gap <= 1.2*wmed、y 重合 >= 0.7*min(h)），
p009 的 '十歳集九草'(y=156 h=63) 配 '和字、外属下…'(y=53 h=166)
明显是**短碎片 vs 全高列**，不是并排割注。

分层：
  A 严格割注：gap < 0.15*wmed ∧ |Δh| <= 0.15*max(h) ∧ |dy_top| <= 0.05*h
  B 宽松并排：gap < 0.15*wmed ∧ y 顶对齐（|dy_top| <= 0.05*h），不要求等高
  C 其余（含垂直错位/不等高的伪配对）

对每层报右先率，并给出 A 层的 dy 分布（用于选 tie 容差）。

产出: eval/night49_pair_quality.json
用法: python -X utf8 tools/night49_pair_quality.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

D = os.path.join(ROOT, "eval", "night49_diagnose.json")
OUT = os.path.join(ROOT, "eval", "night49_pair_quality.json")


def main():
    d = json.load(open(D, encoding="utf-8"))
    rows = d["rows"]

    def cls(x):
        top_aligned = abs(x["dy_left_minus_right"]) <= 0.05 * max(
            x["r"]["h"], x["l"]["h"])
        tight = x["gap_rel"] < 0.15
        hclose = x["dh"] <= 0.15 * max(x["r"]["h"], x["l"]["h"])
        if tight and top_aligned and hclose:
            return "A_strict"
        if tight and top_aligned:
            return "B_sidelined"
        return "C_loose"

    buckets = {"A_strict": [], "B_sidelined": [], "C_loose": []}
    for x in rows:
        buckets[cls(x)].append(x)

    print("== 配对质量分层 ==")
    print("%-12s %5s %7s %9s" % ("层", "n", "右先", "右先率"))
    for k in ("A_strict", "B_sidelined", "C_loose"):
        sub = buckets[k]
        ok = sum(1 for x in sub if x["right_first"])
        print("%-12s %5d %7d %8.1f%%"
              % (k, len(sub), ok, 100.0 * ok / max(1, len(sub))))

    print("\n== A 层（真割注）颠倒明细 ==")
    badA = [x for x in buckets["A_strict"] if not x["right_first"]]
    print("  颠倒 %d / %d" % (len(badA), len(buckets["A_strict"])))
    import collections
    dyc = collections.Counter(x["dy_left_minus_right"] for x in badA)
    print("  dy(L-R) 分布:", sorted(dyc.items()))
    dya = collections.Counter(x["dy_left_minus_right"]
                              for x in buckets["A_strict"]
                              if x["right_first"])
    print("  右先对 dy(L-R) 分布:", sorted(dya.items())[:15], "...")

    print("\n== 各层 |dy| 分布（选容差）==")
    for k in ("A_strict", "B_sidelined", "C_loose"):
        dys = sorted(abs(x["dy_left_minus_right"]) for x in buckets[k])
        if not dys:
            continue
        print("  %-12s n=%3d  |dy| 中位=%d p90=%d max=%d  <=3px:%d"
              % (k, len(dys), dys[len(dys) // 2],
                 dys[int(0.9 * (len(dys) - 1))], dys[-1],
                 sum(1 for v in dys if v <= 3)))

    print("\n== A 层颠倒的页面 ==")
    pc = collections.Counter(x["page"] for x in badA)
    print("  ", dict(sorted(pc.items())))
    print("\n== A 层按 dy 符号 ==")
    neg = sum(1 for x in badA if x["dy_left_minus_right"] < 0)
    pos = sum(1 for x in badA if x["dy_left_minus_right"] > 0)
    zero = sum(1 for x in badA if x["dy_left_minus_right"] == 0)
    print("  左半更高(负) %d / 左半更低(正) %d / 相等 %d" % (neg, pos, zero))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({k: {"n": len(v),
                       "right_first": sum(1 for x in v if x["right_first"]),
                       "rows": v}
                   for k, v in buckets.items()}, f,
                  ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_pair_quality.json")


if __name__ == "__main__":
    main()
