# -*- coding: utf-8 -*-
"""night25_debug_align.py — 调试对齐失败原因。"""
import difflib
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(s):
    return re.sub(r"\s+", "", s)


with open(os.path.join(ROOT, "eval", "night22_results_full.json"), encoding="utf-8") as f:
    rows = json.load(f)["results"]

shown = 0
for r in rows:
    got = norm(r.get("udkundoku_kakikudashi") or "")
    exp = norm(r["expected_kakikudashi"])
    sm = difflib.SequenceMatcher(a=got, b=exp)
    ops = sm.get_opcodes()
    for m in re.finditer("而して", got):
        i1, i2 = m.start(), m.end()
        hit = None
        for op, a1, a2, b1, b2 in ops:
            if a1 <= i1 and i2 <= a2:
                hit = (op, a1, a2, b1, b2)
                break
        if hit is None and shown < 3:
            shown += 1
            print("FAIL %s i1=%d i2=%d len(got)=%d" % (r["id"], i1, i2, len(got)))
            for op, a1, a2, b1, b2 in ops:
                mark = ""
                if a1 <= i1 <= a2 or a1 <= i2 <= a2:
                    mark = "   <<< touches match"
                print("   %-7s a[%d:%d] b[%d:%d] got=%r%s"
                      % (op, a1, a2, b1, b2, got[a1:min(a2, a1 + 24)], mark))
print("total fails shown:", shown)
