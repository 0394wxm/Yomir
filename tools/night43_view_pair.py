# -*- coding: utf-8 -*-
"""night43_view_pair.py — 打印选样页「行文本↔框」配对（NIGHT43 测量辅助）。
噪音行列表（Night42 §3 点名）单独打头，方便定位其框坐标。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NAMED = ["晴辰", "筒城君", "専列記", "早朝堀紀州岩朝不福指越", "愛利氏", "西側面",
         "一四十一冊", "新助麹町三丁"]

with open(os.path.join(ROOT, "eval", "night43_boxes.json"), encoding="utf-8") as f:
    bx = json.load(f)
sz = {p["page"]: (p["img_w"], p["img_h"]) for p in bx["pages"]}

with open(os.path.join(ROOT, "eval", "night43_pair.json"), encoding="utf-8") as f:
    pair = json.load(f)

for pg in pair["pages"]:
    iw, ih = sz[pg["page"]]
    print("== %s %dx%d pairs=%d" % (pg["page"], iw, ih, len(pg["pairs"])))
    print("-- named noise rows --")
    for p in pg["pairs"]:
        if any(s in p["text"] for s in NAMED):
            print("  x=%4d y=%4d w=%3d h=%4d cx=%5.0f cy=%5.0f vert=%d  %r"
                  % (p["x"], p["y"], p["w"], p["h"], p["x"] + p["w"] / 2.0,
                     p["y"] + p["h"] / 2.0, p["vert"], p["text"]))
    print("-- all rows (y then x desc) --")
    rows = sorted(pg["pairs"], key=lambda p: (p["y"], -(p["x"] + p["w"])))
    for p in rows:
        print("  x=%4d y=%4d w=%3d h=%4d cy=%5.0f vert=%d  %r"
              % (p["x"], p["y"], p["w"], p["h"], p["y"] + p["h"] / 2.0, p["vert"], p["text"]))
