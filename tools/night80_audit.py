# -*- coding: utf-8 -*-
"""night80_audit.py — N80: 判定ファイルの完全性チェック（全 503...500 候選 vs decisions）。"""
import glob
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

cands = json.load(io.open(os.path.join(EV, "night80_candidates.json"), encoding="utf-8"))["candidates"]
cand_words = [c["word"] for c in cands]

seen = {}
dup = []
for p in sorted(glob.glob(os.path.join(EV, "night80_decisions_*.json"))):
    for d in json.load(io.open(p, encoding="utf-8"))["decisions"]:
        w = d["word"]
        if w in seen:
            dup.append((w, seen[w], os.path.basename(p)))
        seen[w] = os.path.basename(p)

inc = [w for w, p in seen.items() if p]
missing = [c for c in cand_words if c not in seen]
out = []
out.append("candidates=%d decided=%d dup=%d missing=%d" % (len(cand_words), len(seen), len(dup), len(missing)))
if dup:
    out.append("DUP: " + ", ".join("%s(%s/%s)" % t for t in dup[:10]))
if missing:
    out.append("MISSING (%d): %s" % (len(missing), ", ".join(missing[:60])))
io.open(os.path.join(EV, "night80_audit.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print(out[0])
