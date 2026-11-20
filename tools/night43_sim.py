# -*- coding: utf-8 -*-
"""night43_sim.py — 用 night43_boxes.json（47 页检测-only 框）仿真 NIGHT43 版面过滤。

先剔除 junk3=true（与引擎实现顺序一致：Night3 junk filter 之后跑版面过滤），
再跑 backend/ocr_layout.judge_layout。输出逐页影响面 + 异常页清单。
**不识别、不用文本**——纯框几何仿真。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import judge_layout  # noqa: E402

with open(os.path.join(ROOT, "eval", "night43_boxes.json"), encoding="utf-8") as f:
    d = json.load(f)

total_raw = total_junk3 = total_layout = 0
odd_pages = []
for p in d["pages"]:
    raw = p["lines"]
    kept3 = [dict(b, vert=b["h"] >= b["w"]) for b in raw if not b["junk3"]]
    miban, judged = judge_layout(kept3, p["img_w"], p["img_h"])
    n_footer = sum(1 for _, r in judged if r == "footer_band")
    n_strip = sum(1 for _, r in judged if r == "intruded_strip")
    n_none = sum(1 for _, r in judged if r is None)
    total_raw += len(raw)
    total_junk3 += len(raw) - len(kept3)
    total_layout += n_footer + n_strip
    flag = ""
    # 异常关注：滤框占比过高、或主栏带没估出来但仍有框的页
    if not miban and kept3:
        flag = " NO-MIBAN"
    elif (n_footer + n_strip) > max(3, 0.45 * len(judged)):
        flag = " AGGRESSIVE"
    if flag:
        odd_pages.append((p["page"], len(raw), len(kept3), n_footer, n_strip, flag))
    print("%s raw=%2d junk3=%d kept=%2d footer=%d strip=%d%s"
          % (p["page"], len(raw), len(raw) - len(kept3), len(kept3), n_footer, n_strip, flag))
print("TOTAL raw=%d junk3=%d layout_filtered=%d" % (total_raw, total_junk3, total_layout))
if odd_pages:
    print("odd pages:")
    for o in odd_pages:
        print("  %s" % (o,))
