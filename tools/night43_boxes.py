# -*- coding: utf-8 -*-
"""night43_boxes.py — 检测-only：对 import_pid 页图跑检测器拿 LINE 框并落盘（NIGHT43 测量用）。

**不跑识别**（红线：不重跑全本 OCR）——只复刻 ocr_engine.recognize_bytes 的
检测→eval_xml 前半段，取 junk 过滤前的全部 LINE 框 + Night3 junk 判据数值。
产出: eval/night43_boxes.json
  {pages: [{page, file, img_w, img_h, detect_sec,
            lines: [{x,y,w,h,vert,sat_mean,sat_frac,junk3}]}]}
用法: python -X utf8 -I tools/night43_boxes.py [页码过滤如 p020] [更多页...]
      无参数 = 全部 pages/p*.jpg
"""
import json
import os
import sys
import time
import xml.etree.ElementTree as ET

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

PAGES_DIR = os.path.join(ROOT, "eval", "import_pid_11892692", "pages")
OUT = os.path.join(ROOT, "eval", "night43_boxes.json")


def main():
    only = set(a for a in sys.argv[1:] if a.startswith("p"))
    files = sorted(f for f in os.listdir(PAGES_DIR) if f.endswith(".jpg"))
    if only:
        files = [f for f in files if f[:-4] in only]
    print("[plan] %d pages" % len(files), flush=True)

    print("[engine] loading...", flush=True)
    t0 = time.time()
    engine = get_engine()
    print("[engine] load %.1fs" % (time.time() - t0), flush=True)

    out_pages = []
    for k, fname in enumerate(files, 1):
        path = os.path.join(PAGES_DIR, fname)
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
        detect_sec = round(time.time() - t1, 1)

        # 縦行中位高（与 ocr_engine 相同口径，供矮框判据数值参考）
        raw = []
        for lo in root.findall(".//LINE"):
            x, y = int(lo.get("X")), int(lo.get("Y"))
            w, h = int(lo.get("WIDTH")), int(lo.get("HEIGHT"))
            raw.append((x, y, w, h))
        vh = sorted(h for _, _, _, h in raw if h >= w)
        median_vh = vh[len(vh) // 2] if vh else None

        lines = []
        n_junk3 = 0
        for x, y, w, h in raw:
            crop = img[y:y + h, x:x + w]
            if crop.size:
                hsv = np.array(Image.fromarray(crop).convert("HSV"))
                sat = hsv[:, :, 1]
                s_mean = float(sat.mean())
                s_frac = float((sat > 120).mean())
            else:
                s_mean, s_frac = 0.0, 0.0
            junk3 = engine._is_junk_line(img, x, y, w, h, median_vh)
            n_junk3 += bool(junk3)
            lines.append({"x": x, "y": y, "w": w, "h": h, "vert": bool(h >= w),
                          "sat_mean": round(s_mean, 1), "sat_frac": round(s_frac, 3),
                          "junk3": bool(junk3)})
        print("[%d/%d] %s detect %.1fs lines=%d junk3=%d" % (k, len(files), fname,
              detect_sec, len(lines), n_junk3), flush=True)
        out_pages.append({"page": fname[:-4], "file": fname,
                          "img_w": img_w, "img_h": img_h, "detect_sec": detect_sec,
                          "median_vh": median_vh, "lines": lines})

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n_pages": len(out_pages), "pages": out_pages}, f,
                  ensure_ascii=False, indent=1)
    print("[done] written:", OUT, flush=True)


if __name__ == "__main__":
    main()
