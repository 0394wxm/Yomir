# -*- coding: utf-8 -*-
"""night36_status.py — 列出 GT 抄录素材状态：高清图尺寸 + 每页可用行数（NIGHT36）。"""
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HR = os.path.join(ROOT, "eval", "ocr_samples", "gt36_hr")
GT36 = os.path.join(ROOT, "eval", "ocr_samples", "gt36")

try:
    from PIL import Image
except ImportError:
    Image = None

print("--- hi-res images ---")
for p in sorted(glob.glob(os.path.join(HR, "*.jpg"))):
    size = os.path.getsize(p)
    if Image:
        w, h = Image.open(p).size
        print("%-28s %5dx%-5d %8d" % (os.path.basename(p), w, h, size))
    else:
        print("%-28s %8d" % (os.path.basename(p), size))

print("\n--- per-page lines ---")
tot = 0
for p in sorted(glob.glob(os.path.join(GT36, "*", "boxes.json"))):
    with open(p, encoding="utf-8") as f:
        b = json.load(f)
    ok = [l["line_no"] for l in b["lines"] if not l["junk"]]
    print("%-28s total=%-3d usable=%-3d junk=%d" % (b["file"], b["n_lines"], len(ok), b["n_lines"] - len(ok)))
    tot += len(ok)
print("usable total =", tot)
