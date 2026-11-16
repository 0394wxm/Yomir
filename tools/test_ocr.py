# -*- coding: utf-8 -*-
"""test_ocr.py — 独立测试 backend/ocr_engine.py（加载模型 + 识别样张）。"""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"D:\kanbun-kakikudashi")

t0 = time.time()
from backend.ocr_engine import get_engine  # noqa: E402

engine = get_engine()
print("[engine] loaded in %.1fs" % (time.time() - t0), flush=True)

img = sys.argv[1] if len(sys.argv) > 1 else r"D:\kanbun-kakikudashi\ocr_runtime\samples\ndl_1287221_R0000002_clean.jpg"
with open(img, "rb") as f:
    data = f.read()
t1 = time.time()
res = engine.recognize_bytes(data)
print("[ocr] %s" % img)
print("[ocr] elapsed %.1fs, %d lines" % (time.time() - t1, res["line_count"]))
print("[ocr] text:")
print(res["text"])
