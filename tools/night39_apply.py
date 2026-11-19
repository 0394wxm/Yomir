# -*- coding: utf-8 -*-
"""night39_apply.py — 引擎 Night39 后处理（词典+兼容码位+同字串垃圾行过滤）应用到
night36 OCR 行，产出 eval/night36_ocr_lines_n39.json 供 eval_ocr_gt.py 对比（NIGHT39）。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_postfix import is_junk_repeat_line, postprocess_line  # noqa: E402

SRC = os.path.join(ROOT, "eval", "night36_ocr_lines.json")
DST = os.path.join(ROOT, "eval", "night36_ocr_lines_n39.json")

with open(SRC, encoding="utf-8") as f:
    data = json.load(f)
n_changed = n_dropped = 0
for res in data["results"]:
    kept = []
    for l in res["lines"]:
        fixed = postprocess_line(l["text"])
        if fixed != l["text"]:
            n_changed += 1
        if is_junk_repeat_line(fixed):
            n_dropped += 1
            continue
        l["text"] = fixed
        kept.append(l)
    res["lines"] = kept
    res["ocr_n_lines"] = len(kept)
with open(DST, "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("[done] lines changed: %d, junk-repeat dropped: %d -> %s" % (n_changed, n_dropped, DST))
