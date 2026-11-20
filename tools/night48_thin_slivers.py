# -*- coding: utf-8 -*-
"""night48_thin_slivers.py — 正文区内「窄竖条」全本清单（21 框/12 页）。

Night44 记 p044 有两个页脚漏滤框；实测它们中心在主栏底之上 70/40px，
根本不是页脚判据能管的区域。真实形态是：**窄竖条（w≈13-18，主栏宽 54）
纵向嵌在主栏 y 跨度内部**，与正文同列并列。全本 47 页共 21 框 / 12 页。

本脚本把这 21 框全部列出（文本 + 几何 + 同列宽度对比），以便人读判断
它们到底是：手写書き入れ / 蔵書印 / 割注（应保留）/ 检测器重框（应去重）。

判据（与 night48_p044_ctx 一致，仅作定位用，不作上线判据）：
  x 落在主栏 x 区间内 且 h < 0.35*hmax 且 中心 y > 主栏底 - 120

只测量，不改代码。
产出: eval/night48_thin_slivers.json
用法: python -X utf8 tools/night48_thin_slivers.py
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
OUT = os.path.join(ROOT, "eval", "night48_thin_slivers.json")


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
            pages.append(json.load(open(os.path.join(OFF, fn), encoding="utf-8")))

    hits = []
    for q in pages:
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
        wmed = _median([b["w"] for b in mn])
        for i in ki:
            b = bx[i]
            if (b["x"], b["y"], b["w"], b["h"]) in skk:
                continue
            if not (xlo <= b["x"] <= xhi and b["h"] < 0.35 * hm):
                continue
            if b["y"] + b["h"] / 2.0 <= ymax_m - 120:
                continue
            t = q["lines"][i]
            # 同列（x 重叠 ≥0.4）的框
            peers = []
            for j in ki:
                c = bx[j]
                if c is b or (c["x"], c["y"], c["w"], c["h"]) in skk:
                    continue
                if ov_x(b, c) >= 0.4:
                    peers.append(c)
            hits.append({
                "page": q["page"], "x": b["x"], "y": b["y"],
                "w": b["w"], "h": b["h"],
                "w_rel_main": round(b["w"] / float(wmed), 3),
                "h_rel": round(b["h"] / float(hm), 3),
                "x_right": b["x"] + b["w"], "page_xhi": xhi,
                "kana": round(kana_ratio(t), 3),
                "n_peers": len(peers),
                "peer_w": [c["w"] for c in peers],
                "peer_span": ([min(c["y"] for c in peers),
                               max(c["y"] + c["h"] for c in peers)]
                              if peers else None),
                "text": t,
            })

    print("== 正文区内窄竖条：%d 框 / %d 页 =="
          % (len(hits), len({h["page"] for h in hits})))
    print("\n%-5s %5s %5s %4s %4s %7s %7s %6s %5s %s"
          % ("page", "x", "y", "w", "h", "w_relM", "h_rel", "kana", "peer", "text"))
    for h in sorted(hits, key=lambda r: (r["page"], r["y"])):
        print("%-5s %5d %5d %4d %4d %7.2f %7.2f %6.2f %5d %r"
              % (h["page"], h["x"], h["y"], h["w"], h["h"],
                 h["w_rel_main"], h["h_rel"], h["kana"], h["n_peers"],
                 h["text"][:50]))

    print("\n== 宽度分布 ==")
    ws = sorted(h["w"] for h in hits)
    print("  w: min=%d p25=%d 中位=%d p75=%d max=%d"
          % (ws[0], ws[len(ws) // 4], ws[len(ws) // 2],
             ws[3 * len(ws) // 4], ws[-1]))
    wr = sorted(h["w_rel_main"] for h in hits)
    print("  w/主栏宽: min=%.2f p25=%.2f 中位=%.2f p75=%.2f max=%.2f"
          % (wr[0], wr[len(wr) // 4], wr[len(wr) // 2],
             wr[3 * len(wr) // 4], wr[-1]))
    print("  同列有并列框的: %d/%d"
          % (sum(1 for h in hits if h["n_peers"]), len(hits)))
    print("  peer 的 y 跨度包含本框的: %d"
          % sum(1 for h in hits
                if h["peer_span"] and h["peer_span"][0] <= h["y"]
                and h["y"] + h["h"] <= h["peer_span"][1]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n": len(hits), "hits": hits}, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night48_thin_slivers.json")


if __name__ == "__main__":
    main()
