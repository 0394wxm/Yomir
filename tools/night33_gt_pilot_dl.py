# -*- coding: utf-8 -*-
"""night33_gt_pilot_dl.py — 下载 1 张 IIIF 样张到 gt_pilot 目录（GT 试点用）+ KuroNet 可得性探测。"""
import json
import os
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "eval", "ocr_samples", "gt_pilot")
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(ROOT, "eval", "ocr_samples", "batch20_summary.json"), encoding="utf-8") as f:
    rows = json.load(f)["results"]
r = next(x for x in rows if x["file"].startswith("ndl_1287221_R0000002"))
url = r["source_url"]
dest = os.path.join(OUT, r["file"])
if not os.path.exists(dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as fo:
        fo.write(resp.read())
print("downloaded:", dest, os.path.getsize(dest), "bytes; page", r["page"], "img", r["img_w"], "x", r["img_h"])

# KuroNet：hf-mirror 搜索（KuroNet 是歴史文書 OCR 模型，NII 发布）
import urllib.error
for q in ("kuronet", "kuro-net", "historicanybody"):
    try:
        req = urllib.request.Request("https://hf-mirror.com/api/models?search=" + q + "&limit=10",
                                     headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            hits = json.loads(resp.read().decode("utf-8"))
        print("hf models %r: %d hits" % (q, len(hits)))
        for h in hits[:5]:
            print("   ", h.get("id"), h.get("downloads"))
    except Exception as e:
        print("hf models %r failed: %r" % (q, e))
