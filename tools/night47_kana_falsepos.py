# -*- coding: utf-8 -*-
"""night47_kana_falsepos.py — 假名比率判据的误伤风险（真正文含返り点假名）。

night47_residual 报「阈值 0.10-0.30 时 GT 正文行误伤 = 0」。但 GT 只有 8 页
124 行，**不是全本**。本脚本在 47 页全本里找「真正文但假名比率高」的框：

判据（三选一即算真正文嫌疑）：
  F1 框在主栏集合里（is_main）且假名比率 > 0.15
  F2 框文本含返り点假名（レ / 一 / 二 / 上 / 下）→ 訓読注記，不是噪音
  F3 框文本含「。」且以汉字为主，但夹少量假名（如「如丘者焉不レ如レ如クリ…」）

这些框如果被文本判据删掉，就是误伤。逐个列出以便人读判断。

只测量，不改代码。
产出: eval/night47_kana_falsepos.json
用法: python -X utf8 tools/night47_kana_falsepos.py
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
OUT = os.path.join(ROOT, "eval", "night47_kana_falsepos.json")

# 返り点・送り仮名の記号（訓読注記の証拠）
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
            with open(os.path.join(OFF, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    rows = []
    n_hi = 0
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
        main_k = {(b["x"], b["y"], b["w"], b["h"]) for b in main}
        for i in kept_i:
            b = boxes[i]
            if (b["x"], b["y"], b["w"], b["h"]) in sk:
                continue
            t = p["lines"][i]
            r = kana_ratio(t)
            if r <= 0.15:
                continue
            n_hi += 1
            has_kaeri = any(c in KAERI for c in t)
            rows.append({
                "page": p["page"], "x": b["x"], "y": b["y"],
                "w": b["w"], "h": b["h"], "kana": round(r, 3),
                "is_main": (b["x"], b["y"], b["w"], b["h"]) in main_k,
                "has_kaeri_mark": has_kaeri,
                "text": t,
            })

    print("== 假名比率 > 0.15 的保留框：%d 个 ==" % n_hi)
    print("\n== F1 在主栏集合里的（真正文嫌疑最高）==")
    f1 = [r for r in rows if r["is_main"]]
    print("%d 个:" % len(f1))
    for r in f1:
        print("  %s r=%.2f  %r" % (r["page"], r["kana"], r["text"]))

    print("\n== F2 含返り点/送り仮名记号的 ==")
    f2 = [r for r in rows if r["has_kaeri_mark"]]
    print("%d 个:" % len(f2))
    for r in f2:
        print("  %s r=%.2f main=%d  %r"
              % (r["page"], r["kana"], r["is_main"], r["text"][:56]))

    print("\n== 结论 ==")
    print("若用「假名比率 > 0.15」作判据，会删 %d 框，其中：" % n_hi)
    print("  * 在主栏集合里的（可能是真正文）: %d" % len(f1))
    print("  * 含返り点记号的（訓読注記，不是噪音）: %d" % len(f2))
    print("  → 误伤上界 = %d / %d = %.0f%%"
          % (len(f1), n_hi, 100.0 * len(f1) / max(1, n_hi)))
    print("  （f1 与 f2 可能重叠，误伤上界取 f1）")

    print("\n== 但 GT 8 页里误伤 = 0 ==")
    gt = json.load(open(os.path.join(ROOT, "eval", "night36_ocr_lines.json"),
                        encoding="utf-8"))["results"]
    gt_texts = {ln["text"] for r in gt for ln in r["lines"]}
    hit = [r for r in rows if r["text"] in gt_texts]
    print("与 GT 正文行文本相同的: %d" % len(hit))
    print("→ GT 只覆盖 8 页，不能代表 47 页；本判据**不应**据 GT 零误伤就上线。")

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n_high": n_hi, "n_main": len(f1),
                   "n_kaeri": len(f2), "n_gt_overlap": len(hit),
                   "rows": rows}, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night47_kana_falsepos.json")


if __name__ == "__main__":
    main()
