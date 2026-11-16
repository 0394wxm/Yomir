# -*- coding: utf-8 -*-
"""debug_ocr_boxes.py — 转储一张样张的 LINE 盒子 + 饱和度统计 + 识别文本（NIGHT3）。

用于从事实调 junk filter 阈值。用法:
    python -X utf8 tools/debug_ocr_boxes.py <sample.jpg>
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def main():
    img_path = sys.argv[1]
    data = open(img_path, "rb").read()
    from backend.ocr_engine import get_engine

    engine = get_engine()  # 建立 sys.path（numpy 等在 dlkotenocr-lite 侧）并加载模型

    import numpy as np  # noqa: E402
    from PIL import Image  # noqa: E402

    # 复刻 recognize 前半段，但打印每个盒子的判据数值
    from ndl_parser import convert_to_xml_string3
    from reading_order.xy_cut.eval import eval_xml
    import xml.etree.ElementTree as ET

    img = np.array(Image.open(__import__("io").BytesIO(data)).convert("RGB"))
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
    xmlstr = convert_to_xml_string3(img_w, img_h, "dbg", classeslist, resultobj)
    root = ET.fromstring("<OCRDATASET>" + xmlstr + "</OCRDATASET>")
    eval_xml(root, logger=None)
    print("image %dx%d" % (img_w, img_h))
    lines = root.findall(".//LINE")
    crops = []
    for lo in lines:
        x, y, w, h = (int(lo.get(k)) for k in ("X", "Y", "WIDTH", "HEIGHT"))
        crop = img[y:y + h, x:x + w]
        hsv = np.array(Image.fromarray(crop).convert("HSV")) if crop.size else np.zeros((1, 1, 3), dtype=np.uint8)
        sat = hsv[:, :, 1]
        crops.append(crop)
        print("box x=%4d y=%4d w=%4d h=%4d  x/w=%.2f y/h=%.2f w/w=%.2f  satMean=%5.1f satFrac=%.3f  %s"
              % (x, y, w, h, (x + w) / img_w, y / img_h, w / img_w,
                 float(sat.mean()), float((sat > 120).mean()),
                 "JUNK?" if engine._is_junk_line(img, x, y, w, h) else ""))
    with __import__("concurrent.futures", fromlist=["ThreadPoolExecutor"]).ThreadPoolExecutor(max_workers=4) as ex:
        texts = list(ex.map(engine.recognizer.read, crops))
    for lo, t in zip(lines, texts):
        print("  y=%4d %-20r" % (int(lo.get("Y")), (t or "")[:24]))


if __name__ == "__main__":
    main()
