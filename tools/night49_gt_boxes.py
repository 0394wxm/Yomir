# -*- coding: utf-8 -*-
"""night49_gt_boxes.py — 看 GT 页上被重排的两处框几何（确认方向正确）。

用法: python -X utf8 tools/night49_gt_boxes.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TARGETS = {
    "ndl_10301438_R0000003.jpg": ["一", "市川"],
    "ndl_781193_R0000003.jpg": ["第九九四條之事", "十一月廿五日"],
}

b = json.load(open(os.path.join(ROOT, "eval", "night49_gt_lines.json"),
                   encoding="utf-8"))
a = json.load(open(os.path.join(ROOT, "eval", "night44_gt_lines.json"),
                   encoding="utf-8"))
ra = {r["file"]: r for r in a["results"]}
for r in b["results"]:
    f = r["file"]
    if f not in TARGETS:
        continue
    print("\n### %s" % f)
    old = ra[f]["lines"]
    print(" 改前顺序（只列涉及重排的框，含上下文）:")
    for i, l in enumerate(old):
        if any(t in l["text"] for t in TARGETS[f]):
            print("   pos=%2d x=%4d y=%4d w=%3d h=%3d %r"
                  % (i, l["x"], l["y"], l["w"], l["h"], l["text"][:40]))
    print(" 改后顺序:")
    for i, l in enumerate(r["lines"]):
        if any(t in l["text"] for t in TARGETS[f]):
            print("   pos=%2d x=%4d y=%4d w=%3d h=%3d %r"
                  % (i, l["x"], l["y"], l["w"], l["h"], l["text"][:40]))
