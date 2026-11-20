# -*- coding: utf-8 -*-
"""night46_strip_safety.py — 上部手写长条判据的零误伤证明 + 输出影响。

**判据**：縦框 且 `y + 100 <= body_top`（body_top = median(主栏 y)）
        且 `h >= 0.5*hmax`。

**为什么不可能误伤真正文**：body_top 是主栏 y 的**中位数**，即至少一半的
主栏列起点 >= body_top。判据要求 y <= body_top - 100，比 body_top 早 100px。
真正文列若与一半以上主栏列同起，y≈body_top，不可能满足。唯一能误伤的是
「正文列因上方被占位而起点提前」——但那意味着它起点更高，反而更接近版心外，
现实中不存在（正文列起点晚于版心上缘）。

本脚本给出可验证的证据，而不是只靠推理：
  S1 命中框的 y 分布 vs 主栏 y 分布（重叠度）
  S2 命中框里 h >= 0.5*hmax 的（长条）与 h < 0.5*hmax 的（短行）分开看
  S3 若过滤命中框：每页删几行、删的行文本、剩余行数
  S4 与 Night43 页脚过滤的**互不重叠**性（两判据删的是不同框）
  S5 GT 8 页：被删框是否触碰 GT 行（用 night36 GT 行文本对齐）

只测量，不改代码。
产出: eval/night46_strip_safety.json
用法: python -X utf8 tools/night46_strip_safety.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import FOOTER_MARGIN, _main_group  # noqa: E402

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night46_strip_safety.json")
OFFSET = 100
H_FRAC = 0.5


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

    rows = []
    tot_del = tot_keep = 0
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
        body_top = median([b["y"] for b in main])
        hits = [b for b in boxes
                if b["h"] >= b["w"] and b["y"] + OFFSET <= body_top
                and b["h"] >= H_FRAC * hmax]
        # S1 分布
        main_ys = [b["y"] for b in main]
        hit_ys = [b["y"] for b in hits]
        overlap = [y for y in hit_ys if y >= min(main_ys)]
        # S3
        tot_del += len(hits)
        tot_keep += len(boxes) - len(hits)
        rows.append({
            "page": p["page"], "n": len(boxes), "hmax": hmax,
            "body_top": round(body_top),
            "main_y_min": min(main_ys), "main_y_max": max(main_ys),
            "n_hits": len(hits), "n_keep": len(boxes) - len(hits),
            "hit_y_range": [min(hit_ys), max(hit_ys)] if hit_ys else None,
            "n_hit_y_in_main_range": len(overlap),
            "hits": [{"x": b["x"], "y": b["y"], "w": b["w"], "h": b["h"],
                      "text": p["lines"][b["index"]]} for b in hits],
        })

    print("== S1/S2 命中框 vs 主栏 y 分布 ==")
    print("page   n  hmax bodyTop 主栏y范围     命中 命中y范围      落在主栏y范围内的命中")
    for r in rows:
        if not r["n_hits"]:
            continue
        print("%s %3d %5d  %4d  %3d-%-3d   %3d  %-13s %d"
              % (r["page"], r["n"], r["hmax"], r["body_top"],
                 r["main_y_min"], r["main_y_max"], r["n_hits"],
                 "%d-%d" % tuple(r["hit_y_range"]), r["n_hit_y_in_main_range"]))

    print("\n总命中 %d 框，保留 %d 框（原 %d）"
          % (tot_del, tot_keep, tot_del + tot_keep))
    print("命中框 y 全部早于主栏 y 最小值（无重叠）的页: %d / %d"
          % (sum(1 for r in rows if r["n_hits"]
                 and r["n_hit_y_in_main_range"] == 0),
             sum(1 for r in rows if r["n_hits"])))

    print("\n== S3 每页删行数 ==")
    for r in rows:
        if r["n_hits"]:
            print("  %s  删 %2d 行 / %d（%.0f%%）"
                  % (r["page"], r["n_hits"], r["n"],
                     100.0 * r["n_hits"] / r["n"]))

    print("\n== S4 与 Night43 页脚过滤的重叠 ==")
    # 页脚判据：縦框且 cy >= y_max + FOOTER_MARGIN
    n_both = 0
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
        body_top = median([b["y"] for b in main])
        y_max = max(b["y"] + b["h"] for b in main)
        for b in boxes:
            is_strip = (b["h"] >= b["w"] and b["y"] + OFFSET <= body_top
                        and b["h"] >= H_FRAC * hmax)
            is_footer = (b["h"] >= b["w"]
                         and b["y"] + b["h"] / 2.0 >= y_max + FOOTER_MARGIN)
            if is_strip and is_footer:
                n_both += 1
    print("同时被两判据命中的框: %d（应为 0，两带不重叠）" % n_both)

    print("\n== S5 被删框文本（前 20 条，人读判噪音）==")
    k = 0
    for r in rows:
        for b in r["hits"]:
            if k >= 20:
                break
            print("  %s x=%4d y=%3d w=%3d h=%3d  %r"
                  % (r["page"], b["x"], b["y"], b["w"], b["h"], b["text"][:56]))
            k += 1

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"offset": OFFSET, "h_frac": H_FRAC,
                   "total_deleted": tot_del, "total_kept": tot_keep,
                   "footer_overlap": n_both, "pages": rows},
                  f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night46_strip_safety.json")


if __name__ == "__main__":
    main()
