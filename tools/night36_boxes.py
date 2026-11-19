# -*- coding: utf-8 -*-
"""night36_boxes.py — 打印某页的行框（NIGHT36）。用法: python tools/night36_boxes.py <stem> [stem2 ...]"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GT36 = os.path.join(ROOT, "eval", "ocr_samples", "gt36")

for stem in sys.argv[1:]:
    p = os.path.join(GT36, stem, "boxes.json")
    with open(p, encoding="utf-8") as f:
        b = json.load(f)
    print("== %s n_lines=%d pid=%s page=%s" % (stem, b["n_lines"], b["pid"], b["page"]))
    for l in b["lines"]:
        print("  %2d x=%4d y=%4d w=%3d h=%4d junk=%s" % (
            l["line_no"], l["x"], l["y"], l["w"], l["h"], l["junk"]))
