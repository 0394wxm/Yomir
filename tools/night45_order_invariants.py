# -*- coding: utf-8 -*-
"""night45_order_invariants.py — 阅读顺序的三条真实不变式 + 过合并诊断（NIGHT45）。

背景：Night45 原假设「头注被 cluster 切开」经检验**不成立**——
`_cluster_order` 以列单元为整体输出，列连续性（同一列是否连续出现）是
**构造性质**，47 页恒为 0 段打断。原 `night45_headnote_check.py` 的
「违规」来自一个错误的不变式（把所有非主栏框都当作「必须排在所属列正文
之前」的头注，把列中/列末割注也算进去），并与 P1 的构造同源 → 循环论证。

本脚本改用三条**可证伪**的判据：

  I1 列内 y 单调：同一列（`_cluster_order` 的单元定义）内，输出位置递增时
     y 必须非降。违反 = 列内上下颠倒。
  I2 列带内不串列：同一列内任意两框的 x 区间，其「并集宽度」不得超过
     该列最宽框宽度的 OVER_MERGE_FACTOR 倍。违反 = 传递闭包把不同 x
     位置并成了一列（头注被挂到错的列）。
  I3 主栏列序右→左：主栏（`_main_group`）各列按右缘 x 严格降序。

诊断输出逐页计数，不存全文。

产出: eval/night45_invariants.json
用法: python -X utf8 tools/night45_order_invariants.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import _main_group  # noqa: E402

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night45_invariants.json")

COL_OVERLAP = 0.4        # 与 _cluster_order 的列聚类阈值同值
OVER_MERGE_FACTOR = 2.0  # 列内 x 并集宽度 / 列内最宽框宽 的上限


def ov_x(a, b):
    lo = max(a["x"], b["x"])
    hi = min(a["x"] + a["w"], b["x"] + b["w"])
    return max(0, hi - lo) / max(1, min(a["w"], b["w"]))


def cluster_units(boxes):
    """复刻 `_cluster_order` 的竖排列单元构造（只用竖排框）。

    返回 [(unit_box, [box_index...]), ...]，units 按质心 x 右→左。
    """
    vert = [i for i, b in enumerate(boxes) if b["h"] >= b["w"]]
    units = []
    for i in sorted(vert, key=lambda i: -(boxes[i]["x"] + boxes[i]["w"])):
        b = boxes[i]
        for u in units:
            if ov_x(u["box"], b) >= COL_OVERLAP:
                u["items"].append(i)
                u["box"] = {
                    "x": min(u["box"]["x"], b["x"]),
                    "y": min(u["box"]["y"], b["y"]),
                    "w": max(u["box"]["x"] + u["box"]["w"], b["x"] + b["w"])
                    - min(u["box"]["x"], b["x"]),
                    "h": max(u["box"]["y"] + u["box"]["h"], b["y"] + b["h"])
                    - min(u["box"]["y"], b["y"]),
                }
                break
        else:
            units.append({"box": dict(b), "items": [i]})
    units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
    return [(u["box"], sorted(u["items"], key=lambda i: boxes[i]["y"]))
            for u in units]


def main():
    pages = []
    for fn in sorted(os.listdir(FULL)):
        if fn.endswith(".json"):
            with open(os.path.join(FULL, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    rows = []
    tot_i1 = tot_i2 = tot_units = 0
    pages_i1 = pages_i2 = 0
    pages_i3 = 0
    worst_ratio = []

    for p in pages:
        boxes = p["line_boxes"]
        if len(boxes) < 4:
            continue
        units = cluster_units(boxes)

        # I1：列内 y 单调（输出位置 = 框下标，因为 A 顺序就是 line_boxes 下标序）
        i1 = 0
        for _ub, items in units:
            for a, b in zip(items, items[1:]):
                if boxes[b]["y"] < boxes[a]["y"]:
                    i1 += 1

        # I2：列内 x 并集宽度 / 列内最宽框宽
        i2 = 0
        ratios = []
        for _ub, items in units:
            if len(items) < 2:
                continue
            lo = min(boxes[i]["x"] for i in items)
            hi = max(boxes[i]["x"] + boxes[i]["w"] for i in items)
            wmax = max(boxes[i]["w"] for i in items)
            r = (hi - lo) / max(1, wmax)
            ratios.append(r)
            if r > OVER_MERGE_FACTOR:
                i2 += 1
        if ratios:
            worst_ratio.append((p["page"], round(max(ratios), 2),
                                len(units), len(boxes)))

        # I3：主栏列序右→左
        _miban, main = _main_group([dict(b) for b in boxes])
        mk = {(b["x"], b["y"], b["w"], b["h"]) for b in main}
        mi = [i for i, b in enumerate(boxes)
              if (b["x"], b["y"], b["w"], b["h"]) in mk]
        mcols = []
        for i in sorted(mi, key=lambda i: -(boxes[i]["x"] + boxes[i]["w"])):
            b = boxes[i]
            for c in mcols:
                if any(ov_x(b, boxes[j]) >= COL_OVERLAP for j in c):
                    c.append(i)
                    break
            else:
                mcols.append([i])
        mcols.sort(key=lambda c: -max(boxes[i]["x"] + boxes[i]["w"] for i in c))
        rights = [max(boxes[i]["x"] + boxes[i]["w"] for i in c) for c in mcols]
        i3 = all(rights[k] > rights[k + 1] for k in range(len(rights) - 1))

        tot_i1 += i1
        tot_i2 += i2
        tot_units += len(units)
        pages_i1 += 1 if i1 else 0
        pages_i2 += 1 if i2 else 0
        pages_i3 += 0 if i3 else 1
        rows.append({"page": p["page"], "n": len(boxes), "units": len(units),
                     "i1_y_inversions": i1, "i2_over_merged_units": i2,
                     "i3_main_right_to_left": i3,
                     "max_x_ratio": round(max(ratios), 2) if ratios else None})

    print("== 阅读顺序不变式（A 生产顺序，filter=ON 47 页归档）==")
    print("pages=%d  竖排列单元合计=%d" % (len(rows), tot_units))
    print("I1 列内 y 逆序 = %d（页数 %d）→ %s"
          % (tot_i1, pages_i1, "PASS" if tot_i1 == 0 else "FAIL"))
    print("I2 过合并列单元 = %d（页数 %d，阈值 x并集宽/最宽框 > %.1f）→ %s"
          % (tot_i2, pages_i2, OVER_MERGE_FACTOR,
             "PASS" if tot_i2 == 0 else "FAIL"))
    print("I3 主栏列序右→左 失败页 = %d → %s"
          % (pages_i3, "PASS" if pages_i3 == 0 else "FAIL"))

    print("\n-- 列单元 x 离散度最大的页（ratio = x并集宽/最宽框宽）--")
    for pg, r, nu, n in sorted(worst_ratio, key=lambda t: -t[1])[:12]:
        print("  %s ratio=%5.2f  units=%2d  n=%2d" % (pg, r, nu, n))

    print("\n-- I2 违规页 --")
    for r in rows:
        if r["i2_over_merged_units"]:
            print("  %s units=%2d 过合并=%d  max_ratio=%s"
                  % (r["page"], r["units"], r["i2_over_merged_units"],
                     r["max_x_ratio"]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"col_overlap": COL_OVERLAP,
                   "over_merge_factor": OVER_MERGE_FACTOR,
                   "total_units": tot_units,
                   "i1_y_inversions": tot_i1,
                   "i2_over_merged_units": tot_i2,
                   "i3_failed_pages": pages_i3,
                   "pages": rows}, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night45_invariants.json")


if __name__ == "__main__":
    main()
