# -*- coding: utf-8 -*-
"""night45_headnote_check.py — 头注错位的**否证**记录（NIGHT45，离线）。

本脚本最初用来支持「头注被全局 x 排序切开」的假设，并度量一个「违规」
（头注排在所属列正文之后）。结论是**该假设不成立**：

  * 该「违规」定义把**所有非主栏框**都当成「必须排在所属列正文之前」的头注，
    但页面上大量非主栏框是**列中/列末的割注与手写批注**，它们本就该在正文之后；
  * 度量与原型（P1 头注归列）的构造同源 → 「重排后违规=0」是循环论证。

改用与原型无关的指标后（tools/night45_contiguity.py：按生产列定义度量列
连续性），原顺序 659 列**零打断**，P1 反而制造 48 处打断、31 页变差 →
P1 废弃。真正的缺陷另由 tools/night45_maincol_order.py 的 I5 定位
（并列主栏被跨列头注桥接后 y 排序判反，p021），修复见
`backend/ocr_layout.reorder_main_slots`。

本脚本保留为**否证证据**：它给出的 161/1245（13%）数字说明「非主栏框排在
正文之后」在版面里是常态，不是缺陷。产出 eval/night45_headnote.json。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import MAIN_COL_OVERLAP, _main_group  # noqa: E402

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night45_headnote.json")


def ov_x(a, b):
    lo = max(a["x"], b["x"])
    hi = min(a["x"] + a["w"], b["x"] + b["w"])
    return max(0, hi - lo) / max(1, min(a["w"], b["w"]))


def analyze(boxes):
    """返回 (n_head, n_cols, main_monotonic, violations)。"""
    miban, main = _main_group([dict(b) for b in boxes])
    if miban is None:
        return 0, 0, True, []
    main_keys = {(b["x"], b["y"], b["w"], b["h"]) for b in main}
    head = [i for i, b in enumerate(boxes)
            if (b["x"], b["y"], b["w"], b["h"]) not in main_keys]
    main_idx = [i for i, b in enumerate(boxes)
                if (b["x"], b["y"], b["w"], b["h"]) in main_keys]
    if not head or not main_idx:
        return len(head), 0, True, []

    cols = []
    for i in sorted(main_idx, key=lambda i: -(boxes[i]["x"] + boxes[i]["w"])):
        b = boxes[i]
        for c in cols:
            if any(ov_x(b, boxes[j]) >= MAIN_COL_OVERLAP for j in c):
                c.append(i)
                break
        else:
            cols.append([i])
    right = [max(boxes[i]["x"] + boxes[i]["w"] for i in c) for c in cols]
    monotonic = all(right[k] > right[k + 1] for k in range(len(right) - 1))

    owner = {}
    for h in head:
        best, bestv = None, -1.0
        for k, c in enumerate(cols):
            v = max(ov_x(boxes[h], boxes[j]) for j in c)
            if v > bestv:
                bestv, best = v, k
        if bestv <= 0:
            hcx = boxes[h]["x"] + boxes[h]["w"] / 2.0
            best = min(range(len(cols)),
                       key=lambda k: abs(hcx - (boxes[cols[k][0]]["x"]
                                                + boxes[cols[k][0]]["w"] / 2.0)))
        owner[h] = best

    pos = {i: k for k, i in enumerate(range(len(boxes)))}
    viol = []
    for h in head:
        k = owner[h]
        first = min(pos[j] for j in cols[k])
        if pos[h] > first:
            viol.append({"head_idx": h, "col": k,
                         "head_pos": pos[h], "col_first_pos": first})
    return len(head), len(cols), monotonic, viol


def main():
    pages = []
    for fn in sorted(os.listdir(FULL)):
        if fn.endswith(".json"):
            with open(os.path.join(FULL, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    rows = []
    tot_head = tot_viol = 0
    pages_with_head = 0
    for p in pages:
        boxes = p["line_boxes"]
        if not boxes:
            continue
        n_head, n_cols, mono, viol = analyze(boxes)
        if not n_head:
            continue
        pages_with_head += 1
        tot_head += n_head
        tot_viol += len(viol)
        rows.append({"page": p["page"], "n": len(boxes), "n_head": n_head,
                     "n_cols": n_cols, "main_monotonic": mono,
                     "viol": len(viol), "viol_detail": viol[:8]})

    print("== 否证记录：非主栏框排在所属列正文之后（不是缺陷）==")
    print("有非主栏框的页=%d  非主栏框合计=%d" % (pages_with_head, tot_head))
    print("「排在正文之后」=%d（%.0f%%）——版面常态：割注/批注本就在正文之后"
          % (tot_viol, 100.0 * tot_viol / max(1, tot_head)))
    mono_bad = [r["page"] for r in rows if not r["main_monotonic"]]
    print("主栏列序非右→左的页: %s" % (mono_bad or "无（47/47 单调）"))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"total_head": tot_head, "total_after_body": tot_viol,
                   "pages_with_head": pages_with_head, "pages": rows}, f,
                  ensure_ascii=False, indent=1)
    print("\n[written] eval/night45_headnote.json")


if __name__ == "__main__":
    main()
