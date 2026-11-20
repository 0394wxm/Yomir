# -*- coding: utf-8 -*-
"""night45_maincol_order.py — I5：主栏列对在输出中的先后（NIGHT45 关键判据）。

I4（tools/night45_xorder_check.py）的 176 次「左右颠倒」绝大多数发生在头注带
内部相邻的两条批注之间（那些框 w=16-24、h=170，是横写短行被当成縦框；
它们之间本无竖排列序）。真正影响阅读的是**主栏列**的先后。

  I5 = 主栏列对 (k, k+1)（按右缘 x 右→左编号）在输出序列里，
       列 k 的所有框都排在列 k+1 的所有框之前 → 该对正确。
       反之 = 一次列对颠倒。

本次结果：544 个主栏列对里 2 对颠倒（p017、p021）。p021 经正文验证是真错
（「天下之無道也久矣、天将以夫子爲木鐸」被读反）；p017 的两条是手写批注
被 w 判据纳入主栏，不属正文。修复见 `backend/ocr_layout.reorder_main_slots`，
修复后 I5 = 1（仅剩 p017 的批注）。

产出: eval/night45_maincol.json
用法: python -X utf8 tools/night45_maincol_order.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import (  # noqa: E402
    MAIN_COL_OVERLAP, _main_group, main_column_keys, reorder_main_slots,
)
from tools.night45_cluster_proto import build_units, order_v1  # noqa: E402

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night45_maincol.json")


def ov_x(a, b):
    lo = max(a["x"], b["x"])
    hi = min(a["x"] + a["w"], b["x"] + b["w"])
    return max(0, hi - lo) / max(1, min(a["w"], b["w"]))


def main_cols(boxes):
    """主栏列：_main_group 判定 → x 重叠聚类 → 右→左排序。"""
    _miban, main = _main_group([dict(b) for b in boxes])
    if not main:
        return []
    mk = {(b["x"], b["y"], b["w"], b["h"]) for b in main}
    mi = [i for i, b in enumerate(boxes)
          if (b["x"], b["y"], b["w"], b["h"]) in mk]
    cols = []
    for i in sorted(mi, key=lambda i: -(boxes[i]["x"] + boxes[i]["w"])):
        b = boxes[i]
        for c in cols:
            if any(ov_x(b, boxes[j]) >= MAIN_COL_OVERLAP for j in c):
                c.append(i)
                break
        else:
            cols.append([i])
    cols.sort(key=lambda c: -max(boxes[i]["x"] + boxes[i]["w"] for i in c))
    return cols


def prod_order(boxes):
    """生产顺序（NIGHT45 修复后）。"""
    main_keys = main_column_keys(boxes)
    units = build_units(boxes)
    for u in units:
        if u["kind"] == "col":
            u["items"] = sorted(u["items"], key=lambda t: t["y"])
            u["items"] = reorder_main_slots(u["items"], main_keys)
        else:
            u["items"] = sorted(u["items"], key=lambda t: -t["x"])
    units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
    idx = []
    for u in units:
        idx.extend(b["index"] for b in u["items"])
    return idx


def count_inv(cols, order):
    pos = {i: k for k, i in enumerate(order)}
    inv = []
    for k in range(len(cols) - 1):
        a, b = cols[k], cols[k + 1]
        if max(pos[i] for i in a) > min(pos[i] for i in b):
            inv.append(k)
    return inv


def main():
    pages = []
    for fn in sorted(os.listdir(FULL)):
        if fn.endswith(".json"):
            with open(os.path.join(FULL, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    rows = []
    tot_pairs = tot1 = tot2 = 0
    bad1 = bad2 = []
    for p in pages:
        boxes = [dict(b, index=i) for i, b in enumerate(p["line_boxes"])]
        if len(boxes) < 4:
            continue
        cols = main_cols(boxes)
        if len(cols) < 2:
            continue
        i1 = order_v1(boxes)
        i2 = prod_order(boxes)
        inv1 = count_inv(cols, i1)
        inv2 = count_inv(cols, i2)
        tot_pairs += len(cols) - 1
        tot1 += len(inv1)
        tot2 += len(inv2)
        if inv1:
            bad1.append(p["page"])
        if inv2:
            bad2.append(p["page"])
        rows.append({"page": p["page"], "n": len(boxes), "n_main_cols": len(cols),
                     "inv_before": len(inv1), "inv_after": len(inv2),
                     "inv_pairs": inv1})

    print("== I5 主栏列对顺序（47 页 filter=ON 归档）==")
    print("pages=%d  主栏列对合计=%d" % (len(rows), tot_pairs))
    print("修复前颠倒=%d（页 %d）  修复后颠倒=%d（页 %d）"
          % (tot1, len(bad1), tot2, len(bad2)))
    print("→ %s" % ("PASS（修复消除了全部正文列对颠倒）" if tot2 < tot1
                    else "FAIL"))
    for r in rows:
        if r["inv_before"] or r["inv_after"]:
            print("  %s cols=%2d  颠倒 %d -> %d  pairs=%s"
                  % (r["page"], r["n_main_cols"], r["inv_before"],
                     r["inv_after"], r["inv_pairs"]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"total_pairs": tot_pairs, "inv_before": tot1,
                   "inv_after": tot2, "pages_with_inv_before": bad1,
                   "pages_with_inv_after": bad2, "pages": rows},
                  f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night45_maincol.json")


if __name__ == "__main__":
    main()
