# -*- coding: utf-8 -*-
"""night45_cluster_proto.py — _cluster_order 最小修复原型（NIGHT45，离线）。

**P1（reorder_headnote）已被证伪**：按生产列定义度量，A 原顺序列连续性
excess=0/659 列，P1 反而 48；I5 主栏列对颠倒 A 只有 2/544。

**真缺陷（I5 定位）**：`_cluster_order` 用 x 重叠≥0.4 的**传递闭包**聚列。
一个跨列的头注/割注框能把左右两个主栏桥接进同一列单元；单元内部只按 y 排序，
而两主栏的 y 只差 2px（p021: 215 vs 217）→ 先后由噪声决定，可能左先右后，
整列正文读反。

**最小修复**：列单元若含 ≥2 个 **x 互不重叠的长框**（h ≥ MAIN_H_FRAC×h_max），
就按长框的 x 互不重叠关系拆成子列；短框（头注/割注）按 x 重叠最大归入子列；
子列按右缘 x 右→左。不碰其余任何单元。

本脚本离线对比 v1（生产）vs v2（修复）：页级顺序差异、I5、内容多重集。

产出: eval/night45_proto.json
用法: python -X utf8 tools/night45_cluster_proto.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import MAIN_H_FRAC  # noqa: E402

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night45_proto.json")
COL_OVERLAP = 0.4


def ov_x(a, b):
    lo = max(a["x"], b["x"])
    hi = min(a["x"] + a["w"], b["x"] + b["w"])
    return max(0, hi - lo) / max(1, min(a["w"], b["w"]))


def ov_y(a, b):
    lo = max(a["y"], b["y"])
    hi = min(a["y"] + a["h"], b["y"] + b["h"])
    return max(0, hi - lo) / max(1, min(a["h"], b["h"]))


def build_units(boxes):
    """复刻 _cluster_order 的单元构造（竖排列 + 横排行）。"""
    vert = [b for b in boxes if b["h"] >= b["w"]]
    horz = [b for b in boxes if b["h"] < b["w"]]
    units = []
    for b in sorted(vert, key=lambda t: -(t["x"] + t["w"])):
        for u in units:
            if u["kind"] == "col" and ov_x(u["box"], b) >= COL_OVERLAP:
                u["items"].append(b)
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
            units.append({"kind": "col", "box": dict(b), "items": [b]})
    for b in sorted(horz, key=lambda t: t["y"]):
        for u in units:
            if u["kind"] == "row" and ov_y(u["box"], b) >= 0.4:
                u["items"].append(b)
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
            units.append({"kind": "row", "box": dict(b), "items": [b]})
    return units


def order_v1(boxes):
    """生产 `_cluster_order`（A）。"""
    units = build_units(boxes)
    for u in units:
        if u["kind"] == "col":
            u["items"] = sorted(u["items"], key=lambda t: t["y"])
        else:
            u["items"] = sorted(u["items"], key=lambda t: -t["x"])
    units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
    idx = []
    for u in units:
        idx.extend(b["index"] for b in u["items"])
    return idx


def split_col_unit(items, hmax):
    """把含 ≥2 个 x 互不重叠长框的列单元拆成子列；返回 [items, ...]。"""
    long_ = [b for b in items if b["h"] >= MAIN_H_FRAC * hmax]
    if len(long_) < 2:
        return [items]
    subs = []
    for b in sorted(long_, key=lambda t: -(t["x"] + t["w"])):
        for s in subs:
            if any(ov_x(b, o) >= COL_OVERLAP for o in s):
                s.append(b)
                break
        else:
            subs.append([b])
    if len(subs) < 2:
        return [items]
    longs = {id(b) for b in long_}
    for b in items:
        if id(b) in longs:
            continue
        best, bestv = 0, -1.0
        for k, s in enumerate(subs):
            v = max(ov_x(b, o) for o in s)
            if v > bestv:
                bestv, best = v, k
        if bestv <= 0:
            cx = b["x"] + b["w"] / 2.0
            best = min(range(len(subs)),
                       key=lambda k: abs(cx - (subs[k][0]["x"]
                                               + subs[k][0]["w"] / 2.0)))
        subs[best].append(b)
    subs.sort(key=lambda s: -max(o["x"] + o["w"] for o in s))
    return subs


def order_v2(boxes):
    """修复版：列单元拆子列后再按质心右→左。"""
    hmax = max((b["h"] for b in boxes), default=0)
    units = build_units(boxes)
    out_units = []
    n_split = 0
    for u in units:
        if u["kind"] != "col":
            out_units.append(u)
            continue
        subs = split_col_unit(u["items"], hmax)
        if len(subs) == 1:
            out_units.append(u)
            continue
        n_split += 1
        for s in subs:
            xs = min(b["x"] for b in s)
            ys = min(b["y"] for b in s)
            out_units.append({"kind": "col",
                              "box": {"x": xs, "y": ys,
                                      "w": max(b["x"] + b["w"] for b in s) - xs,
                                      "h": max(b["y"] + b["h"] for b in s) - ys},
                              "items": s})
    for u in out_units:
        if u["kind"] == "col":
            u["items"] = sorted(u["items"], key=lambda t: t["y"])
        else:
            u["items"] = sorted(u["items"], key=lambda t: -t["x"])
    out_units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
    idx = []
    for u in out_units:
        idx.extend(b["index"] for b in u["items"])
    return idx, n_split


def main_col_pairs_inv(boxes, order):
    """I5：主栏列对颠倒数（用 _main_group 的主栏框）。"""
    from backend.ocr_layout import _main_group
    _miban, main = _main_group([dict(b) for b in boxes])
    if not main:
        return 0, 0
    mk = {(b["x"], b["y"], b["w"], b["h"]) for b in main}
    mi = [i for i, b in enumerate(boxes)
          if (b["x"], b["y"], b["w"], b["h"]) in mk]
    cols = []
    for i in sorted(mi, key=lambda i: -(boxes[i]["x"] + boxes[i]["w"])):
        b = boxes[i]
        for c in cols:
            if any(ov_x(b, boxes[j]) >= COL_OVERLAP for j in c):
                c.append(i)
                break
        else:
            cols.append([i])
    cols.sort(key=lambda c: -max(boxes[i]["x"] + boxes[i]["w"] for i in c))
    pos = {i: k for k, i in enumerate(order)}
    inv = 0
    for k in range(len(cols) - 1):
        if max(pos[i] for i in cols[k]) > min(pos[i] for i in cols[k + 1]):
            inv += 1
    return inv, len(cols) - 1


def main():
    pages = []
    for fn in sorted(os.listdir(FULL)):
        if fn.endswith(".json"):
            with open(os.path.join(FULL, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    rows = []
    tot_inv1 = tot_inv2 = tot_pairs = tot_split = 0
    changed = []
    bad_ms = []
    for p in pages:
        boxes = [dict(b, index=i) for i, b in enumerate(p["line_boxes"])]
        if len(boxes) < 4:
            continue
        idx1 = order_v1(boxes)
        idx2, n_split = order_v2(boxes)
        if sorted(idx2) != list(range(len(boxes))):
            bad_ms.append(p["page"])
        # 内容多重集
        if sorted(idx2) != sorted(idx1):
            bad_ms.append(p["page"] + ":perm")
        inv1, npair = main_col_pairs_inv(boxes, idx1)
        inv2, _ = main_col_pairs_inv(boxes, idx2)
        tot_inv1 += inv1
        tot_inv2 += inv2
        tot_pairs += npair
        tot_split += n_split
        if idx1 != idx2:
            changed.append(p["page"])
        rows.append({"page": p["page"], "n": len(boxes), "split_units": n_split,
                     "changed": idx1 != idx2, "i5_v1": inv1, "i5_v2": inv2,
                     "pairs": npair})

    print("== _cluster_order 最小修复原型（47 页 filter=ON 归档）==")
    print("pages=%d  主栏列对合计=%d  被拆的列单元=%d" % (len(rows), tot_pairs, tot_split))
    print("I5 列对颠倒: v1=%d → v2=%d  → %s"
          % (tot_inv1, tot_inv2, "PASS" if tot_inv2 == 0 else "FAIL"))
    print("顺序有变化的页 (%d/%d): %s" % (len(changed), len(rows), changed))
    print("置换/多重集错误: %s" % (bad_ms or "无"))

    print("\n-- 变化页明细 --")
    for r in rows:
        if r["changed"]:
            print("  %s n=%2d split=%d  I5 %d->%d  pairs=%d"
                  % (r["page"], r["n"], r["split_units"], r["i5_v1"],
                     r["i5_v2"], r["pairs"]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"pages": len(rows), "total_pairs": tot_pairs,
                   "i5_v1": tot_inv1, "i5_v2": tot_inv2,
                   "split_units": tot_split, "changed_pages": changed,
                   "multiset_errors": bad_ms, "detail": rows},
                  f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night45_proto.json")


if __name__ == "__main__":
    main()
