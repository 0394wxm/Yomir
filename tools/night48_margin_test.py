# -*- coding: utf-8 -*-
"""night48_margin_test.py — 未配对窄框是否在「主栏 x 区间之外」（页边/栏缝）。

前一步得到 71 个未配对窄框。若它们是手写書き入れ，常见位置是页边或栏缝；
若是割注（正文），应紧贴主栏列。本脚本测三个几何量：

  M1  x+w > 主栏右缘（伸出右页边）
  M2  x < 主栏左缘（伸出左页边）
  M3  距最近主栏列的横向间隙 gap / 主栏宽（割注应 ≈0）

并按 h_rel 分档，看「全高未配对」（疑似割注缺对）与「矮未配对」
（疑似手写）能否被 M1-M3 分开。

只测量，不改代码。
产出: eval/night48_margin_test.json
用法: python -X utf8 tools/night48_margin_test.py
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
OUT = os.path.join(ROOT, "eval", "night48_margin_test.json")


def ov(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def page_ctx(q):
    bx = [dict(b) for b in q["line_boxes"]]
    if len(bx) < 4:
        return None
    _mi, jd = judge_layout(bx)
    ki = [i for i, (b, r) in enumerate(jd) if r is None]
    kp = [bx[i] for i in ki]
    vt = [b for b in kp if b["h"] >= b["w"]]
    if not vt:
        return None
    hm = max(b["h"] for b in vt)
    _m3, mn = _main_group([dict(b) for b in kp])
    if not mn:
        return None
    bt = _median([b["y"] for b in mn])
    st = judge_headnote_strip(kp, body_top=bt, h_max=hm)
    skk = {(b["x"], b["y"], b["w"], b["h"]) for b in st}
    wmed = _median([b["w"] for b in mn])
    if wmed <= 0:
        return None
    thin = []
    for i in ki:
        b = bx[i]
        if (b["x"], b["y"], b["w"], b["h"]) in skk:
            continue
        if b["w"] / float(wmed) < 0.6 and b["h"] >= b["w"]:
            thin.append((b, q["lines"][i]))
    return thin, mn, wmed, hm, bt


def has_partner(a, thin, wmed):
    for b, _t in thin:
        if b is a:
            continue
        if ov(a["x"], a["x"] + a["w"], b["x"], b["x"] + b["w"]) > 0:
            continue
        gap = min(abs(a["x"] - (b["x"] + b["w"])),
                  abs(b["x"] - (a["x"] + a["w"])))
        if gap > 1.2 * wmed:
            continue
        yo = ov(a["y"], a["y"] + a["h"], b["y"], b["y"] + b["h"])
        if yo < 0.7 * min(a["h"], b["h"]):
            continue
        if a["w"] + b["w"] + gap > 1.35 * wmed:
            continue
        return True
    return False


def main():
    pages = []
    for fn in sorted(os.listdir(OFF)):
        if fn.endswith(".json"):
            pages.append(json.load(open(os.path.join(OFF, fn), encoding="utf-8")))

    rows = []
    for q in pages:
        got = page_ctx(q)
        if not got:
            continue
        thin, mn, wmed, hm, bt = got
        xlo = min(b["x"] for b in mn)
        xhi = max(b["x"] + b["w"] for b in mn)
        for a, t in thin:
            if has_partner(a, thin, wmed):
                continue
            # 与最近主栏列的横向间隙
            gaps = []
            for m in mn:
                if ov(a["x"], a["x"] + a["w"], m["x"], m["x"] + m["w"]) > 0:
                    gaps.append(0.0)
                else:
                    gaps.append(min(abs(a["x"] - (m["x"] + m["w"])),
                                    abs(m["x"] - (a["x"] + a["w"]))))
            g = min(gaps) if gaps else 9999
            rows.append({
                "page": q["page"], "x": a["x"], "y": a["y"],
                "w": a["w"], "h": a["h"],
                "h_rel": round(a["h"] / float(hm), 3),
                "x_right": a["x"] + a["w"],
                "xhi": xhi, "xlo": xlo,
                "M1_right_out": (a["x"] + a["w"]) > xhi,
                "M2_left_out": a["x"] < xlo,
                "M3_gap_rel": round(g / float(wmed), 2) if g < 9999 else 99.0,
                "text": t,
            })

    print("== 未配对窄框 %d 个的几何位置 ==" % len(rows))
    print("%-5s %7s %6s %9s %9s %8s %s"
          % ("page", "h_rel", "w_rel", "M1右外", "M2左外", "M3缝宽", "text"))
    for r in sorted(rows, key=lambda t: -t["h_rel"]):
        print("%-5s %7.2f %6.2f %9d %9d %8.2f %r"
              % (r["page"], r["h_rel"], r["w"] / 30.0,
                 r["M1_right_out"], r["M2_left_out"], r["M3_gap_rel"],
                 r["text"][:44]))

    print("\n== 汇总 ==")
    tall = [r for r in rows if r["h_rel"] >= 0.5]
    short = [r for r in rows if r["h_rel"] < 0.5]
    for name, sel in (("全高(h_rel>=0.5)", tall), ("矮(h_rel<0.5)", short)):
        print("  %s n=%d: M1右外 %d, M2左外 %d, 贴栏(缝<0.3) %d, 缝>=0.3 %d"
              % (name, len(sel),
                 sum(1 for r in sel if r["M1_right_out"]),
                 sum(1 for r in sel if r["M2_left_out"]),
                 sum(1 for r in sel if r["M3_gap_rel"] < 0.3),
                 sum(1 for r in sel if r["M3_gap_rel"] >= 0.3)))

    print("\n== 分离度检验：若用「M1 或 M2 = 页边」作判据 ==")
    edge = [r for r in rows if r["M1_right_out"] or r["M2_left_out"]]
    print("  命中 %d / %d" % (len(edge), len(rows)))
    print("  其中全高（疑似割注，误伤）: %d"
          % sum(1 for r in edge if r["h_rel"] >= 0.5))
    print("  → 若全高算误伤，误伤率 %.0f%%"
          % (100.0 * sum(1 for r in edge if r["h_rel"] >= 0.5)
             / max(1, len(edge))))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n": len(rows), "rows": rows}, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night48_margin_test.json")


if __name__ == "__main__":
    main()
