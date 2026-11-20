# -*- coding: utf-8 -*-
"""night43_stats.py — 噪音行 vs 正文列的框几何分布统计（NIGHT43 测量核心）。

与过滤器实现（backend/ocr_layout.py）同款判据，跑在选样页的「行文本↔框」配对上，
产出 noise/body 两组的判据数值分布 → 阈值依据 + 错滤检查。
标注表只覆盖 noise 白名单（eval/night43_labels.json）；其余行一律按 body 对待，
因此「body 错滤」= 被滤但不在 noise 白名单里的行——必须为 0。

输入: eval/night43_pair.json / eval/night43_labels.json / eval/night43_boxes.json
输出: stdout 分布表 + eval/night43_stats.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL = os.path.join(ROOT, "eval")
sys.path.insert(0, ROOT)
from backend.ocr_layout import (  # noqa: E402
    FOOTER_MARGIN, MAIN_H_FRAC, MAIN_W_FRAC, MIN_MAIN, judge_layout,
)


def load(name):
    with open(os.path.join(EVAL, name), encoding="utf-8") as f:
        return json.load(f)


def main():
    pair = load("night43_pair.json")
    labels = load("night43_labels.json")
    boxes = load("night43_boxes.json")
    imgsz = {p["page"]: (p["img_w"], p["img_h"]) for p in boxes["pages"]}

    rows = []
    for pg in pair["pages"]:
        iw, ih = imgsz[pg["page"]]
        bs = [dict(p) for p in pg["pairs"]]
        miban, judged = judge_layout(bs, iw, ih)
        noise = set(labels.get(pg["page"], {}).get("noise", []))
        y_max = None
        if miban:
            y_max = miban["y"] + miban["h"]
        for b, reason in judged:
            rows.append({"page": pg["page"], "text": b["text"],
                         "x": b["x"], "y": b["y"], "w": b["w"], "h": b["h"],
                         "cy": round(b["y"] + b["h"] / 2.0),
                         "dy_ymax": (round(b["y"] + b["h"] / 2.0 - y_max) if y_max else None),
                         "reason": reason,
                         "label": "noise" if b["text"] in noise else "body"})

    with open(os.path.join(EVAL, "night43_stats.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"main_h_frac": MAIN_H_FRAC, "main_w_frac": MAIN_W_FRAC,
                   "min_main": MIN_MAIN, "footer_margin": FOOTER_MARGIN,
                   "rows": rows}, f, ensure_ascii=False, indent=1)

    print("== 判据: main h>=%.2f*hmax & w>=%.2f*p90w; footer cy>=y_max%+d; 无 strip =="
          % (MAIN_H_FRAC, MAIN_W_FRAC, FOOTER_MARGIN))
    for kind in ("noise", "body"):
        sel = [r for r in rows if r["label"] == kind]
        n = len(sel)
        got = [r for r in sel if r["reason"]]
        print("[%s] n=%d  caught=%d" % (kind, n, len(got)))
        if kind == "body":
            print("  >>> body 错滤 = %d（硬门: 必须 0）" % len(got))
            for r in got:
                print("    WRONG %-5s %-12s x=%4d y=%4d w=%3d h=%4d  %r"
                      % (r["page"], r["reason"], r["x"], r["y"], r["w"], r["h"], r["text"]))
        else:
            miss = [r for r in sel if not r["reason"]]
            print("  noise 漏滤 = %d" % len(miss))
            for r in miss:
                print("    MISS  %-5s x=%4d y=%4d w=%3d h=%4d cy=%4d  %r"
                      % (r["page"], r["x"], r["y"], r["w"], r["h"], r["cy"], r["text"]))

    # 判据数值分布（含 cy - y_max），报告引用
    for kind in ("noise", "body"):
        sel = [r for r in rows if r["label"] == kind]
        if not sel:
            continue
        for key in ("cy", "h", "dy_ymax"):
            vs = sorted(r[key] for r in sel if r[key] is not None)
            if not vs:
                continue
            n = len(vs)
            print("[%s] %-7s min=%d p5=%d p25=%d med=%d p75=%d p95=%d max=%d"
                  % (kind, key, vs[0], vs[max(0, n // 20)], vs[n // 4], vs[n // 2],
                     vs[(3 * n) // 4], vs[min(n - 1, 19 * n // 20)], vs[-1]))

    # 每页 caught/n
    print("-- per page --")
    pages = []
    for pg in pair["pages"]:
        sel = [r for r in rows if r["page"] == pg["page"]]
        pages.append("%s %d/%d" % (pg["page"], sum(1 for r in sel if r["reason"]), len(sel)))
    print("  " + "  ".join(pages))


if __name__ == "__main__":
    main()
