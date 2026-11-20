# -*- coding: utf-8 -*-
"""night45_prod_equiv.py — 生产路径 vs v4 原型的等价性验证（NIGHT45）。

不跑 OCR：直接用 `_cluster_order` 的单元构造逻辑离线复算，但**调用生产函数**
`reorder_main_slots` / `main_column_keys`，与 `night45_cluster_proto3.order_v4`
的输出逐页比对。若 43 页全部逐位相同 → 生产代码确实实现了 v4 的语义。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import main_column_keys, reorder_main_slots  # noqa: E402
from tools.night45_cluster_proto import build_units, order_v1  # noqa: E402
from tools.night45_cluster_proto3 import order_v4  # noqa: E402

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")


def prod_order(boxes):
    """用生产函数复刻 _cluster_order（与 backend/ocr_engine.py 同步）。"""
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


def main():
    pages = []
    for fn in sorted(os.listdir(FULL)):
        if fn.endswith(".json"):
            with open(os.path.join(FULL, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    mism = []
    changed = []
    for p in pages:
        boxes = [dict(b, index=i) for i, b in enumerate(p["line_boxes"])]
        if len(boxes) < 4:
            continue
        ip = prod_order(boxes)
        i4, _ = order_v4(boxes)
        i1 = order_v1(boxes)
        if ip != i4:
            mism.append(p["page"])
        if ip != i1:
            changed.append(p["page"])
        if sorted(ip) != list(range(len(boxes))):
            mism.append(p["page"] + ":perm")

    print("== 生产路径 vs v4 原型 ==")
    print("逐页不一致: %s" % (mism or "无（完全等价）"))
    print("相对原顺序有变化的页: %s" % changed)
    print("置换检查: %s" % ("PASS" if not mism else "FAIL"))


if __name__ == "__main__":
    main()
