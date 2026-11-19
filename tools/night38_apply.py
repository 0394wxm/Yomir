# -*- coding: utf-8 -*-
"""night38_apply.py — 把 ocr_postfix.fix_kanji_confusions 应用到 night36 OCR 行，
产出 eval/night36_ocr_lines_fixed.json 供 eval_ocr_gt.py 对比（NIGHT38）。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_postfix import fix_kanji_confusions  # noqa: E402

SRC = os.path.join(ROOT, "eval", "night36_ocr_lines.json")
DST = os.path.join(ROOT, "eval", "night36_ocr_lines_fixed.json")

with open(SRC, encoding="utf-8") as f:
    data = json.load(f)
n_changed = 0
for res in data["results"]:
    for l in res["lines"]:
        fixed = fix_kanji_confusions(l["text"])
        if fixed != l["text"]:
            n_changed += 1
        l["text"] = fixed
with open(DST, "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("[done] lines changed: %d -> %s" % (n_changed, DST))
