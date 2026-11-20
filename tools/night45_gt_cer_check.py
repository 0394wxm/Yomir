# -*- coding: utf-8 -*-
"""night45_gt_cer_check.py — 主栏重排对 GT 92 行 CER 的影响（NIGHT45 硬门）。

思路：**不跑新 OCR**——用已存档的 eval/night44_gt_lines.json（产品流输出，含 text +
坐标），离线把行序换成生产顺序（`_cluster_order` 的单元构造 + NIGHT45 的
`reorder_main_slots`），再按新顺序喂 eval_ocr_gt.py。

为什么能这样：eval_ocr_gt 的对齐是**按坐标**（boxes.json 的 line_no + x 簇聚类），
不依赖输出顺序；但 GT 行的「共享列」（一条列文本含多条目）用的是 x 簇拼接，
顺序会改变拼接结果——所以这个检查是有意义的。

产出: eval/night45_gt_cer.json + eval/night45_gt_lines_reordered.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import main_column_keys, reorder_main_slots  # noqa: E402
from tools.night45_cluster_proto import build_units  # noqa: E402

EVAL = os.path.join(ROOT, "eval")
GT36 = os.path.join(EVAL, "ocr_samples", "gt36")
SRC = os.path.join(EVAL, "night44_gt_lines.json")
OUT_JSON = os.path.join(EVAL, "night45_gt_lines_reordered.json")


def reorder(lines, boxes):
    """生产顺序：单元构造 → 单元内 y 排序 → 主栏槽位重排。"""
    if not boxes:
        return lines, boxes
    bxs = [dict(b, index=i) for i, b in enumerate(boxes)]
    main_keys = main_column_keys(bxs)
    units = build_units(bxs)
    for u in units:
        if u["kind"] == "col":
            u["items"] = sorted(u["items"], key=lambda t: t["y"])
            u["items"] = reorder_main_slots(u["items"], main_keys)
        else:
            u["items"] = sorted(u["items"], key=lambda t: -t["x"])
    units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
    seq = []
    for u in units:
        seq.extend(b["index"] for b in u["items"])
    assert sorted(seq) == list(range(len(boxes)))
    return [lines[i] for i in seq], [boxes[i] for i in seq]


def main():
    with open(SRC, encoding="utf-8") as f:
        doc = json.load(f)
    changed_pages = []
    for res in doc["results"]:
        stem = res["file"].rsplit(".", 1)[0]
        bpath = os.path.join(GT36, stem, "boxes.json")
        canon = {}
        if os.path.exists(bpath):
            with open(bpath, encoding="utf-8") as f:
                canon = {(l["x"], l["y"], l["w"], l["h"]): l["line_no"]
                         for l in json.load(f)["lines"]}
        boxes = [{"x": l["x"], "y": l["y"], "w": l["w"], "h": l["h"]}
                 for l in res["lines"]]
        texts = [l["text"] for l in res["lines"]]
        before = list(texts)
        new_texts, new_boxes = reorder(texts, boxes)
        if new_texts != before:
            changed_pages.append(stem)
        res["lines"] = [{"line_no": canon.get((b["x"], b["y"], b["w"], b["h"])),
                         "x": b["x"], "y": b["y"], "w": b["w"], "h": b["h"],
                         "text": t} for t, b in zip(new_texts, new_boxes)]
        print("[%s] lines=%d reordered=%s" % (stem, len(new_texts),
                                              new_texts != before), flush=True)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("\n顺序有变化的 GT 页: %d / %d -> %s"
          % (len(changed_pages), len(doc["results"]), changed_pages or "无"))
    print("[written] %s" % OUT_JSON)


if __name__ == "__main__":
    main()
