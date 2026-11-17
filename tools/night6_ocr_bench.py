# -*- coding: utf-8 -*-
"""night6_ocr_bench.py — 20 张样张逐张跑 OCR，分相计时（加载/检测/识别/排序），只记不重构（NIGHT6）。

输出: eval/ocr_samples/batch20_summary.json + 控制台摘要
"""
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_engine import get_engine  # noqa: E402

SAMPLE_DIR = os.path.join(ROOT, "ocr_runtime", "samples", "batch20")
OUT = os.path.join(ROOT, "eval", "ocr_samples", "batch20_summary.json")

t0 = time.time()
engine = get_engine()
load_sec = round(time.time() - t0, 1)
print("[engine] load %.1fs" % load_sec, flush=True)

from ndl_parser import convert_to_xml_string3  # noqa: E402
from reading_order.xy_cut.eval import eval_xml  # noqa: E402
import xml.etree.ElementTree as ET  # noqa: E402
from concurrent.futures import ThreadPoolExecutor  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
import io  # noqa: E402

manifest_path = os.path.join(SAMPLE_DIR, "manifest.json")
with open(manifest_path, encoding="utf-8") as f:
    manifest = json.load(f)

results = []
for m in manifest:
    path = os.path.join(SAMPLE_DIR, m["file"])
    img = np.array(Image.open(path).convert("RGB"))
    img_h, img_w = img.shape[:2]

    t1 = time.time()
    detections = engine.detector.detect(img)
    t_detect = round(time.time() - t1, 1)

    classeslist = list(engine.detector.classes.values())
    resultobj = [dict(), dict()]
    resultobj[0][0] = list()
    for i in range(17):
        resultobj[1][i] = []
    for det in detections:
        xmin, ymin, xmax, ymax = det["box"]
        if det["class_index"] == 0:
            resultobj[0][0].append([xmin, ymin, xmax, ymax])
        resultobj[1][det["class_index"]].append([xmin, ymin, xmax, ymax, det["confidence"], 0])
    xmlstr = convert_to_xml_string3(img_w, img_h, m["file"], classeslist, resultobj)
    root = ET.fromstring("<OCRDATASET>" + xmlstr + "</OCRDATASET>")
    eval_xml(root, logger=None)

    crops = []
    for lineobj in root.findall(".//LINE"):
        x, y = int(lineobj.get("X")), int(lineobj.get("Y"))
        w, h = int(lineobj.get("WIDTH")), int(lineobj.get("HEIGHT"))
        crops.append(img[y:y + h, x:x + w, :])

    t2 = time.time()
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="ocr") as ex:
        texts = list(ex.map(engine.recognizer.read, crops))
    t_recog = round(time.time() - t2, 1)

    lines = [t for t in texts if t and "□□□" not in t and "、、、" not in t]
    first = lines[0][:22] if lines else "(none)"
    print("[%s] detect %.1fs recog %.1fs lines=%d first=%r"
          % (m["file"], t_detect, t_recog, len(lines), first), flush=True)
    results.append({
        "file": m["file"], "source_url": m["source_url"], "pid": m["pid"], "page": m["page"],
        "img_w": img_w, "img_h": img_h, "detect_sec": t_detect, "recognize_sec": t_recog,
        "lines_total": len(texts), "lines_kept": len(lines),
        "first_line": first,
        "ocr_text_head": "\n".join(lines[:6]),
    })

total_detect = sum(r["detect_sec"] for r in results)
total_recog = sum(r["recognize_sec"] for r in results)
summary = {
    "engine_load_sec": load_sec,
    "n_images": len(results),
    "total_detect_sec": round(total_detect, 1),
    "total_recognize_sec": round(total_recog, 1),
    "avg_detect_sec": round(total_detect / len(results), 1),
    "avg_recognize_sec": round(total_recog / len(results), 1),
    "results": results,
}
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print("[done] load %.1fs | detect avg %.1fs x%d | recog avg %.1fs x%d"
      % (load_sec, summary["avg_detect_sec"], len(results), summary["avg_recognize_sec"], len(results)), flush=True)
print("[done] written:", OUT, flush=True)
