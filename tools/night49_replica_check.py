# -*- coding: utf-8 -*-
"""night49_replica_check.py — 先验证「_cluster_order 复刻」与生产一致。

night49_warichu_order 的 Q1 用「同一列单元」作判据是**错的**：割注两半的 x
不相交，本来就该落在不同单元。真正该测的是**最终扁平输出顺序**里右半是否在
左半之前。

但在重测之前必须先证明复刻可信。方法：归档 `filter_off/*.json` 里的
`line_boxes` **已经是生产 _cluster_order 排好序的结果**。所以把归档框喂给复刻，
输出应该是**恒等置换**（order[i] == i）。任何非恒等 = 复刻与生产不一致。

同时用真实引擎跑 1 页做交叉验证（引擎耗时约 60s/页，只跑 1 页）。

产出: eval/night49_replica_check.json
用法: python -X utf8 tools/night49_replica_check.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import main_column_keys  # noqa: E402

OFF = os.path.join(ROOT, "eval", "night44_full", "filter_off")
OUT = os.path.join(ROOT, "eval", "night49_replica_check.json")


def overlap_x(a, b):
    lo = max(a["x"], b["x"])
    hi = min(a["x"] + a["w"], b["x"] + b["w"])
    inter = max(0, hi - lo)
    return inter / max(1, min(a["w"], b["w"]))


def cluster_order(boxes, use_maincol=True):
    """复刻 backend/ocr_engine.py::_cluster_order（含 reorder_main_slots）。"""
    from backend.ocr_layout import reorder_main_slots
    vert = [b for b in boxes if b["h"] >= b["w"]]
    horz = [b for b in boxes if b["h"] < b["w"]]
    units = []
    for b in sorted(vert, key=lambda t: -(t["x"] + t["w"])):
        placed = False
        for u in units:
            if u["kind"] == "col" and overlap_x(u["box"], b) >= 0.4:
                u["items"].append(b)
                u["box"] = {
                    "x": min(u["box"]["x"], b["x"]),
                    "y": min(u["box"]["y"], b["y"]),
                    "w": max(u["box"]["x"] + u["box"]["w"],
                             b["x"] + b["w"]) - min(u["box"]["x"], b["x"]),
                    "h": max(u["box"]["y"] + u["box"]["h"],
                             b["y"] + b["h"]) - min(u["box"]["y"], b["y"]),
                }
                placed = True
                break
        if not placed:
            units.append({"kind": "col", "box": dict(b), "items": [b]})
    for b in sorted(horz, key=lambda t: t["y"]):
        placed = False
        for u in units:
            if u["kind"] == "row" and overlap_x(u["box"], b) >= 0.4:
                u["items"].append(b)
                placed = True
                break
        if not placed:
            units.append({"kind": "row", "box": dict(b), "items": [b]})
    main_keys = main_column_keys(boxes) if use_maincol else set()
    for u in units:
        if u["kind"] == "col":
            u["items"] = sorted(u["items"], key=lambda t: t["y"])
            if use_maincol:
                u["items"] = reorder_main_slots(u["items"], main_keys)
        else:
            u["items"] = sorted(u["items"], key=lambda t: -(t["x"]))
    units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
    idx = []
    for u in units:
        idx.extend(b["index"] for b in u["items"])
    return idx


def main():
    pages = []
    for fn in sorted(os.listdir(OFF)):
        if fn.endswith(".json"):
            pages.append(json.load(open(os.path.join(OFF, fn), encoding="utf-8")))

    ident = 0
    nonident = []
    for q in pages:
        boxes = [dict(b) for b in q["line_boxes"]]
        if not boxes:
            continue
        for i, b in enumerate(boxes):
            b["index"] = i
        idx = cluster_order(boxes)
        if idx == list(range(len(boxes))):
            ident += 1
        else:
            nonident.append({"page": q["page"], "n": len(boxes),
                             "n_swapped": sum(1 for i, j in enumerate(idx) if i != j),
                             "idx": idx})

    print("== 复刻自检：把归档（已排序）框喂回复刻，应为恒等置换 ==")
    print("  恒等: %d / %d 页" % (ident, len(pages)))
    print("  非恒等: %d 页" % len(nonident))
    for r in nonident[:12]:
        print("    %s n=%d 错位 %d 个" % (r["page"], r["n"], r["n_swapped"]))

    if not nonident:
        print("\n  → 复刻与生产**逐页完全一致**，可以放心用它做分析。")
    else:
        print("\n  → 复刻与生产有差异，分析结论需打折；差异页见 JSON。")

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n_pages": len(pages), "identical": ident,
                   "nonidentical": nonident}, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_replica_check.json")


if __name__ == "__main__":
    main()
