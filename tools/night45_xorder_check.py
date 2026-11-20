# -*- coding: utf-8 -*-
"""night45_xorder_check.py — I4：列单元内的 x 左右颠倒（NIGHT45 真 bug 度量）。

I2 发现过合并列单元后，本脚本量化其**后果**：

  I4 = 同一列单元内，x 区间不相交的两框，若左侧框出现在右侧框之前，
       即为一次「左右颠倒」。

竖排阅读方向是右→左，`_cluster_order` 的单元内部只按 y 排序；当两个 x 分离的
子列（通常是两个主栏）被一个跨列头注的 x 重叠桥接进同一单元时，两子列的 y
几乎相等（实测 p021 主栏 y=215 vs 217），y 排序的先后由 ±2px 噪声决定，
结果可能是左先右后 → 该列对的正文顺序整体颠倒。

产出: eval/night45_xorder.json
用法: python -X utf8 tools/night45_xorder_check.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools.night45_order_invariants import cluster_units  # noqa: E402

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night45_xorder.json")


def x_disjoint(a, b):
    return a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"]


def main():
    pages = []
    for fn in sorted(os.listdir(FULL)):
        if fn.endswith(".json"):
            with open(os.path.join(FULL, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    rows = []
    tot = 0
    bad_pages = []
    for p in pages:
        boxes = p["line_boxes"]
        if len(boxes) < 4:
            continue
        units = cluster_units(boxes)
        viol = []
        for k, (_ub, items) in enumerate(units):
            # items 已按 y 排序（= _cluster_order 的单元内输出顺序）
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    a, b = boxes[items[i]], boxes[items[j]]
                    if not x_disjoint(a, b):
                        continue
                    if a["x"] < b["x"]:   # 左框排在右框之前 → 颠倒
                        viol.append({"unit": k, "left_idx": items[i],
                                     "right_idx": items[j],
                                     "left_x": a["x"], "right_x": b["x"],
                                     "left_y": a["y"], "right_y": b["y"],
                                     "left_text": p["lines"][items[i]][:20],
                                     "right_text": p["lines"][items[j]][:20]})
        tot += len(viol)
        if viol:
            bad_pages.append(p["page"])
        rows.append({"page": p["page"], "n": len(boxes), "units": len(units),
                     "i4_inversions": len(viol), "detail": viol[:8]})

    print("== I4 列单元内左右颠倒 ==")
    print("pages=%d  I4 合计=%d  涉及页=%d → %s"
          % (len(rows), tot, len(bad_pages), "PASS" if tot == 0 else "FAIL"))
    print("违规页: %s" % (bad_pages or "无"))
    for r in rows:
        if not r["i4_inversions"]:
            continue
        print("\n--- %s  n=%d units=%d  I4=%d ---"
              % (r["page"], r["n"], r["units"], r["i4_inversions"]))
        for d in r["detail"]:
            print("  unit=%d  L(x=%4d y=%3d) %r" % (d["unit"], d["left_x"],
                                                    d["left_y"], d["left_text"]))
            print("            R(x=%4d y=%3d) %r" % (d["right_x"],
                                                     d["right_y"], d["right_text"]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"total_i4": tot, "pages_with_i4": bad_pages, "pages": rows},
                  f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night45_xorder.json")


if __name__ == "__main__":
    main()
