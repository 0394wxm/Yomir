# -*- coding: utf-8 -*-
"""night43_view_boxes.py — 打印某页检测框几何（NIGHT43 测量辅助）。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, "eval", "night43_boxes.json"), encoding="utf-8") as f:
    d = json.load(f)
pg = sys.argv[1]
p = next(p for p in d["pages"] if p["page"] == pg)
print("== %s %dx%d median_vh=%s lines=%d" % (pg, p["img_w"], p["img_h"], p["median_vh"], len(p["lines"])))
for i, l in enumerate(p["lines"]):
    cx = l["x"] + l["w"] / 2.0
    edge = min(l["x"], p["img_w"] - l["x"] - l["w"], l["y"], p["img_h"] - l["y"] - l["h"])
    print("%3d x=%4d y=%4d w=%3d h=%4d cx=%5.0f vert=%d edge=%4d sat=%5.1f/%.2f junk3=%d"
          % (i, l["x"], l["y"], l["w"], l["h"], cx, l["vert"], edge,
             l["sat_mean"], l["sat_frac"], l["junk3"]))
