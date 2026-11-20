# -*- coding: utf-8 -*-
"""night46_strip_gt.py — 上部手写长条判据的 GT 影响（零触碰证明）。

把 GT 8 页（eval/night36_ocr_lines.json 的 results）的框坐标，与
`night46_strip_safety.py` 的命中判据对齐，检查：
  G1 GT 8 页里有没有框被判据命中（= 会误删 GT 行）
  G2 GT 页的 body_top / 命中情况
  G3 若 GT 页零命中，则 GT CER 必然逐位不变（结构性证明，不靠跑）

只测量，不改代码。
用法: python -X utf8 tools/night46_strip_gt.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import _main_group  # noqa: E402

GT = os.path.join(ROOT, "eval", "night36_ocr_lines.json")
FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OFFSET = 100
H_FRAC = 0.5


def median(vs):
    s = sorted(vs)
    n = len(s)
    if not n:
        return 0.0
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def main():
    gt = json.load(open(GT, encoding="utf-8"))["results"]
    print("GT 8 页: %s" % [(r["pid"], r["page"], len(r["lines"])) for r in gt])

    print("\n== 对 GT 页自己的框跑判据 ==")
    tot_hit = 0
    for r in gt:
        boxes = [dict(b, index=i) for i, b in enumerate(r["lines"])]
        if not boxes:
            continue
        vert = [b for b in boxes if b["h"] >= b["w"]]
        if not vert:
            print("  %s/%s  无縦框" % (r["pid"], r["page"]))
            continue
        hmax = max(b["h"] for b in vert)
        _miban, main = _main_group([dict(b) for b in boxes])
        if not main:
            print("  %s/%s  版心估不出（%d 框）" % (r["pid"], r["page"], len(boxes)))
            continue
        body_top = median([b["y"] for b in main])
        hits = [b for b in boxes
                if b["h"] >= b["w"] and b["y"] + OFFSET <= body_top
                and b["h"] >= H_FRAC * hmax]
        tot_hit += len(hits)
        print("  %s/%s  n=%2d hmax=%3d bodyTop=%3d  命中 %d"
              % (r["pid"], r["page"], len(boxes), hmax, body_top, len(hits)))
        for b in hits:
            print("       x=%4d y=%3d w=%3d h=%3d  %r"
                  % (b["x"], b["y"], b["w"], b["h"],
                     r["lines"][b["index"]]["text"][:50]))

    print("\n== 归档 47 页里，GT 8 页对应的页命中情况 ==")
    # GT 页的 pid/page 与归档 p0xx 的对应：归档页名是 p001..p047（論語 47 页），
    # GT 是另外 8 页（不同书）。两者集合不同，需确认是否重叠。
    arch_pages = sorted(fn[:-5] for fn in os.listdir(FULL) if fn.endswith(".json"))
    gt_pages = ["%s/%s" % (r["pid"], r["page"]) for r in gt]
    print("归档页: %s ... %s（%d 页，論語）"
          % (arch_pages[:3], arch_pages[-3:], len(arch_pages)))
    print("GT 页: %s" % gt_pages)
    print("→ 两集合是否重叠: %s"
          % ("是" if set(arch_pages) & set(gt_pages) else "否（GT 是另外 8 页样张）"))

    print("\n== 结论 ==")
    print("GT 8 页被本判据命中的框数: %d" % tot_hit)
    if tot_hit == 0:
        print("→ GT CER 结构性不变（判据在 GT 页上零命中，不可能删 GT 行）")
    else:
        print("→ 有命中，需实跑 GT CER 验证")

    # 也给出：GT 页的最小 y 与 body_top 的差（说明为何零命中）
    print("\n== GT 页 y 分布（为何零命中）==")
    for r in gt:
        boxes = r["lines"]
        if not boxes:
            continue
        ys = sorted(b["y"] for b in boxes)
        print("  %s/%s  y min=%d max=%d  n=%d"
              % (r["pid"], r["page"], ys[0], ys[-1], len(ys)))


if __name__ == "__main__":
    main()
