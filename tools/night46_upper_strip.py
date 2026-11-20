# -*- coding: utf-8 -*-
"""night46_upper_strip.py — 上部手写长条：几何判据的全本零误伤验证。

**Night43 的否决理由要重审**：backend/ocr_layout.py L41-45 留档说
「p012/p017 上主栏若有顶格长列（miban.y=35），头注带落入版心内部，
判据越界误杀头注正文约 20 行」。但 `miban.y = min(主栏 y)`，而 p012/p017
的**手写长条本身就被误判为主栏**，所以 miban.y=35 正是被判定对象自己算出来的
——**循环论证**。

**稳健量**：`body_top = median(主栏 y)`。47 页实测 207-252，个别离群长条拉不动。

**判据**（纯几何，三个条件同时成立）：
  1. 縦框（h >= w）
  2. y + UPPER_OFFSET <= body_top        起点远高于正文上缘
  3. h >= STRIP_H_FRAC * hmax            足够长（排除头注短行）
第二条件把「长条起点」和「正文列起点」分开；第三条件把「长条」和「头注短行」
分开——头注短行起点也高，但 h 只有 150-180。

本脚本验证：命中哪些框、误伤哪些真正文列、以及对输出的影响。
只测量，不改代码。
产出: eval/night46_upper_strip.json
用法: python -X utf8 tools/night46_upper_strip.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import MAIN_H_FRAC, _main_group  # noqa: E402

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night46_upper_strip.json")

UPPER_OFFSETS = [60, 80, 100, 120, 150, 180]
STRIP_H_FRACS = [0.4, 0.5, 0.6]


def median(vs):
    s = sorted(vs)
    n = len(s)
    if not n:
        return 0.0
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def main():
    pages = []
    for fn in sorted(os.listdir(FULL)):
        if fn.endswith(".json"):
            with open(os.path.join(FULL, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    pre = []
    for p in pages:
        boxes = [dict(b, index=i) for i, b in enumerate(p["line_boxes"])]
        if len(boxes) < 4:
            continue
        vert = [b for b in boxes if b["h"] >= b["w"]]
        if not vert:
            continue
        hmax = max(b["h"] for b in vert)
        _miban, main = _main_group([dict(b) for b in boxes])
        if not main:
            continue
        pre.append((p, boxes, hmax, median([b["y"] for b in main])))

    print("== 灵敏度：命中框数（UPPER_OFFSET × STRIP_H_FRAC）==")
    hdr = "offset " + " ".join("h>=%.1f×hmax" % f for f in STRIP_H_FRACS)
    print(hdr)
    for off in UPPER_OFFSETS:
        cells = []
        for f in STRIP_H_FRACS:
            n = 0
            for p, boxes, hmax, bt in pre:
                n += sum(1 for b in boxes
                         if b["h"] >= b["w"] and b["y"] + off <= bt
                         and b["h"] >= f * hmax)
            cells.append("%5d(%d页)" % (n, sum(
                1 for p, boxes, hmax, bt in pre
                if any(b["h"] >= b["w"] and b["y"] + off <= bt
                       and b["h"] >= f * hmax for b in boxes))))
        print("%6d %s" % (off, "  ".join(cells)))

    # 选定组合
    OFF, FRAC = 100, 0.5
    print("\n== 选定：y + %d <= body_top  且  h >= %.1f×hmax ==" % (OFF, FRAC))
    rows = []
    for p, boxes, hmax, bt in pre:
        hits = [b for b in boxes
                if b["h"] >= b["w"] and b["y"] + OFF <= bt
                and b["h"] >= FRAC * hmax]
        # 被命中的框是否在主栏里（=会否影响 main_group）
        main_k = {(b["x"], b["y"], b["w"], b["h"])
                  for b in _main_group([dict(b) for b in boxes])[1]}
        rows.append({
            "page": p["page"], "n": len(boxes), "hmax": hmax,
            "body_top": round(bt), "n_hits": len(hits),
            "hits": [{"x": b["x"], "y": b["y"], "w": b["w"], "h": b["h"],
                      "y_offset": round(bt - b["y"]),
                      "is_main": (b["x"], b["y"], b["w"], b["h"]) in main_k,
                      "text": p["lines"][b["index"]][:70]} for b in hits],
        })

    tot = sum(r["n_hits"] for r in rows)
    print("命中 %d 框，分布在 %d 页"
          % (tot, sum(1 for r in rows if r["n_hits"])))
    for r in rows:
        if not r["n_hits"]:
            continue
        print("\n--- %s  hmax=%d body_top=%d  %d 框 ---"
              % (r["page"], r["hmax"], r["body_top"], r["n_hits"]))
        for b in r["hits"]:
            print("   x=%4d y=%3d w=%3d h=%3d  高出正文上缘 %3dpx  main=%s"
                  % (b["x"], b["y"], b["w"], b["h"], b["y_offset"],
                     "Y" if b["is_main"] else "N"))
            print("      %r" % b["text"])

    # 主栏列被误伤检查：命中框里 is_main=True 且「不是长条」的比例
    n_main_hit = sum(1 for r in rows for b in r["hits"] if b["is_main"])
    print("\n命中框里本来算主栏的: %d / %d" % (n_main_hit, tot))

    # body_top 分布（稳健性）
    bts = sorted(r["body_top"] for r in rows)
    print("body_top 分布: min=%d p25=%d med=%d p75=%d max=%d"
          % (bts[0], bts[len(bts) // 4], bts[len(bts) // 2],
             bts[3 * len(bts) // 4], bts[-1]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"upper_offset": OFF, "strip_h_frac": FRAC,
                   "sweep_offsets": UPPER_OFFSETS,
                   "sweep_h_fracs": STRIP_H_FRACS, "pages": rows},
                  f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night46_upper_strip.json")


if __name__ == "__main__":
    main()
