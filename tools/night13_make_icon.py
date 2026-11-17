# -*- coding: utf-8 -*-
"""night13_make_icon.py — 生成 Tauri 所需的 icon.ico（32x32 占位图标）。"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(r"D:\dlkotenocr-lite\site-packages")  # PIL 在官方 OCR 运行包里
from PIL import Image, ImageDraw  # noqa: E402

OUT_DIR = r"D:\kanbun-kakikudashi\frontend\src-tauri\icons"
os.makedirs(OUT_DIR, exist_ok=True)

img = Image.new("RGBA", (32, 32), (138, 109, 59, 255))
d = ImageDraw.Draw(img)
d.rectangle([6, 4, 26, 28], outline=(255, 244, 223, 255), width=2)
d.line([16, 4, 16, 28], fill=(255, 244, 223, 255), width=2)
d.line([6, 16, 26, 16], fill=(255, 244, 223, 255), width=2)
out = os.path.join(OUT_DIR, "icon.ico")
img.save(out, sizes=[(32, 32)])
print("icon ok:", out, os.path.getsize(out), "bytes")
