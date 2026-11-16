# -*- coding: utf-8 -*-
"""test_ocr_samples.py — 4 张 NDL 样张 × {native, cluster} 行序 对比实测（NIGHT3）。

输出: eval/ocr_samples/<sample>__<mode>.txt + 控制台摘要。
同一进程只加载一次模型；样张串行跑（Celeron 不并行）。
"""
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SAMPLES = [
    "ndl_1287221_R0000002_clean.jpg",   # 竹取物語（巻子本・仮名）
    "ndl_10301438_R0000002_clean.jpg",  # 人間萬事翁馬（江戸絵本）
    "ndl_11892692_R0000003_clean.jpg",  # NDL item 11892692
    "ndl_9973821_R0000002_clean.jpg",   # 伊藤博文関係文書（明治文書）
]
OUT_DIR = os.path.join(ROOT, "eval", "ocr_samples")

t0 = time.time()
from backend.ocr_engine import get_engine  # noqa: E402

engine = get_engine()
print("[engine] loaded in %.1fs" % (time.time() - t0), flush=True)

os.makedirs(OUT_DIR, exist_ok=True)
for s in SAMPLES:
    path = os.path.join(ROOT, "ocr_runtime", "samples", s)
    if not os.path.isfile(path):
        print("[SKIP] missing:", path)
        continue
    with open(path, "rb") as f:
        data = f.read()
    for mode in ("native", "cluster"):
        t1 = time.time()
        res = engine.recognize_bytes(data, order=mode)
        out_name = "%s__%s.txt" % (os.path.splitext(s)[0], mode)
        with open(os.path.join(OUT_DIR, out_name), "w", encoding="utf-8", newline="\n") as f:
            f.write(res["text"])
        first = res["lines"][0] if res["lines"] else "(no lines)"
        print("[%s/%s] %d lines, junk_filtered=%d, %.1fs, first=%r"
              % (s, mode, res["line_count"], res.get("junk_filtered", 0),
                 res["elapsed_sec"], first[:24]), flush=True)
print("[done]", flush=True)
