# -*- coding: utf-8 -*-
"""night47_residual.py — 用**当前代码**过滤后的残留噪音盘点。

**为什么重做**：night47_kana_ratio.py 读的是 `eval/night44_full/filter_on`
归档，那是 **Night44 生成的**（只有页脚带判据，没有 Night46 的
headnote_strip）。于是 p031 的 13 个手写长条在归档里还在，被误报成
「几何漏掉的残留噪音」。必须用当前代码重跑过滤。

**本脚本**：在 filter_off 的 47 页原始框上跑**当前生产判据**
（judge_layout + judge_headnote_strip），得到「现在真的会输出的框」，
然后按假名比率分类：

  R1 当前过滤后的框数（应 = 1832 - 223 - 62 = 1547，但 junk 前置剔除的
     不在 filter_off 里，故以实测为准）
  R2 假名比率分布
  R3 假名比率 > 0.15 的残留框逐条列出（**这才是真正的漏网噪音**）
  R4 假名比率 > 0.15 的框里，有多少是 GT 正文行（误伤风险）
  R5 阈值灵敏度：0.10 / 0.15 / 0.20 / 0.30 各会删多少、GT 会伤多少

只测量，不改代码。
产出: eval/night47_residual.json
用法: python -X utf8 tools/night47_residual.py
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
OUT = os.path.join(ROOT, "eval", "night47_residual.json")
THRESHOLDS = [0.10, 0.15, 0.20, 0.30]


def is_kana(c):
    return ("\u3041" <= c <= "\u309f") or ("\u30a1" <= c <= "\u30ff")


def is_kanji(c):
    return ("\u4e00" <= c <= "\u9fff") or ("\u3400" <= c <= "\u4dbf")


def kana_ratio(s):
    k = sum(1 for c in s if is_kana(c))
    h = sum(1 for c in s if is_kanji(c))
    return k / float(k + h) if (k + h) else 0.0


def filter_current(boxes):
    """当前生产判据：页脚带 + 上部手写长条。返回 (保留框索引集合, 计数)。"""
    _m, judged = judge_layout(boxes)
    kept = [b for b, r in judged if r is None]
    n_footer = sum(1 for b, r in judged if r is not None)
    vert = [b for b in kept if b["h"] >= b["w"]]
    strips = []
    if vert:
        _m2, main2 = _main_group([dict(b) for b in kept])
        if main2:
            strips = judge_headnote_strip(
                kept, body_top=_median([b["y"] for b in main2]),
                h_max=max(b["h"] for b in vert))
    sk = {(b["x"], b["y"], b["w"], b["h"]) for b in strips}
    keep = {i for i, b in enumerate(boxes)
            if (b["x"], b["y"], b["w"], b["h"]) not in sk}
    # 页脚已在 judged 里剔除
    foot_k = {(b["x"], b["y"], b["w"], b["h"])
              for b, r in judged if r is not None}
    keep = {i for i in keep
            if (boxes[i]["x"], boxes[i]["y"], boxes[i]["w"],
                boxes[i]["h"]) not in foot_k}
    return keep, n_footer, len(strips)


def main():
    pages = []
    for fn in sorted(os.listdir(OFF)):
        if fn.endswith(".json"):
            with open(os.path.join(OFF, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    rows = []
    all_kept = []
    tot_orig = tot_keep = tot_foot = tot_strip = 0
    for p in pages:
        boxes = [dict(b) for b in p["line_boxes"]]
        if len(boxes) < 4:
            continue
        keep, n_foot, n_strip = filter_current(boxes)
        tot_orig += len(boxes)
        tot_keep += len(keep)
        tot_foot += n_foot
        tot_strip += n_strip
        high = []
        for i in sorted(keep):
            t = p["lines"][i]
            r = kana_ratio(t)
            all_kept.append((p["page"], r, t))
            if r > 0.15:
                b = boxes[i]
                high.append({"x": b["x"], "y": b["y"], "w": b["w"], "h": b["h"],
                             "kana_ratio": round(r, 3), "text": t})
        rows.append({"page": p["page"], "n_orig": len(boxes),
                     "footer": n_foot, "strip": n_strip,
                     "keep": len(keep), "n_high": len(high), "high": high})

    print("== R1 当前判据过滤后 ==")
    print("原始 %d 框 → 页脚滤 %d + 上部滤 %d → 保留 %d"
          % (tot_orig, tot_foot, tot_strip, tot_keep))
    print("（junk 前置剔除的框不在 filter_off 里，故 2056≠%d）" % tot_orig)

    print("\n== R2 保留框的假名比率分布 ==")
    bins = [(0.0, 0.01), (0.01, 0.05), (0.05, 0.10), (0.10, 0.15),
            (0.15, 0.25), (0.25, 0.40), (0.40, 0.60), (0.60, 1.01)]
    vals = [r for _p, r, _t in all_kept]
    for lo, hi in bins:
        n = sum(1 for v in vals if lo <= v < hi)
        print("  %.2f-%.2f  %4d  %5.1f%%"
              % (lo, hi, n, 100.0 * n / max(1, len(vals))))
    print("  合计 %d 框" % len(vals))

    print("\n== R3 假名比率 > 0.15 的残留框（真正的漏网噪音）==")
    tot_high = sum(r["n_high"] for r in rows)
    print("合计 %d 框（%.1f%%），分布在 %d 页"
          % (tot_high, 100.0 * tot_high / max(1, tot_keep),
             sum(1 for r in rows if r["n_high"])))
    for r in rows:
        if r["n_high"]:
            print("\n--- %s  %d / %d 框 ---"
                  % (r["page"], r["n_high"], r["keep"]))
            for b in r["high"]:
                print("   r=%.2f x=%4d y=%3d w=%3d h=%3d  %r"
                      % (b["kana_ratio"], b["x"], b["y"], b["w"], b["h"],
                         b["text"][:58]))

    print("\n== R5 阈值灵敏度（会删多少 / GT 会伤多少）==")
    print("阈值   删框数  占保留%   其中 GT 正文行")
    gt = json.load(open(os.path.join(ROOT, "eval", "night36_ocr_lines.json"),
                        encoding="utf-8"))["results"]
    gt_texts = set()
    for r in gt:
        for ln in r["lines"]:
            gt_texts.add(ln["text"])
    for th in THRESHOLDS:
        n = sum(1 for _p, r, _t in all_kept if r > th)
        n_gt = sum(1 for _p, r, t in all_kept if r > th and t in gt_texts)
        print("%.2f   %4d    %5.1f%%     %d"
              % (th, n, 100.0 * n / max(1, len(all_kept)), n_gt))

    print("\n== R4 高假名框与 GT 的重叠（误伤风险）==")
    hit = [(p, round(r, 2), t) for p, r, t in all_kept
           if r > 0.15 and t in gt_texts]
    print("假名>0.15 且文本与 GT 正文行完全相同的: %d" % len(hit))
    for h in hit[:10]:
        print("  %s r=%.2f %r" % h)

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"thresholds": THRESHOLDS,
                   "totals": {"orig": tot_orig, "footer": tot_foot,
                              "strip": tot_strip, "keep": tot_keep},
                   "n_high_015": tot_high, "pages": rows},
                  f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night47_residual.json")


if __name__ == "__main__":
    main()
