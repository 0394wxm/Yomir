# -*- coding: utf-8 -*-
"""night36_gt_crops.py — Night 36 GT 抄录辅助：只跑检测+xy_cut 切行，导出行 crop（NIGHT36）。

红线遵守：本脚本【不调用 recognizer】、不读不写任何 OCR 识别文本。
产出（eval/ocr_samples/gt36/<stem>/）：
  line_XX.png   — 第 XX 行（canonical 1-based，eval_xml 顺序、junk 过滤前）的 crop
  boxes.json    — 每行 bbox/尺寸/junk 标记（junk=朱印/界框候选，选行时排除）
用法: python tools/night36_gt_crops.py [file1 file2 ...]（不带参数=全部 19 张，跳过 0 行插图页）
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "ocr_runtime", "src"))
sys.path.append(os.environ.get("KANBUN_OCR_SITE", r"D:\dlkotenocr-lite\site-packages"))
from backend.ocr_engine import get_engine  # noqa: E402

from ndl_parser import convert_to_xml_string3  # noqa: E402
from reading_order.xy_cut.eval import eval_xml  # noqa: E402
import xml.etree.ElementTree as ET  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

SAMPLE_DIR = os.path.join(ROOT, "ocr_runtime", "samples", "batch20")
OUT_DIR = os.path.join(ROOT, "eval", "ocr_samples", "gt36")
SKIP = {"ndl_11892692_R0000002.jpg"}  # Night6 实证 0 行插图页

with open(os.path.join(SAMPLE_DIR, "manifest.json"), encoding="utf-8") as f:
    manifest = json.load(f)

wanted = set(sys.argv[1:])
print("[engine] loading...", flush=True)
engine = get_engine()

for m in manifest:
    if m["file"] in SKIP:
        print("[skip 0-line]", m["file"], flush=True)
        continue
    if wanted and m["file"] not in wanted:
        continue
    stem = m["file"][:-4]
    page_dir = os.path.join(OUT_DIR, stem)
    if os.path.exists(os.path.join(page_dir, "boxes.json")):
        print("[exists]", stem, flush=True)
        continue
    os.makedirs(page_dir, exist_ok=True)
    img = np.array(Image.open(os.path.join(SAMPLE_DIR, m["file"])).convert("RGB"))
    img_h, img_w = img.shape[:2]

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

    xmlstr = convert_to_xml_string3(img_w, img_h, m["file"], classeslist, resultobj)
    root = ET.fromstring("<OCRDATASET>" + xmlstr + "</OCRDATASET>")
    eval_xml(root, logger=None)

    raw_boxes = []
    for lineobj in root.findall(".//LINE"):
        raw_boxes.append({
            "x": int(lineobj.get("X")), "y": int(lineobj.get("Y")),
            "w": int(lineobj.get("WIDTH")), "h": int(lineobj.get("HEIGHT")),
        })
    vh = sorted(b["h"] for b in raw_boxes if b["h"] >= b["w"])
    median_vh = vh[len(vh) // 2] if vh else None

    boxes = []
    for i, b in enumerate(raw_boxes, 1):
        junk = engine._is_junk_line(img, b["x"], b["y"], b["w"], b["h"], median_vh)
        boxes.append(dict(b, line_no=i, junk=bool(junk)))
        crop = img[b["y"]:b["y"] + b["h"], b["x"]:b["x"] + b["w"], :]
        Image.fromarray(crop).save(os.path.join(page_dir, "line_%02d.png" % i))
    with open(os.path.join(page_dir, "boxes.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"file": m["file"], "pid": m["pid"], "page": m["page"],
                   "source_url": m["source_url"], "n_lines": len(boxes), "lines": boxes},
                  f, ensure_ascii=False, indent=1)
    n_junk = sum(1 for b in boxes if b["junk"])
    print("[%s] lines=%d junk=%d" % (stem, len(boxes), n_junk), flush=True)
print("[done]", flush=True)
