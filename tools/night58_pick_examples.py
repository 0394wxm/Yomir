# -*- coding: utf-8 -*-
"""night58_pick_examples.py — 从组合改写行里挑每条规则的真实例句（测试/报告用）。"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

rows = json.load(io.open(os.path.join(EV, "night58_combo_changed_rows_kana_zero_shinjitai.json"),
                         encoding="utf-8"))
out = io.open(os.path.join(EV, "night58_examples.txt"), "w", encoding="utf-8", newline="\n")
for tag, pat, lim in (("mata", "復た", 4), ("sore", "只だ", 3), ("bekarazu", "須いず", 3),
                      ("shin", None, 6)):
    picked = 0
    for r in rows:
        old, new = r["old_text"], r["new_text"]
        if tag == "shin":
            if new == old or picked >= lim:
                continue
            changed = [(a, b) for a, b in zip(old, new) if a != b]
            if not changed:
                continue
            out.write("SHIN %s %s\n  got: %s\n  new: %s\n  exp: %s\n" % (
                r["id"], " ".join("%s→%s" % p for p in changed[:6]), old, new, r["expected"]))
            picked += 1
        else:
            if pat not in new or pat in old or picked >= lim:
                continue
            out.write("%s %s\n  got: %s\n  new: %s\n  exp: %s\n" % (
                tag, r["id"], old, new, r["expected"]))
            picked += 1
out.close()
print("written eval/night58_examples.txt", flush=True)
