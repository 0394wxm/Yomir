# -*- coding: utf-8 -*-
"""night48_unpaired.py — 71 个「窄框且无配对」的框逐个列出（人工读）。

night48_thin_verdict 发现：窄框（w<0.6×主栏宽）1118 个里 1047 (94%) 能配成对，
是双行割注（一列排两行注），属正文必须保留。剩 71 个未配对 —— 这些才是
「窄框=噪音」判据的真正候选集。

关键：本判据与 Night47 路线 A 的区别在于用的是**宽**不是**高**。
Night47 用 h_rel<0.3 会误删 1064 个正文短行（列末 2-3 字）；本判据只看宽，
列末短行是全宽的（w_rel≈1.0），不在候选集里。但必须实测确认这一点。

本脚本：
  1) 列出 71 个未配对框（页/几何/文本），供人读分类
  2) 交叉检查 GT 8 页：候选集里有几个落在 GT 正文行上（= 误伤）
  3) 检查候选集的 w_rel 分布，看是否有全宽框混进来

只测量，不改代码。
产出: eval/night48_unpaired.json
用法: python -X utf8 tools/night48_unpaired.py
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
OUT = os.path.join(ROOT, "eval", "night48_unpaired.json")
GT = os.path.join(ROOT, "eval", "night36_ocr_lines.json")


def ov(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def is_kana(c):
    return ("\u3041" <= c <= "\u309f") or ("\u30a1" <= c <= "\u30ff")


def is_kanji(c):
    return ("\u4e00" <= c <= "\u9fff") or ("\u3400" <= c <= "\u4dbf")


def kana_ratio(s):
    k = sum(1 for c in s if is_kana(c))
    h = sum(1 for c in s if is_kanji(c))
    return k / float(k + h) if (k + h) else 0.0


def page_thin_boxes(q):
    """返回 (thin, wmed, hm, body_top, xlo, xhi, ki, bx) —— thin 为 [(box,text)]。"""
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
    return thin, wmed, hm, bt, skk


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

    unpaired = []
    for q in pages:
        got = page_thin_boxes(q)
        if not got:
            continue
        thin, wmed, hm, bt, _skk = got
        for a, t in thin:
            if has_partner(a, thin, wmed):
                continue
            unpaired.append({
                "page": q["page"], "x": a["x"], "y": a["y"],
                "w": a["w"], "h": a["h"],
                "w_rel_main": round(a["w"] / float(wmed), 3),
                "h_rel": round(a["h"] / float(hm), 3),
                "body_top": round(bt, 1),
                "above_body_top": a["y"] + a["h"] / 2.0 < bt,
                "kana": round(kana_ratio(t), 3),
                "n_chars": len(t),
                "text": t,
            })

    print("== 未配对窄框：%d 个 / %d 页 =="
          % (len(unpaired), len({u["page"] for u in unpaired})))
    print("\n%-5s %5s %5s %4s %4s %7s %7s %6s %5s %s"
          % ("page", "x", "y", "w", "h", "w_relM", "h_rel", "kana",
             "above", "text"))
    for u in sorted(unpaired, key=lambda r: (r["page"], r["y"])):
        print("%-5s %5d %5d %4d %4d %7.2f %7.2f %6.2f %5d %r"
              % (u["page"], u["x"], u["y"], u["w"], u["h"],
                 u["w_rel_main"], u["h_rel"], u["kana"],
                 u["above_body_top"], u["text"][:48]))

    print("\n== w_rel 分布（确认没有全宽框混进来）==")
    ws = sorted(u["w_rel_main"] for u in unpaired)
    print("  min=%.2f p25=%.2f 中位=%.2f p75=%.2f max=%.2f"
          % (ws[0], ws[len(ws) // 4], ws[len(ws) // 2],
             ws[3 * len(ws) // 4], ws[-1]))
    print("  w_rel >= 0.6 的（不该有）: %d"
          % sum(1 for u in unpaired if u["w_rel_main"] >= 0.6))

    print("\n== 与 GT 8 页正文行的重叠 ==")
    gt = json.load(open(GT, encoding="utf-8"))["results"]
    gt_texts = {ln["text"] for r in gt for ln in r["lines"]}
    hit = [u for u in unpaired if u["text"] in gt_texts]
    print("文本与 GT 正文行完全相同的: %d" % len(hit))
    for u in hit:
        print("  %s  %r" % (u["page"], u["text"]))
    print("GT 覆盖页里出现在候选集的框数: %d"
          % sum(1 for u in unpaired
                if u["page"] in {r["page"] for r in gt}))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n": len(unpaired), "n_gt_overlap": len(hit),
                   "unpaired": unpaired}, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night48_unpaired.json")


if __name__ == "__main__":
    main()
