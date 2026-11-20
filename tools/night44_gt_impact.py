# -*- coding: utf-8 -*-
"""night44_gt_impact.py — GT 8 页上「被版面过滤的框」是否触碰 GT 行（NIGHT44 硬门）。

背景：Night43 的 GT 门走的是**检测层**重跑（night36_ocr_run.py 直接调 detector），
不经过 recognize_bytes，因此版面过滤对 GT 页的实际影响从未被测过。
NIGHT44 走产品流后发现 ndl_10301438_R0000002 有 6 个框被滤——必须逐框核对
是否与 GT 行（eval/ocr_gt_100.tsv + gt36/*/boxes.json 的 canonical line_no）重合。

判据：框与 GT 框的 IoU 或包含关系；任一 GT 行被滤 = FAIL。
产出: eval/night44_gt_impact.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EVAL = os.path.join(ROOT, "eval")
GT36 = os.path.join(EVAL, "ocr_samples", "gt36")


def inter(a, b):
    x0 = max(a["x"], b["x"])
    y0 = max(a["y"], b["y"])
    x1 = min(a["x"] + a["w"], b["x"] + b["w"])
    y1 = min(a["y"] + a["h"], b["y"] + b["h"])
    return max(0, x1 - x0) * max(0, y1 - y0)


def iou(a, b):
    i = inter(a, b)
    u = a["w"] * a["h"] + b["w"] * b["h"] - i
    return i / u if u else 0.0


def main():
    # 重跑产品流拿被滤框（与 night44_gt_run 同一配置）
    src = os.path.join(EVAL, "night44_gt_lines.json")
    with open(src, encoding="utf-8") as f:
        gt_run = {r["file"].rsplit(".", 1)[0]: r for r in json.load(f)["results"]}

    gt_rows = []
    with open(os.path.join(EVAL, "ocr_gt_100.tsv"), encoding="utf-8") as f:
        f.readline()
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            file_, line_no, gt = line.split("\t", 2)
            gt_rows.append({"file": file_, "line_no": int(line_no), "gt": gt})

    # 按页统计 GT 行
    by_file = {}
    for r in gt_rows:
        by_file.setdefault(r["file"], []).append(r)

    out = []
    n_bad = 0
    for fname, rows in sorted(by_file.items()):
        stem = fname.rsplit(".", 1)[0]
        bpath = os.path.join(GT36, stem, "boxes.json")
        if not os.path.exists(bpath):
            print("== %s (无 boxes.json，跳过)" % stem)
            continue
        with open(bpath, encoding="utf-8") as f:
            canon = {l["line_no"]: l for l in json.load(f)["lines"]}
        gt_boxes = []
        for r in rows:
            c = canon.get(r["line_no"])
            if c:
                gt_boxes.append({"line_no": r["line_no"], "gt": r["gt"],
                                 "x": c["x"], "y": c["y"], "w": c["w"], "h": c["h"]})

        filt = gt_run[stem].get("layout_filtered_boxes") or []
        # night44_gt_lines.json 只存了数量，这里按需重算（产品流，版面过滤 ON）
        if not filt:
            from backend.ocr_engine import get_engine
            eng = get_engine()
            with open(os.path.join(ROOT, "ocr_runtime", "samples", "batch20",
                                   stem + ".jpg"), "rb") as f:
                data = f.read()
            r = eng.recognize_bytes(data)
            filt = r["layout_filtered"]

        print("== %s  GT行=%d  被滤框=%d" % (stem, len(gt_boxes), len(filt)))
        for b in filt:
            hits = []
            for g in gt_boxes:
                i = inter(b, g)
                garea = g["w"] * g["h"]
                if i > 0:
                    hits.append({"line_no": g["line_no"], "iou": round(iou(b, g), 3),
                                 "cover_of_gt": round(i / garea, 3), "gt": g["gt"][:20]})
            status = "TOUCHES_GT" if hits else "no-gt"
            if hits:
                n_bad += 1
            print("   %-11s x=%4d y=%4d w=%3d h=%3d  %s"
                  % (status, b["x"], b["y"], b["w"], b["h"],
                     "; ".join("#%d iou=%.2f cover=%.2f %r"
                               % (h["line_no"], h["iou"], h["cover_of_gt"], h["gt"])
                               for h in hits) or ""))
            out.append({"file": stem, "box": b, "touches_gt": hits, "status": status})

    with open(os.path.join(EVAL, "night44_gt_impact.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump({"rows": out, "n_touching": n_bad}, f, ensure_ascii=False, indent=1)
    print("\nHARD GATE 被滤框触碰 GT 行 = %d（必须 0）: %s"
          % (n_bad, "PASS" if n_bad == 0 else "FAIL"))


if __name__ == "__main__":
    main()
