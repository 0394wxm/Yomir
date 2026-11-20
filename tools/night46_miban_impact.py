# -*- coding: utf-8 -*-
"""night46_miban_impact.py — miban.y 污染的影响面（NIGHT46 立项依据）。

**发现**：47 页里 **p012（y=38）、p017（y=36）** 的 `_main_group` 版心上缘
被抬进了上部头注带；其余 41 页 miban.y 都在 204–252。原因：这两页有
w=33–41、h=523–694 的**手写长条**，宽度刚过 `w ≥ 0.65×P90(w)`（33.1），
高度又过 `0.6×hmax`（416–473），于是被算作主栏。

`miban.y` 有两个消费者，本脚本量化污染程度：

  U1 `judge_layout` 的页脚带判据用 `y_max = max(y+h of main)`，**不用 miban.y**
      → 页脚过滤不受影响（p012/p017 的 y_max 与其他页同量级，798–823）。
  U2 `_main_group` 的**框集合**（main vs 非 main）→ 影响 `main_column_keys`
      （Night45 重排）与任何「主栏/头注」二分。p012/p017 的窄长条被误纳为
      主栏 → Night45 的 I5 把 p017 计为 1 处颠倒。

**Night46 的结论**：这个污染对产品流**零影响**（miban 被丢弃、页脚判据用
y_max、行序零变化）。真正可利用的是：改用 `body_top = median(主栏 y)` 后，
这批长条可由 `judge_headnote_strip` 纯几何分离 → 见 REPORT_NIGHT46.md。

产出: eval/night46_miban_impact.json
用法: python -X utf8 tools/night46_miban_impact.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import (  # noqa: E402
    MAIN_H_FRAC, MAIN_W_FRAC, _main_group, _median, _p90,
)

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night46_miban_impact.json")

# 「版心上缘应在此之上」的经验下界：主栏列 y 中位数 − 该偏移
TOP_OFFSET = 30


def main():
    pages = []
    for fn in sorted(os.listdir(FULL)):
        if fn.endswith(".json"):
            with open(os.path.join(FULL, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    rows = []
    suspect = []
    for p in pages:
        boxes = p["line_boxes"]
        if len(boxes) < 4:
            continue
        vert = [b for b in boxes if b["h"] >= b["w"]]
        if not vert:
            continue
        hmax = max(b["h"] for b in vert)
        w90 = _p90([b["w"] for b in vert])
        miban, main = _main_group([dict(b) for b in boxes])
        if miban is None:
            rows.append({"page": p["page"], "miban_y": None})
            continue
        med_y = _median([b["y"] for b in main])
        outliers = [b for b in main if b["y"] < med_y - TOP_OFFSET]
        y_max = max(b["y"] + b["h"] for b in main)
        rows.append({"page": p["page"], "n": len(boxes), "main": len(main),
                     "miban_y": miban["y"], "main_med_y": round(med_y),
                     "main_y_max": y_max, "top_outliers": len(outliers),
                     "hmax": hmax, "p90w": round(w90),
                     "h_gate": round(MAIN_H_FRAC * hmax),
                     "w_gate": round(MAIN_W_FRAC * w90, 1)})
        for b in outliers:
            i = next(i for i, x in enumerate(boxes)
                     if (x["x"], x["y"], x["w"], x["h"])
                     == (b["x"], b["y"], b["w"], b["h"]))
            suspect.append({"page": p["page"], "x": b["x"], "y": b["y"],
                            "w": b["w"], "h": b["h"],
                            "text": p["lines"][i][:50]})

    print("== 版心上缘（miban.y）与主栏 y 中位数 ==")
    print("page  n   main  miban.y  medY  y_max  outliers  hmax  h门槛  P90w  w门槛")
    for r in rows:
        if r.get("miban_y") is None:
            print("%s  (版心估不出)" % r["page"])
            continue
        flag = "  <<<" if r["miban_y"] < r["main_med_y"] - TOP_OFFSET else ""
        print("%s %3d %5d   %5d  %5d %6d   %3d   %5d  %5d  %4d  %5.1f%s"
              % (r["page"], r["n"], r["main"], r["miban_y"], r["main_med_y"],
                 r["main_y_max"], r["top_outliers"], r["hmax"], r["h_gate"],
                 r["p90w"], r["w_gate"], flag))

    bad = [r["page"] for r in rows
           if r.get("miban_y") is not None
           and r["miban_y"] < r["main_med_y"] - TOP_OFFSET]
    print("\n== 结论 ==")
    print("miban.y 明显高于主栏 y 中位数的页（> %dpx）: %s"
          % (TOP_OFFSET, bad or "无"))
    print("这些页的主栏框里 y 偏高的框（手写长条）:")
    for s in suspect:
        print("  %s x=%4d y=%3d w=%3d h=%3d  %r"
              % (s["page"], s["x"], s["y"], s["w"], s["h"], s["text"]))
    print("\n页脚判据用的是 y_max（不是 miban.y）→ 全本 798-823，不受污染。")

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"top_offset": TOP_OFFSET, "suspect_pages": bad,
                   "suspect_boxes": suspect, "pages": rows},
                  f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night46_miban_impact.json")


if __name__ == "__main__":
    main()
