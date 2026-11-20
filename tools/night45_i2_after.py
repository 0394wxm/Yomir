# -*- coding: utf-8 -*-
"""night45_i2_after.py — I2 过合并：修复前 vs 修复后（NIGHT45）。

I2 = 列单元内 x 并集宽度 / 单元内最宽框宽。过合并本身只是「几何警告」，
真正的问题是它是否导致顺序错误（I5）。本脚本在**修复后**的单元上重算 I2，
确认修复没有把过合并变严重，并逐条给出剩余过合并单元的构成。

产出: eval/night45_i2_after.json
用法: python -X utf8 tools/night45_i2_after.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import main_column_keys, reorder_main_slots  # noqa: E402
from tools.night45_cluster_proto import build_units  # noqa: E402

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night45_i2_after.json")
FACTOR = 2.0


def ratio_of(items):
    lo = min(b["x"] for b in items)
    hi = max(b["x"] + b["w"] for b in items)
    wmax = max(b["w"] for b in items)
    return (hi - lo) / max(1, wmax)


def main():
    pages = []
    for fn in sorted(os.listdir(FULL)):
        if fn.endswith(".json"):
            with open(os.path.join(FULL, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    before = after = 0
    rows = []
    detail = []
    for p in pages:
        boxes = [dict(b, index=i) for i, b in enumerate(p["line_boxes"])]
        if len(boxes) < 4:
            continue
        units = build_units(boxes)
        nb = na = 0
        for u in units:
            if u["kind"] != "col" or len(u["items"]) < 2:
                continue
            if ratio_of(u["items"]) > FACTOR:
                nb += 1
                detail.append({"page": p["page"], "stage": "before",
                               "ratio": round(ratio_of(u["items"]), 2),
                               "n": len(u["items"])})
        # 修复后
        main_keys = main_column_keys(boxes)
        for u in units:
            if u["kind"] != "col":
                continue
            u["items"] = sorted(u["items"], key=lambda t: t["y"])
            u["items"] = reorder_main_slots(u["items"], main_keys)
            if len(u["items"]) >= 2 and ratio_of(u["items"]) > FACTOR:
                na += 1
                detail.append({"page": p["page"], "stage": "after",
                               "ratio": round(ratio_of(u["items"]), 2),
                               "n": len(u["items"])})
        before += nb
        after += na
        if nb or na:
            rows.append({"page": p["page"], "before": nb, "after": na})

    print("== I2 过合并单元（ratio > %.1f）==" % FACTOR)
    print("修复前=%d  修复后=%d" % (before, after))
    for r in rows:
        print("  %s  %d -> %d" % (r["page"], r["before"], r["after"]))
    print("\n-- 明细 --")
    for d in detail:
        print("  %s %-6s ratio=%.2f n=%d" % (d["page"], d["stage"],
                                             d["ratio"], d["n"]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"factor": FACTOR, "before": before, "after": after,
                   "pages": rows, "detail": detail}, f,
                  ensure_ascii=False, indent=1)
    print("\n[written] eval/night45_i2_after.json")


if __name__ == "__main__":
    main()
