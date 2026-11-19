# -*- coding: utf-8 -*-
"""night36_hires_dl.py — 下载 GT 抄录用高清原图（3000px 宽），NDL IIIF（NIGHT36）。

只下图片，不产生/不读取任何 OCR 文本。产出 eval/ocr_samples/gt36_hr/<file>
"""
import json
import os
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_DIR = os.path.join(ROOT, "ocr_runtime", "samples", "batch20")
OUT_DIR = os.path.join(ROOT, "eval", "ocr_samples", "gt36_hr")
os.makedirs(OUT_DIR, exist_ok=True)

with open(os.path.join(SAMPLE_DIR, "manifest.json"), encoding="utf-8") as f:
    manifest = json.load(f)

for m in manifest:
    dst = os.path.join(OUT_DIR, m["file"])
    if os.path.exists(dst) and os.path.getsize(dst) > 100000:
        print("[exists]", m["file"], flush=True)
        continue
    url = "https://dl.ndl.go.jp/api/iiif/%s/%s/full/3000,/0/default.jpg" % (m["pid"], m["page"])
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "kanbun-research/1.0"})
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read()
        with open(dst, "wb") as f:
            f.write(data)
        print("[ok] %s %d bytes" % (m["file"], len(data)), flush=True)
    except Exception as e:  # noqa: BLE001
        print("[FAIL] %s %r" % (m["file"], e), flush=True)
print("[done]", flush=True)
