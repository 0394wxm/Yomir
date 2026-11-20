# -*- coding: utf-8 -*-
"""night45_cluster_proto3.py — v4：只重排单元内的主栏框（NIGHT45 最终原型）。

v2（h≥0.6hmax 判长框）→ 9 页变动，其中 7 页是批注带内部的无谓改动。
v3（主栏判据 + 并排同高 + 短框按重叠归子列）→ 修好 p021，但把 p018 改坏：
    注文碎框 A19/A20 被分到不同子列，正文 A22 反而排到注文之后。

**v4 的取舍**：不去动任何非主栏框的位置，只在列单元内部**重排主栏框所占的槽位**：
  1. 单元内按 y 排序得到基准序列；
  2. 取出其中属于 `_main_group` 的框，记下它们的槽位；
  3. 若这些主栏框里有 x 互不重叠的对（真正的并列主栏被头注桥接），
     就把它们按右缘 x 右→左重新填回这些槽位；
  4. 非主栏框位置逐位不变。

这样 p018（主栏 y 序本来就与 x 序一致）零改动；p021（y 差 2px 判反）被修正；
p017（两条手写长条）按几何右→左纠正。

产出: eval/night45_proto3.json
用法: python -X utf8 tools/night45_cluster_proto3.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import _main_group  # noqa: E402
from tools.night45_cluster_proto import (  # noqa: E402
    build_units, main_col_pairs_inv, order_v1,
)

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night45_proto3.json")


def _key(b):
    return (b["x"], b["y"], b["w"], b["h"])


def x_disjoint(a, b):
    return a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"]


def reorder_main_slots(items, main_keys):
    """单元内只重排主栏框的槽位；非主栏框位置不变。"""
    m = [b for b in items if _key(b) in main_keys]
    if len(m) < 2:
        return items
    if not any(x_disjoint(m[i], m[j])
               for i in range(len(m)) for j in range(i + 1, len(m))):
        return items
    # 主栏框按右缘 x 右→左（竖排正确列序）
    m_sorted = sorted(m, key=lambda t: -(t["x"] + t["w"]))
    if m_sorted == m:
        return items
    slots = [k for k, b in enumerate(items) if _key(b) in main_keys]
    out = list(items)
    for slot, b in zip(slots, m_sorted):
        out[slot] = b
    return out


def order_v4(boxes):
    _miban, main = _main_group([dict(b) for b in boxes])
    main_keys = {_key(b) for b in main}
    units = build_units(boxes)
    n_fixed = 0
    for u in units:
        if u["kind"] != "col":
            u["items"] = sorted(u["items"], key=lambda t: -t["x"])
            continue
        base = sorted(u["items"], key=lambda t: t["y"])
        new = reorder_main_slots(base, main_keys)
        if new != base:
            n_fixed += 1
        u["items"] = new
    units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
    idx = []
    for u in units:
        idx.extend(b["index"] for b in u["items"])
    return idx, n_fixed


def main():
    pages = []
    for fn in sorted(os.listdir(FULL)):
        if fn.endswith(".json"):
            with open(os.path.join(FULL, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    rows = []
    tot_inv1 = tot_inv4 = tot_pairs = tot_fixed = 0
    changed = []
    bad = []
    for p in pages:
        boxes = [dict(b, index=i) for i, b in enumerate(p["line_boxes"])]
        if len(boxes) < 4:
            continue
        idx1 = order_v1(boxes)
        idx4, n_fixed = order_v4(boxes)
        if sorted(idx4) != sorted(idx1):
            bad.append(p["page"])
        inv1, npair = main_col_pairs_inv(boxes, idx1)
        inv4, _ = main_col_pairs_inv(boxes, idx4)
        tot_inv1 += inv1
        tot_inv4 += inv4
        tot_pairs += npair
        tot_fixed += n_fixed
        if idx1 != idx4:
            changed.append(p["page"])
        rows.append({"page": p["page"], "n": len(boxes), "fixed_units": n_fixed,
                     "changed": idx1 != idx4, "i5_v1": inv1, "i5_v4": inv4,
                     "pairs": npair})

    print("== v4 只重排主栏槽位（47 页 filter=ON 归档）==")
    print("pages=%d  主栏列对=%d  修正的单元=%d" % (len(rows), tot_pairs, tot_fixed))
    print("I5 列对颠倒: v1=%d → v4=%d → %s"
          % (tot_inv1, tot_inv4, "PASS" if tot_inv4 == 0 else "FAIL"))
    print("顺序变化页 (%d/%d): %s" % (len(changed), len(rows), changed))
    print("置换/多重集错误: %s" % (bad or "无"))
    for r in rows:
        if r["changed"]:
            print("  %s n=%2d fixed=%d  I5 %d->%d  pairs=%d"
                  % (r["page"], r["n"], r["fixed_units"], r["i5_v1"],
                     r["i5_v4"], r["pairs"]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"pages": len(rows), "total_pairs": tot_pairs,
                   "i5_v1": tot_inv1, "i5_v4": tot_inv4,
                   "fixed_units": tot_fixed, "changed_pages": changed,
                   "multiset_errors": bad, "detail": rows},
                  f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night45_proto3.json")


if __name__ == "__main__":
    main()
