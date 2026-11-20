# -*- coding: utf-8 -*-
"""night44_gt_run.py — 产品流（recognize_bytes，版面过滤 ON）跑 8 张 GT 页（NIGHT44 回归门）。

Night43 的 GT 门是拿**检测层**重跑的；本脚本走**引擎产品流**，确认过滤接入后
92 行 GT 的 CER 与 Night41 产品流基线（norm micro 0.3053）逐位一致。

输出格式与 night36_ocr_lines.json 相同（line_no/x/y/w/h/text），
可直接喂 tools/eval_ocr_gt.py：
    python -X utf8 tools/eval_ocr_gt.py eval/night44_gt_lines.json eval/night44_gt_cer.json

注意：GT 页样张在 ocr_runtime/samples/batch20（与 11892692 全本页图不是同一份文件），
line_no 口径 = 该样张的 eval_xml 顺序（junk 过滤前）——但产品流会先剔 junk 框，
所以这里用产品流返回的 line_boxes 坐标反查 boxes.json 的行号。
"""
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

os.environ.setdefault("KANBUN_OCR_LAYOUT_FILTER", "1")

from backend.ocr_engine import get_engine  # noqa: E402

SAMPLE_DIR = os.path.join(ROOT, "ocr_runtime", "samples", "batch20")
GT36 = os.path.join(ROOT, "eval", "ocr_samples", "gt36")
OUT = os.path.join(ROOT, "eval", "night44_gt_lines.json")

GT_STEMS = [
    "ndl_11892692_R0000003", "ndl_11892692_R0000004", "ndl_11892692_R0000005",
    "ndl_1033232_R0000003", "ndl_10301438_R0000002", "ndl_10301438_R0000003",
    "ndl_781192_R0000003", "ndl_781193_R0000003",
]


def main():
    with open(os.path.join(SAMPLE_DIR, "manifest.json"), encoding="utf-8") as f:
        manifest = {m["file"]: m for m in json.load(f)}

    t0 = time.time()
    engine = get_engine()
    print("[engine] load %.1fs" % (time.time() - t0), flush=True)

    results = []
    for stem in GT_STEMS:
        fname = stem + ".jpg"
        with open(os.path.join(SAMPLE_DIR, fname), "rb") as f:
            data = f.read()
        t1 = time.time()
        r = engine.recognize_bytes(data)
        dt = round(time.time() - t1, 1)

        # 产品流坐标 → boxes.json canonical line_no（坐标精确匹配）
        bpath = os.path.join(GT36, stem, "boxes.json")
        canon = []
        if os.path.exists(bpath):
            with open(bpath, encoding="utf-8") as f:
                canon = json.load(f)["lines"]

        def find_no(b):
            for c in canon:
                if (c["x"], c["y"], c["w"], c["h"]) == (b["x"], b["y"], b["w"], b["h"]):
                    return c["line_no"]
            return None

        lines = []
        n_unmatched = 0
        for text, b in zip(r["lines"], r["line_boxes"]):
            no = find_no(b)
            if no is None:
                n_unmatched += 1
            lines.append({"line_no": no, "x": b["x"], "y": b["y"], "w": b["w"],
                          "h": b["h"], "text": text})
        print("[%s] %.1fs lines=%d layout=%d junk=%d unmatched_no=%d"
              % (fname, dt, r["line_count"], len(r["layout_filtered"]),
                 r["junk_filtered"], n_unmatched), flush=True)
        results.append({
            "file": fname, "pid": manifest[fname]["pid"], "page": manifest[fname]["page"],
            "detect_sec": None, "recognize_sec": dt,
            "boxes_n_lines": len(canon), "ocr_n_lines": len(lines),
            "layout_filtered": len(r["layout_filtered"]),
            "junk_filtered": r["junk_filtered"],
            "unmatched_line_no": n_unmatched,
            "lines": lines,
        })

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n_pages": len(results), "results": results}, f,
                  ensure_ascii=False, indent=2)
    print("[done] written: %s" % OUT, flush=True)


if __name__ == "__main__":
    main()
