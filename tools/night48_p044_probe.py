# -*- coding: utf-8 -*-
"""night48_p044_probe.py — p044 两个已知漏滤框 + 全本同类系统性排查。

Night44 §7 如实记录 p044 还有两个页脚框没被滤掉：
  - '一元条同不出旨…' (h=150)
  - '大金表主' (dy -40，中心在主栏底之上 40px)
当时判为「判据已知边界，未修」。本脚本做两件事：

A) 把 p044 的原始框（filter_off）按当前判据跑一遍，逐框列出：
   主栏底 y_max、每框的 cy、dy=cy-y_max、h、h/hmax、文本、判定结果。
   找出这两个框为什么没被 judge_layout 抓到。

B) 全本 47 页做同类扫描：找出「cy 在 y_max 附近 ±FOOTER_GUARD 带内、
   但没被滤掉」的所有框，看漏滤是不是只有 p044 两例，还是有系统性问题。

只测量，不改代码。
产出: eval/night48_p044_probe.json
用法: python -X utf8 tools/night48_p044_probe.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import (  # noqa: E402
    FOOTER_MARGIN, _main_group, _median, judge_headnote_strip, judge_layout,
)

OFF = os.path.join(ROOT, "eval", "night44_full", "filter_off")
OUT = os.path.join(ROOT, "eval", "night48_p044_probe.json")

# 怀疑带：中心落在 y_max 上下这么大的范围里，都算「页脚可疑区」
GUARD = 80


def is_kana(c):
    return ("\u3041" <= c <= "\u309f") or ("\u30a1" <= c <= "\u30ff")


def is_kanji(c):
    return ("\u4e00" <= c <= "\u9fff") or ("\u3400" <= c <= "\u4dbf")


def kana_ratio(s):
    k = sum(1 for c in s if is_kana(c))
    h = sum(1 for c in s if is_kanji(c))
    return k / float(k + h) if (k + h) else 0.0


def load_pages():
    pages = []
    for fn in sorted(os.listdir(OFF)):
        if fn.endswith(".json"):
            with open(os.path.join(OFF, fn), encoding="utf-8") as f:
                pages.append(json.load(f))
    return pages


def probe_page(p, verbose=False):
    """返回 (rows, y_max, footer_cut) —— rows 是保留下来的框的详细记录。"""
    boxes = [dict(b) for b in p["line_boxes"]]
    if len(boxes) < 4:
        return [], None, None
    _miban, judged = judge_layout(boxes)
    kept_i = [i for i, (b, r) in enumerate(judged) if r is None]
    kept = [boxes[i] for i in kept_i]
    vert = [b for b in kept if b["h"] >= b["w"]]
    if not vert:
        return [], None, None
    hmax = max(b["h"] for b in vert)
    _m2, main = _main_group([dict(b) for b in kept])
    if not main:
        return [], None, None
    y_max = max(b["y"] + b["h"] for b in main)
    footer_cut = y_max + FOOTER_MARGIN
    body_top = _median([b["y"] for b in main])
    strips = judge_headnote_strip(kept, body_top=body_top, h_max=hmax)
    sk = {(b["x"], b["y"], b["w"], b["h"]) for b in strips}
    main_k = {(b["x"], b["y"], b["w"], b["h"]) for b in main}

    rows = []
    for i in kept_i:
        b = boxes[i]
        if (b["x"], b["y"], b["w"], b["h"]) in sk:
            continue
        t = p["lines"][i]
        cy = b["y"] + b["h"] / 2.0
        rows.append({
            "page": p["page"], "x": b["x"], "y": b["y"],
            "w": b["w"], "h": b["h"], "cy": round(cy, 1),
            "dy": round(cy - y_max, 1),
            "h_rel": round(b["h"] / float(hmax), 3),
            "is_vert": b["h"] >= b["w"],
            "is_main": (b["x"], b["y"], b["w"], b["h"]) in main_k,
            "kana": round(kana_ratio(t), 3),
            "text": t,
        })
    return rows, y_max, footer_cut


def main():
    pages = load_pages()
    by_page = {}
    for p in pages:
        rows, y_max, cut = probe_page(p)
        if y_max is None:
            continue
        by_page[p["page"]] = (rows, y_max, cut)

    print("== A) p044 逐框明细（主栏底 y_max 附近 ±%d）==" % GUARD)
    rows, y_max, cut = by_page.get("p044", ([], None, None))
    print("p044 y_max=%s  footer_cut=%s  保留框 %d"
          % (y_max, cut, len(rows)))
    near = [r for r in rows if abs(r["dy"]) <= GUARD]
    print("落在 ±%d 带内的保留框: %d 个" % (GUARD, len(near)))
    for r in sorted(near, key=lambda t: t["dy"]):
        print("  dy=%+7.1f h=%3d h_rel=%.2f vert=%d main=%d r=%.2f  %r"
              % (r["dy"], r["h"], r["h_rel"], r["is_vert"], r["is_main"],
                 r["kana"], r["text"][:60]))

    print("\n== B) 全本 47 页：dy 落在 ±%d 带内的保留框总数 ==" % GUARD)
    all_near = []
    for pg, (rs, ym, ct) in by_page.items():
        all_near.extend([r for r in rs if abs(r["dy"]) <= GUARD])
    print("共 %d 个，分布在 %d 页"
          % (len(all_near), len({r["page"] for r in all_near})))
    # 只看「明显是页脚」的：dy > 0（中心已越过主栏底）或 dy 在 -40..0 且很短
    suspect = [r for r in all_near if r["dy"] > 0]
    print("\n其中 dy > 0（中心已越过主栏底，最像页脚）: %d 个" % len(suspect))
    for r in sorted(suspect, key=lambda t: -t["dy"])[:40]:
        print("  %s dy=%+7.1f h=%3d h_rel=%.2f vert=%d main=%d r=%.2f  %r"
              % (r["page"], r["dy"], r["h"], r["h_rel"], r["is_vert"],
                 r["is_main"], r["kana"], r["text"][:56]))

    print("\n== C) 按页汇总 dy>0 的框数 ==")
    per = {}
    for r in suspect:
        per[r["page"]] = per.get(r["page"], 0) + 1
    for pg in sorted(per):
        print("  %s : %d" % (pg, per[pg]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"guard": GUARD,
                   "p044": {"y_max": by_page.get("p044", (None, None, None))[1],
                            "rows": by_page.get("p044", ([], None, None))[0]},
                   "all_near": all_near}, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night48_p044_probe.json")


if __name__ == "__main__":
    main()
