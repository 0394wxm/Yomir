# -*- coding: utf-8 -*-
"""night43_gt_impact.py — GT 8 页的版面过滤影响预检（NIGHT43）。

用 night43_boxes.json 中 GT 页的检测框跑 judge_layout，列出会被过滤的框几何，
再对照 eval/night36_ocr_lines_night42.json 的 GT 行坐标（文件名映射：
ndl_11892692_R0000003.jpg ↔ pages/p003.jpg，页码 = manifest 序号）。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import judge_layout  # noqa: E402

with open(os.path.join(ROOT, "eval", "night43_boxes.json"), encoding="utf-8") as f:
    boxes = {p["page"]: p for p in json.load(f)["pages"]}
with open(os.path.join(ROOT, "eval", "night36_ocr_lines_night42.json"), encoding="utf-8") as f:
    gt = json.load(f)["results"]

# GT stem → import_pid 页码（Night42 校验段确认 p003-p005 = R3-R5；其余按已知映射）
MAP = {
    "ndl_11892692_R0000003": "p003", "ndl_11892692_R0000004": "p004",
    "ndl_11892692_R0000005": "p005", "ndl_1033232_R0000003": None,
    "ndl_10301438_R0000002": None, "ndl_10301438_R0000003": None,
    "ndl_781192_R0000003": None, "ndl_781193_R0000003": None,
}

for r in gt:
    stem = r["file"][:-4]
    pg = MAP.get(stem)
    print("== %s -> %s (%d GT lines)" % (stem, pg or "(非本 PID/无页图)", r["ocr_n_lines"]))
    if not pg or pg not in boxes:
        continue
    p = boxes[pg]
    raw = [dict(b, vert=b["h"] >= b["w"]) for b in p["lines"] if not b["junk3"]]
    miban, judged = judge_layout(raw, p["img_w"], p["img_h"])
    removed = [(b, reason) for b, reason in judged if reason]
    print("   miban=%s  removed=%d/%d" % (miban, len(removed), len(judged)))
    for b, reason in removed:
        print("   REMOVE %-12s x=%4d y=%4d w=%3d h=%4d" % (reason, b["x"], b["y"], b["w"], b["h"]))
