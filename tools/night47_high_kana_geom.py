# -*- coding: utf-8 -*-
"""night47_high_kana_geom.py — 48 个高假名残留框的几何特征（能否纯几何分开）。

**为什么查这个**：Night43 起版面过滤坚持「纯几何、不看文本」，这是刻意设计
（避免依赖 OCR 结果的好坏）。如果这 48 个漏网噪音框能用几何分开，就可以
在不动这个设计原则的前提下修掉；如果不能，才需要考虑文本判据（产品拍板项）。

对每个高假名框给出：w、h、x、y、w/h、与主栏列的 x 重叠、是否在列缝、
是否短框（h < 0.3*hmax）。并统计这些特征与正文框的分离度。

只测量，不改代码。
产出: eval/night47_high_kana_geom.json
用法: python -X utf8 tools/night47_high_kana_geom.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import (  # noqa: E402
    MAIN_H_FRAC, _main_group, _median, judge_headnote_strip, judge_layout, _p90,
)

OFF = os.path.join(ROOT, "eval", "night44_full", "filter_off")
OUT = os.path.join(ROOT, "eval", "night47_high_kana_geom.json")


def is_kana(c):
    return ("\u3041" <= c <= "\u309f") or ("\u30a1" <= c <= "\u30ff")


def is_kanji(c):
    return ("\u4e00" <= c <= "\u9fff") or ("\u3400" <= c <= "\u4dbf")


def kana_ratio(s):
    k = sum(1 for c in s if is_kana(c))
    h = sum(1 for c in s if is_kanji(c))
    return k / float(k + h) if (k + h) else 0.0


def ov_x(a, b):
    lo = max(a["x"], b["x"])
    hi = min(a["x"] + a["w"], b["x"] + b["w"])
    return max(0, hi - lo) / max(1, min(a["w"], b["w"]))


def main():
    pages = []
    for fn in sorted(os.listdir(OFF)):
        if fn.endswith(".json"):
            with open(os.path.join(OFF, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    hi_rows = []
    lo_rows = []
    for p in pages:
        boxes = [dict(b) for b in p["line_boxes"]]
        if len(boxes) < 4:
            continue
        _m, judged = judge_layout(boxes)
        kept_i = [i for i, (b, r) in enumerate(judged) if r is None]
        kept = [boxes[i] for i in kept_i]
        vert = [b for b in kept if b["h"] >= b["w"]]
        if not vert:
            continue
        hmax = max(b["h"] for b in vert)
        _m2, main = _main_group([dict(b) for b in kept])
        if not main:
            continue
        body_top = _median([b["y"] for b in main])
        strips = judge_headnote_strip(kept, body_top=body_top, h_max=hmax)
        sk = {(b["x"], b["y"], b["w"], b["h"]) for b in strips}
        w90 = _p90([b["w"] for b in vert])
        main_k = {(b["x"], b["y"], b["w"], b["h"]) for b in main}
        for i in kept_i:
            b = boxes[i]
            if (b["x"], b["y"], b["w"], b["h"]) in sk:
                continue
            t = p["lines"][i]
            r = kana_ratio(t)
            rec = {
                "page": p["page"], "x": b["x"], "y": b["y"],
                "w": b["w"], "h": b["h"], "kana": round(r, 3),
                "hmax": hmax, "h_rel": round(b["h"] / float(hmax), 3),
                "w_rel": round(b["w"] / float(w90), 3),
                "is_main": (b["x"], b["y"], b["w"], b["h"]) in main_k,
                "n_main_ov": sum(1 for m in main
                                 if ov_x(b, m) >= 0.4),
                "in_body": b["y"] + b["h"] / 2.0 >= body_top,
                "text": t[:56],
            }
            (hi_rows if r > 0.15 else lo_rows).append(rec)

    def stat(name, rows, key):
        vs = sorted(r[key] for r in rows)
        if not vs:
            return
        print("  %-14s n=%3d  min=%.2f  p25=%.2f  中位=%.2f  p75=%.2f  max=%.2f"
              % (name, len(vs), vs[0], vs[len(vs) // 4], vs[len(vs) // 2],
                 vs[3 * len(vs) // 4], vs[-1]))

    print("== 几何特征对比：高假名（噪音）vs 低假名（正文）==")
    for key in ("h_rel", "w_rel", "n_main_ov"):
        print("\n%s:" % key)
        stat("高假名", hi_rows, key)
        stat("低假名", lo_rows, key)

    print("\n== 分类计数 ==")
    for key in ("is_main", "in_body"):
        h = sum(1 for r in hi_rows if r[key])
        l = sum(1 for r in lo_rows if r[key])
        print("  %-10s 高假名 %3d/%3d (%.0f%%)   低假名 %3d/%3d (%.0f%%)"
              % (key, h, len(hi_rows), 100.0 * h / max(1, len(hi_rows)),
                 l, len(lo_rows), 100.0 * l / max(1, len(lo_rows))))

    print("\n== 高假名框里「短框」（h_rel < 0.3）的占比 ==")
    sh = [r for r in hi_rows if r["h_rel"] < 0.3]
    sl = [r for r in lo_rows if r["h_rel"] < 0.3]
    print("  高假名 %d/%d (%.0f%%)   低假名 %d/%d (%.0f%%)"
          % (len(sh), len(hi_rows), 100.0 * len(sh) / max(1, len(hi_rows)),
             len(sl), len(lo_rows), 100.0 * len(sl) / max(1, len(lo_rows))))

    print("\n== 若加「h_rel < 0.3」判据会删掉多少 ==")
    print("  删 %d 框（其中高假名 %d、低假名 %d）"
          % (len(sh) + len(sl), len(sh), len(sl)))
    print("  → 低假名被误删 %d 框（正文短行，如列末 2-3 字）" % len(sl))

    print("\n== 高假名框按 h_rel 分档 ==")
    for lo, hi in [(0.0, 0.1), (0.1, 0.3), (0.3, 0.6), (0.6, 1.01)]:
        n = sum(1 for r in hi_rows if lo <= r["h_rel"] < hi)
        print("  h_rel %.1f-%.1f : %d" % (lo, hi, n))

    print("\n== 高假名框明细（按 h_rel 排序）==")
    for r in sorted(hi_rows, key=lambda t: t["h_rel"]):
        print("  %s h_rel=%.2f w_rel=%.2f main=%d ov=%d r=%.2f  x=%4d y=%3d "
              "w=%2d h=%3d  %r"
              % (r["page"], r["h_rel"], r["w_rel"], r["is_main"],
                 r["n_main_ov"], r["kana"], r["x"], r["y"], r["w"], r["h"],
                 r["text"]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n_high": len(hi_rows), "n_low": len(lo_rows),
                   "high": hi_rows}, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night47_high_kana_geom.json")


if __name__ == "__main__":
    main()
