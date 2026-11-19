# -*- coding: utf-8 -*-
"""night40_engine_run.py — 引擎级（recognize_bytes 产品流）跑 8 张 GT 页 + 19 张样张
结构指标，产出 eval/night40_engine_baseline.json（NIGHT40，列还原的回归基线）。"""
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_engine import get_engine  # noqa: E402

SAMPLE_DIR = os.path.join(ROOT, "ocr_runtime", "samples", "batch20")
GT_STEMS = [
    "ndl_11892692_R0000003", "ndl_11892692_R0000004", "ndl_11892692_R0000005",
    "ndl_1033232_R0000003", "ndl_10301438_R0000002", "ndl_10301438_R0000003",
    "ndl_781192_R0000003", "ndl_781193_R0000003",
]

with open(os.path.join(SAMPLE_DIR, "manifest.json"), encoding="utf-8") as f:
    manifest = {m["file"]: m for m in json.load(f)}

tag = sys.argv[1] if len(sys.argv) > 1 else "baseline"
OUT = os.path.join(ROOT, "eval", "night40_engine_%s.json" % tag)

print("[engine] loading...", flush=True)
t0 = time.time()
engine = get_engine()
load_sec = round(time.time() - t0, 1)
print("[engine] load %.1fs" % load_sec, flush=True)

results = []
for stem in GT_STEMS:
    fname = stem + ".jpg"
    with open(os.path.join(SAMPLE_DIR, fname), "rb") as f:
        data = f.read()
    t1 = time.time()
    r = engine.recognize_bytes(data)
    dt = round(time.time() - t1, 1)
    boxes = r.get("line_boxes", [])
    # 碎框率：w<60% 中位列宽 或 h<35% 中位行高
    ws = sorted(b["w"] for b in boxes) or [0]
    hs = sorted(b["h"] for b in boxes) or [0]
    med_w = ws[len(ws) // 2]
    med_h = hs[len(hs) // 2]
    frag = sum(1 for b in boxes if b["w"] < 0.6 * med_w or b["h"] < 0.35 * med_h)
    print("[%s] %.1fs lines=%d junk_filtered=%s frag=%d/%d first=%r"
          % (fname, dt, r["line_count"], r.get("junk_filtered"), frag, len(boxes),
             (r["lines"][0][:16] if r["lines"] else "(none)")), flush=True)
    results.append({
        "file": fname, "pid": manifest[fname]["pid"], "page": manifest[fname]["page"],
        "sec": dt, "line_count": r["line_count"], "junk_filtered": r.get("junk_filtered"),
        "frag_boxes": frag, "median_w": med_w, "median_h": med_h,
        "lines": [{"text": t, **b} for t, b in zip(r["lines"], boxes)],
    })

out = {"tag": tag, "engine_load_sec": load_sec, "n_pages": len(results), "results": results}
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("[done] written:", OUT, flush=True)
