# -*- coding: utf-8 -*-
"""night48_thin_sweep.py — 全本窄框普查（不看 y，只看宽）。

night48_thin_slivers 发现正文区 21 个短框按宽度天然分成两组：
  w/主栏宽 0.24-0.40（11 框，手写書き入れ/割注）vs 0.78-0.92（10 框，真正文）。
中间 0.40-0.78 是空的。但这是「只看 y 在页底附近」的样本 —— Night47 的教训
是 GT 零误伤可能是采样侥幸。所以这里做**全本、不看 y** 的窄框普查：

列出 47 页所有 w < 0.6 × 主栏宽 的保留框（不设 y 条件），逐个人读文本，
判断「窄框 = 噪音」是否在全本成立。

同时给出每个宽度阈值下：删框数、其中真正文嫌疑数（人读后手工标注的类别
由文本启发式预分类，最终仍以打印出的文本为准）。

只测量，不改代码。
产出: eval/night48_thin_sweep.json
用法: python -X utf8 tools/night48_thin_sweep.py
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
OUT = os.path.join(ROOT, "eval", "night48_thin_sweep.json")

# 漢文正文常见虚词/句读：出现即高度疑似真正文
BODY_MARKS = set("。、，．")
# 返り点・送り仮名记号
KAERI = set("レ一二三四上中下甲乙丙丁天地人")


def is_kana(c):
    return ("\u3041" <= c <= "\u309f") or ("\u30a1" <= c <= "\u30ff")


def is_kanji(c):
    return ("\u4e00" <= c <= "\u9fff") or ("\u3400" <= c <= "\u4dbf")


def kana_ratio(s):
    k = sum(1 for c in s if is_kana(c))
    h = sum(1 for c in s if is_kanji(c))
    return k / float(k + h) if (k + h) else 0.0


def main():
    pages = []
    for fn in sorted(os.listdir(OFF)):
        if fn.endswith(".json"):
            pages.append(json.load(open(os.path.join(OFF, fn), encoding="utf-8")))

    rows = []
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
        wmed = _median([b["w"] for b in mn])
        if wmed <= 0:
            continue
        for i in ki:
            b = bx[i]
            if (b["x"], b["y"], b["w"], b["h"]) in skk:
                continue
            wr = b["w"] / float(wmed)
            if wr >= 0.6:
                continue
            t = q["lines"][i]
            rows.append({
                "page": q["page"], "x": b["x"], "y": b["y"],
                "w": b["w"], "h": b["h"], "w_rel_main": round(wr, 3),
                "h_rel": round(b["h"] / float(hm), 3),
                "is_vert": b["h"] >= b["w"],
                "kana": round(kana_ratio(t), 3),
                "has_punct": any(c in BODY_MARKS for c in t),
                "has_kaeri": any(c in KAERI for c in t),
                "n_chars": len(t),
                "text": t,
            })

    print("== 全本 w < 0.6×主栏宽 的保留框：%d 个 / %d 页 =="
          % (len(rows), len({r["page"] for r in rows})))
    print("\n%-5s %5s %5s %4s %4s %7s %7s %5s %4s %3s %s"
          % ("page", "x", "y", "w", "h", "w_relM", "h_rel", "vert",
             "punct", "kana", "text"))
    for r in sorted(rows, key=lambda t: (t["page"], t["y"])):
        print("%-5s %5d %5d %4d %4d %7.2f %7.2f %5d %4d %3.2f %r"
              % (r["page"], r["x"], r["y"], r["w"], r["h"],
                 r["w_rel_main"], r["h_rel"], r["is_vert"],
                 r["has_punct"], r["kana"], r["text"][:48]))

    print("\n== 按宽度阈值累计 ==")
    print("%6s %7s %9s %9s %9s" % ("thr", "删框", "含句读", "含返り点", "含假名"))
    for thr in (0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60):
        sel = [r for r in rows if r["w_rel_main"] < thr]
        print("%6.2f %7d %9d %9d %9d"
              % (thr, len(sel),
                 sum(1 for r in sel if r["has_punct"]),
                 sum(1 for r in sel if r["has_kaeri"]),
                 sum(1 for r in sel if r["kana"] > 0)))

    print("\n== 宽度分布（这些窄框）==")
    ws = sorted(r["w_rel_main"] for r in rows)
    print("  min=%.2f p25=%.2f 中位=%.2f p75=%.2f max=%.2f"
          % (ws[0], ws[len(ws) // 4], ws[len(ws) // 2],
             ws[3 * len(ws) // 4], ws[-1]))
    # 直方图，步长 0.05，看 0.40-0.60 是否真空
    print("\n  直方图（步长 0.05）:")
    for k in range(6, 12):
        lo = k * 0.05
        n = sum(1 for r in rows if lo <= r["w_rel_main"] < lo + 0.05)
        bar = "#" * n
        print("    %.2f-%.2f : %3d %s" % (lo, lo + 0.05, n, bar))

    print("\n== 关键检查：0.40-0.60 区间里有没有真正文 ==")
    mid = [r for r in rows if 0.40 <= r["w_rel_main"] < 0.60]
    print("该区间 %d 框:" % len(mid))
    for r in mid:
        print("  %s w_rel=%.2f h_rel=%.2f punct=%d kana=%.2f  %r"
              % (r["page"], r["w_rel_main"], r["h_rel"], r["has_punct"],
                 r["kana"], r["text"][:56]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n": len(rows), "rows": rows}, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night48_thin_sweep.json")


if __name__ == "__main__":
    main()
