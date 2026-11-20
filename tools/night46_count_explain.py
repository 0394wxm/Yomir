# -*- coding: utf-8 -*-
"""night46_count_explain.py — 为什么「被滤框数」≠「被删行数」。

e2e 里 p012 被滤 17 框但只删 14 行、p014 被滤 38 框删 29 行、p017 被滤 14 框
删 12 行。原因应该是：**识别为空的框**（PARSeq 输出空串）本来就不产生行，
被滤掉也不减行数。本脚本核对这个解释，并给出逐页账目。

若解释成立：被滤框数 - 删行数 == 该页被滤框里「识别为空」的个数。

用法: python -X utf8 tools/night46_count_explain.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

E2E = os.path.join(ROOT, "eval", "night46_e2e.json")
OUT = os.path.join(ROOT, "eval", "night46_count_explain.json")


def main():
    d = json.load(open(E2E, encoding="utf-8"))
    rows = []
    for r in d["pages"]:
        off_lines = r["off_text"]
        on_lines = r["on_text"]
        dels = r["deleted_lines"]
        n_filtered = sum(r["reasons"].values())
        # 被滤框在 OFF 结果里对应的行数，最多 = 被滤框数
        gap = n_filtered - len(dels)
        # OFF 结果里空串/极短行的个数（PARSeq 空输出的典型形态）
        empty = sum(1 for x in off_lines if not x.strip())
        short = sum(1 for x in off_lines if len(x.strip()) <= 1)
        rows.append({"page": r["page"], "n_filtered": n_filtered,
                     "n_deleted": len(dels), "gap": gap,
                     "n_empty_in_off": empty, "n_short_in_off": short,
                     "gap_explained_by_empty": gap <= empty})
        print("%s  被滤 %2d  删行 %2d  差 %d   OFF 空行 %d  1字行 %d   %s"
              % (r["page"], n_filtered, len(dels), gap, empty, short,
                 "OK" if gap <= empty else "需查"))

    print("\n== 结论 ==")
    print("差值为 0 的页: %s"
          % [r["page"] for r in rows if r["gap"] == 0])
    print("差值 > 0 的页: %s"
          % [(r["page"], r["gap"], r["n_empty_in_off"])
             for r in rows if r["gap"] > 0])
    print("差值能否由 OFF 空行解释: %s"
          % ("全部可以" if all(r["gap_explained_by_empty"] for r in rows)
             else "有页不能"))
    print("\n注：OFF 线的 '空行' 计数是 0 时，说明 PARSeq 对这些框输出的是")
    print("    极短串（1-2 字）而非空串，那些短行在被滤后从行列表消失。")

    # 逐页列出 OFF 里 1 字行（这些最可能是被滤框的空/噪声输出）
    print("\n== OFF 线里的极短行（≤2 字，疑似被滤框的噪声输出）==")
    for r in d["pages"]:
        short = [x for x in r["off_text"] if 0 < len(x.strip()) <= 2]
        if short:
            print("  %s (%d): %s" % (r["page"], len(short), short[:12]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"pages": rows}, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night46_count_explain.json")


if __name__ == "__main__":
    main()
