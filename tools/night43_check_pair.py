# -*- coding: utf-8 -*-
"""night43_check_pair.py — 对 night43_pair.json 的页跑 judge_layout，打印被滤框文本（验证用）。

回答两个问题：
  1. 被滤的 footer/strip 框的文本是不是书志/手写噪音？
  2. 正文列文本是否一个没丢（被滤清单里不能有経文連続文本）？
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import judge_layout  # noqa: E402

with open(os.path.join(ROOT, "eval", "night43_pair.json"), encoding="utf-8") as f:
    pair = json.load(f)
with open(os.path.join(ROOT, "eval", "night43_boxes.json"), encoding="utf-8") as f:
    bx = json.load(f)
sz = {p["page"]: (p["img_w"], p["img_h"]) for p in bx["pages"]}

for pg in pair["pages"]:
    iw, ih = sz[pg["page"]]
    boxes = [dict(p) for p in pg["pairs"]]
    miban, judged = judge_layout(boxes, iw, ih)
    print("== %s pairs=%d miban=%s" % (pg["page"], len(boxes), miban))
    print("-- REMOVED --")
    for b, reason in judged:
        if reason:
            print("  %-8s x=%4d y=%4d w=%3d h=%4d  %r" % (reason, b["x"], b["y"], b["w"], b["h"], b["text"]))
    print("-- KEPT (y>700 的低位框，供对照) --")
    for b, reason in judged:
        if not reason and b["y"] > 700:
            print("  x=%4d y=%4d w=%3d h=%4d  %r" % (b["x"], b["y"], b["w"], b["h"], b["text"]))
