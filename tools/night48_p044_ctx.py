# -*- coding: utf-8 -*-
"""night48_p044_ctx.py — p044 两个疑似广告框的上下文（同列还有什么）。

前一步发现这两框中心在主栏底之上（dy=-70 / -40.5），所以不是页脚判据漏滤，
而是它们几何上就在正文区里。本脚本回答：它们是什么？

做法：取 p044 保留框，按 x 聚类成列，看这两框所在列里还有哪些框（x 重叠、
y 上下关系），以及它们与主栏的 x 关系（在栏内？在栏缝？在页边？）。
同时把这两框的文本按字符拆开，看是否有广告/書肆（出版社）特征词。

只测量，不改代码。
用法: python -X utf8 tools/night48_p044_ctx.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import (  # noqa: E402
    _main_group, _median, judge_headnote_strip, judge_layout,
)

OFF = os.path.join(ROOT, "eval", "night44_full", "filter_off")


def load_page(name):
    with open(os.path.join(OFF, name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def main():
    p = load_page("p044")
    boxes = [dict(b) for b in p["line_boxes"]]
    _miban, judged = judge_layout(boxes)
    kept_i = [i for i, (b, r) in enumerate(judged) if r is None]
    kept = [boxes[i] for i in kept_i]
    vert = [b for b in kept if b["h"] >= b["w"]]
    hmax = max(b["h"] for b in vert)
    _m2, main = _main_group([dict(b) for b in kept])
    body_top = _median([b["y"] for b in main])
    strips = judge_headnote_strip(kept, body_top=body_top, h_max=hmax)
    sk = {(b["x"], b["y"], b["w"], b["h"]) for b in strips}

    print("p044: 原始 %d 框, 保留 %d, 主栏 %d, hmax=%d, body_top=%.0f"
          % (len(boxes), len(kept_i), len(main), hmax, body_top))
    print("主栏 x 范围: %d .. %d"
          % (min(b["x"] for b in main),
             max(b["x"] + b["w"] for b in main)))
    print("主栏 y 范围: %d .. %d"
          % (min(b["y"] for b in main),
             max(b["y"] + b["h"] for b in main)))

    rows = []
    for i in kept_i:
        b = boxes[i]
        if (b["x"], b["y"], b["w"], b["h"]) in sk:
            continue
        rows.append((b, p["lines"][i]))

    # 找那两个目标框
    targets = [r for r in rows if r[1].startswith("一元条同不出旨")
               or r[1].startswith("大金表主")]
    print("\n== 目标框 ==")
    for b, t in targets:
        print("  x=%4d y=%3d w=%3d h=%3d  中心y=%.0f  %r"
              % (b["x"], b["y"], b["w"], b["h"],
                 b["y"] + b["h"] / 2.0, t))

    for b, t in targets:
        print("\n== x 与目标框重叠 ≥40%% 的所有保留框（同列）==")
        col = []
        for b2, t2 in rows:
            lo = max(b["x"], b2["x"])
            hi = min(b["x"] + b["w"], b2["x"] + b2["w"])
            ov = max(0, hi - lo) / max(1, min(b["w"], b2["w"]))
            if ov >= 0.4:
                col.append((b2, t2))
        col.sort(key=lambda r: r[0]["y"])
        for b2, t2 in col:
            mark = " <<<" if b2 is b else ""
            print("  y=%3d..%3d h=%3d w=%3d  %r%s"
                  % (b2["y"], b2["y"] + b2["h"], b2["h"], b2["w"],
                     t2[:52], mark))
        print("  → 同列共 %d 框" % len(col))

    print("\n== 全本 47 页：同一列里「最后一框之上还有正文、下面又冒出短框」的模式 ==")
    print("（p044 这两框的 x 在主栏范围内吗？下面按页统计 x 落在主栏 x 区间内")
    print("  但 h < 0.35*hmax 的保留框数，看 p044 是不是特例）")
    tot = {}
    for fn in sorted(os.listdir(OFF)):
        if not fn.endswith(".json"):
            continue
        q = json.load(open(os.path.join(OFF, fn), encoding="utf-8"))
        bx = [dict(b) for b in q["line_boxes"]]
        if len(bx) < 4:
            continue
        _mi, jd = judge_layout(bx)
        ki = [i for i, (b, r) in enumerate(jd) if r is None]
        kp = [bx[i] for i in ki]
        vt = [b for b in kp if b["h"] >= b["w"]]
        if not vt:
            continue
        hm = max(b["h"] for b in vt)
        _m3, mn = _main_group([dict(b) for b in kp])
        if not mn:
            continue
        bt = _median([b["y"] for b in mn])
        st = judge_headnote_strip(kp, body_top=bt, h_max=hm)
        skk = {(b["x"], b["y"], b["w"], b["h"]) for b in st}
        xlo = min(b["x"] for b in mn)
        xhi = max(b["x"] + b["w"] for b in mn)
        ymax_m = max(b["y"] + b["h"] for b in mn)
        n = 0
        for i in ki:
            b = bx[i]
            if (b["x"], b["y"], b["w"], b["h"]) in skk:
                continue
            if xlo <= b["x"] <= xhi and b["h"] < 0.35 * hm:
                if b["y"] + b["h"] / 2.0 > ymax_m - 120:
                    n += 1
        if n:
            tot[q["page"]] = n
    for pg in sorted(tot):
        print("  %s : %d" % (pg, tot[pg]))
    print("  → 共 %d 页有这种框，合计 %d 个"
          % (len(tot), sum(tot.values())))


if __name__ == "__main__":
    main()
