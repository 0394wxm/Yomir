# -*- coding: utf-8 -*-
"""night45_cluster_proto2.py — 更保守的最小修复（NIGHT45）。

v2（`night45_cluster_proto.py`）用 h≥0.6×hmax 判「长框」，把 p007/p031 那批
**高而窄的手写批注条**（w=22-26, h≈522-549）也算成长框，导致 9 页里 7 页
批注带内部顺序被改动（I5 不变，属无谓改动）。

v3 收紧为**只拆真正的并列主栏**：
  * 长框 = `_main_group` 判定的主栏框（h≥0.6hmax 且 w≥0.65×P90(w)）——
    窄批注条被 w 条件排除；
  * 且这两个主栏框必须 **x 互不重叠 且 y 重叠 ≥0.5**（真正并排、同一高度），
    上下堆叠的同列长框不拆。

预期：只有 p017/p021 变化（I5 的 2 个真 bug），其余 41 页顺序逐位不变。

产出: eval/night45_proto2.json
用法: python -X utf8 tools/night45_cluster_proto2.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import _main_group  # noqa: E402
from tools.night45_cluster_proto import (  # noqa: E402
    build_units, main_col_pairs_inv, order_v1, ov_x,
)

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night45_proto2.json")
COL_OVERLAP = 0.4
Y_OVERLAP_MIN = 0.5


def ov_y(a, b):
    lo = max(a["y"], b["y"])
    hi = min(a["y"] + a["h"], b["y"] + b["h"])
    return max(0, hi - lo) / max(1, min(a["h"], b["h"]))


def x_disjoint(a, b):
    return a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"]


def _key(b):
    return (b["x"], b["y"], b["w"], b["h"])


def split_col_unit_v3(items, main_keys):
    """只有当单元含 ≥2 个「并排且同高」的主栏框时才拆。"""
    m = [b for b in items if _key(b) in main_keys]
    if len(m) < 2:
        return [items]
    # 是否存在一对主栏：x 不重叠 且 y 重叠 ≥0.5
    parallel = False
    for i in range(len(m)):
        for j in range(i + 1, len(m)):
            if x_disjoint(m[i], m[j]) and ov_y(m[i], m[j]) >= Y_OVERLAP_MIN:
                parallel = True
                break
        if parallel:
            break
    if not parallel:
        return [items]

    subs = []
    for b in sorted(m, key=lambda t: -(t["x"] + t["w"])):
        for s in subs:
            if any(ov_x(b, o) >= COL_OVERLAP for o in s):
                s.append(b)
                break
        else:
            subs.append([b])
    if len(subs) < 2:
        return [items]
    mids = {_key(b) for b in m}
    for b in items:
        if _key(b) in mids:
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


def order_v3(boxes):
    _miban, main = _main_group([dict(b) for b in boxes])
    main_keys = {_key(b) for b in main}
    units = build_units(boxes)
    out_units = []
    n_split = 0
    for u in units:
        if u["kind"] != "col":
            out_units.append(u)
            continue
        subs = split_col_unit_v3(u["items"], main_keys)
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


def main():
    pages = []
    for fn in sorted(os.listdir(FULL)):
        if fn.endswith(".json"):
            with open(os.path.join(FULL, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    rows = []
    tot_inv1 = tot_inv3 = tot_pairs = tot_split = 0
    changed = []
    bad = []
    for p in pages:
        boxes = [dict(b, index=i) for i, b in enumerate(p["line_boxes"])]
        if len(boxes) < 4:
            continue
        idx1 = order_v1(boxes)
        idx3, n_split = order_v3(boxes)
        if sorted(idx3) != sorted(idx1):
            bad.append(p["page"])
        inv1, npair = main_col_pairs_inv(boxes, idx1)
        inv3, _ = main_col_pairs_inv(boxes, idx3)
        tot_inv1 += inv1
        tot_inv3 += inv3
        tot_pairs += npair
        tot_split += n_split
        if idx1 != idx3:
            changed.append(p["page"])
        rows.append({"page": p["page"], "n": len(boxes), "split_units": n_split,
                     "changed": idx1 != idx3, "i5_v1": inv1, "i5_v3": inv3})

    print("== 最小修复 v3（只拆并排同高的主栏）==")
    print("pages=%d  主栏列对=%d  拆的单元=%d" % (len(rows), tot_pairs, tot_split))
    print("I5 列对颠倒: v1=%d → v3=%d → %s"
          % (tot_inv1, tot_inv3, "PASS" if tot_inv3 == 0 else "FAIL"))
    print("顺序变化页 (%d/%d): %s" % (len(changed), len(rows), changed))
    print("置换/多重集错误: %s" % (bad or "无"))
    for r in rows:
        if r["changed"]:
            print("  %s n=%2d split=%d  I5 %d->%d"
                  % (r["page"], r["n"], r["split_units"], r["i5_v1"], r["i5_v3"]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"pages": len(rows), "total_pairs": tot_pairs,
                   "i5_v1": tot_inv1, "i5_v3": tot_inv3,
                   "split_units": tot_split, "changed_pages": changed,
                   "multiset_errors": bad, "detail": rows},
                  f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night45_proto2.json")


if __name__ == "__main__":
    main()
