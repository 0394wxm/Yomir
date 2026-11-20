# -*- coding: utf-8 -*-
"""night47_kana_ratio.py — 假名比率作为「白文 vs 噪音」的客观分离信号。

**动机**：Night43/46 的版面过滤全部是**纯几何**（框位置），刻意不看文本。
但滤完之后剩下的 1770 个框里还有多少噪音，从没人量过。

**观察**（p012/p017 的框文本）：这个江户版《論語》的**白文正文是纯汉字**
（「孟孫問孝於我我封曰無違。焚遅曰何謂也。」），而手写批注/公文条是
**假名与汉字混排的日语**（「令之者者、消る所有之広町従将持人…」）。
→ 假名比率是一个不需要任何词典、不需要外部语料的客观分离信号。

本脚本：
  K1 47 页所有框的假名比率分布（看是否双峰）
  K2 被 Night43/46 滤掉的框 vs 保留框的假名比率对比（验证信号有效性）
  K3 保留框里假名比率高的（> 0.15）逐条列出——这些是**几何漏掉的残留噪音**
  K4 用 GT 8 页的正文行做参照，给出正文的假名比率上界

只测量，不改代码（是否据此加文本判据 = 产品拍板项）。
产出: eval/night47_kana_ratio.json
用法: python -X utf8 tools/night47_kana_ratio.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night47_kana_ratio.json")


def is_kana(c):
    return ("\u3041" <= c <= "\u309f") or ("\u30a1" <= c <= "\u30ff")


def is_kanji(c):
    return ("\u4e00" <= c <= "\u9fff") or ("\u3400" <= c <= "\u4dbf")


def kana_ratio(s):
    """假名 / (假名 + 汉字)；标点与符号不计。"""
    k = sum(1 for c in s if is_kana(c))
    h = sum(1 for c in s if is_kanji(c))
    return k / float(k + h) if (k + h) else 0.0


def hist(vals, bins):
    out = {}
    for v in vals:
        for lo, hi in bins:
            if lo <= v < hi:
                out["%.2f-%.2f" % (lo, hi)] = out.get("%.2f-%.2f" % (lo, hi), 0) + 1
                break
        else:
            out[">=%.2f" % bins[-1][1]] = out.get(">=%.2f" % bins[-1][1], 0) + 1
    return out


BINS = [(0.0, 0.01), (0.01, 0.05), (0.05, 0.10), (0.10, 0.15),
        (0.15, 0.25), (0.25, 0.40), (0.40, 0.60), (0.60, 1.01)]


def main():
    pages = []
    for fn in sorted(os.listdir(FULL)):
        if fn.endswith(".json"):
            with open(os.path.join(FULL, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    keep_vals = []
    rows = []
    for p in pages:
        boxes = p["line_boxes"]
        texts = p["lines"]
        if len(boxes) < 4:
            continue
        for b, t in zip(boxes, texts):
            keep_vals.append(kana_ratio(t))
        high = []
        for b, t in zip(boxes, texts):
            r = kana_ratio(t)
            if r > 0.15:
                high.append({"x": b["x"], "y": b["y"], "w": b["w"], "h": b["h"],
                             "kana_ratio": round(r, 3), "text": t})
        rows.append({"page": p["page"], "n": len(boxes),
                     "n_high_kana": len(high), "high": high})

    print("== K1 保留框（filter_on，1770 框）的假名比率分布 ==")
    h = hist(keep_vals, BINS)
    tot = len(keep_vals)
    for k in ["%.2f-%.2f" % b for b in BINS]:
        n = h.get(k, 0)
        print("  %-12s %4d  %5.1f%%" % (k, n, 100.0 * n / max(1, tot)))
    print("  合计 %d 框" % tot)

    print("\n== K2 与 GT 正文行对照（正文的假名比率上界）==")
    gt = json.load(open(os.path.join(ROOT, "eval", "night36_ocr_lines.json"),
                        encoding="utf-8"))["results"]
    gt_vals = []
    for r in gt:
        for ln in r["lines"]:
            gt_vals.append(kana_ratio(ln["text"]))
    gt_vals.sort()
    if gt_vals:
        print("  GT %d 行: 中位 %.3f  90%% 分位 %.3f  最大 %.3f"
              % (len(gt_vals), gt_vals[len(gt_vals) // 2],
                 gt_vals[int(0.9 * (len(gt_vals) - 1))], gt_vals[-1]))
    # 正文参照：GT 里假名比率 < 0.05 的行
    clean = [v for v in gt_vals if v < 0.05]
    print("  GT 里假名比率 <0.05 的行: %d / %d（%.0f%%）"
          % (len(clean), len(gt_vals), 100.0 * len(clean) / max(1, len(gt_vals))))

    print("\n== K3 保留框里假名比率 > 0.15 的（几何漏掉的残留噪音候选）==")
    tot_high = sum(r["n_high_kana"] for r in rows)
    print("合计 %d 框 / %d（%.1f%%），分布在 %d 页"
          % (tot_high, tot, 100.0 * tot_high / max(1, tot),
             sum(1 for r in rows if r["n_high_kana"])))
    for r in rows:
        if r["n_high_kana"]:
            print("\n--- %s  %d / %d 框 ---"
                  % (r["page"], r["n_high_kana"], r["n"]))
            for b in r["high"]:
                print("   r=%.2f x=%4d y=%3d w=%3d h=%3d  %r"
                      % (b["kana_ratio"], b["x"], b["y"], b["w"], b["h"],
                         b["text"][:58]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"bins": BINS, "n_keep": tot, "histogram": h,
                   "gt_kana": {"n": len(gt_vals),
                               "median": gt_vals[len(gt_vals) // 2] if gt_vals else None,
                               "max": gt_vals[-1] if gt_vals else None},
                   "n_high_kana": tot_high, "pages": rows},
                  f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night47_kana_ratio.json")


if __name__ == "__main__":
    main()
