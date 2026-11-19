# -*- coding: utf-8 -*-
"""night36_ocr_run.py — 对有 GT 的 8 页跑完整 OCR，导出每行文本+坐标（NIGHT36）。

GT 已冻结后运行（评测阶段，抄录红线只约束抄录过程）。
行号口径与 boxes.json 一致：eval_xml 顺序、junk 过滤前、canonical 1-based。
产出: eval/night36_ocr_lines.json（每行 line_no/x/y/w/h/text + 每页耗时）
"""
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "ocr_runtime", "src"))
sys.path.append(os.environ.get("KANBUN_OCR_SITE", r"D:\dlkotenocr-lite\site-packages"))
from backend.ocr_engine import get_engine  # noqa: E402

from ndl_parser import convert_to_xml_string3  # noqa: E402
from reading_order.xy_cut.eval import eval_xml  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

SAMPLE_DIR = os.path.join(ROOT, "ocr_runtime", "samples", "batch20")
GT36 = os.path.join(ROOT, "eval", "ocr_samples", "gt36")
OUT = os.path.join(ROOT, "eval", "night36_ocr_lines.json")

GT_STEMS = [
    "ndl_11892692_R0000003", "ndl_11892692_R0000004", "ndl_11892692_R0000005",
    "ndl_1033232_R0000003", "ndl_10301438_R0000002", "ndl_10301438_R0000003",
    "ndl_781192_R0000003", "ndl_781193_R0000003",
]

with open(os.path.join(SAMPLE_DIR, "manifest.json"), encoding="utf-8") as f:
    manifest = {m["file"]: m for m in json.load(f)}

print("[engine] loading...", flush=True)
t0 = time.time()
engine = get_engine()
load_sec = round(time.time() - t0, 1)
print("[engine] load %.1fs" % load_sec, flush=True)

results = []
for stem in GT_STEMS:
    fname = stem + ".jpg"
    path = os.path.join(SAMPLE_DIR, fname)
    img = np.array(Image.open(path).convert("RGB"))
    img_h, img_w = img.shape[:2]

    t1 = time.time()
    detections = engine.detector.detect(img)
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
    xmlstr = convert_to_xml_string3(img_w, img_h, fname, classeslist, resultobj)
    root = ET.fromstring("<OCRDATASET>" + xmlstr + "</OCRDATASET>")
    eval_xml(root, logger=None)
    t_detect = round(time.time() - t1, 1)

    lineobjs = []
    for lineobj in root.findall(".//LINE"):
        x, y = int(lineobj.get("X")), int(lineobj.get("Y"))
        w, h = int(lineobj.get("WIDTH")), int(lineobj.get("HEIGHT"))
        lineobjs.append((x, y, w, h, img[y:y + h, x:x + w, :]))

    t2 = time.time()
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="ocr") as ex:
        texts = list(ex.map(engine.recognizer.read, [c for _, _, _, _, c in lineobjs]))
    t_recog = round(time.time() - t2, 1)

    # 与 boxes.json 的行号对齐校验
    bpath = os.path.join(GT36, stem, "boxes.json")
    box_n = None
    if os.path.exists(bpath):
        with open(bpath, encoding="utf-8") as f:
            box_n = json.load(f)["n_lines"]

    lines = []
    for i, ((x, y, w, h, _), txt) in enumerate(zip(lineobjs, texts), 1):
        lines.append({"line_no": i, "x": x, "y": y, "w": w, "h": h, "text": txt})
    print("[%s] detect %.1fs recog %.1fs lines=%d (boxes n_lines=%s)"
          % (fname, t_detect, t_recog, len(lines), box_n), flush=True)
    results.append({
        "file": fname, "pid": manifest[fname]["pid"], "page": manifest[fname]["page"],
        "img_w": img_w, "img_h": img_h, "detect_sec": t_detect, "recognize_sec": t_recog,
        "boxes_n_lines": box_n, "ocr_n_lines": len(lines), "lines": lines,
    })

out = {"engine_load_sec": load_sec, "n_pages": len(results), "results": results}
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("[done] written:", OUT, flush=True)
