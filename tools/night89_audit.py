# -*- coding: utf-8 -*-
"""night89_audit.py — N89: 判定ファイルの完全性チェック（466 候補 vs decisions）。
（night80_audit.py の night89 版＋include/exclude 集計）"""
import glob
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

cands = json.load(io.open(os.path.join(EV, "night89_candidates.json"), encoding="utf-8"))["candidates"]
cand_words = [c["word"] for c in cands]

seen = {}
dup = []
inc = 0
exc = 0
for p in sorted(glob.glob(os.path.join(EV, "night89_decisions_*.json"))):
    for d in json.load(io.open(p, encoding="utf-8"))["decisions"]:
        w = d["word"]
        if w in seen:
            dup.append((w, seen[w], os.path.basename(p)))
        seen[w] = os.path.basename(p)
        if d.get("verdict") == "include":
            inc += 1
        elif d.get("verdict") == "exclude":
            exc += 1

missing = [c for c in cand_words if c not in seen]
out = []
out.append("candidates=%d decided=%d (include=%d exclude=%d) dup=%d missing=%d"
           % (len(cand_words), len(seen), inc, exc, len(dup), len(missing)))
if dup:
    out.append("DUP: " + ", ".join("%s(%s/%s)" % t for t in dup[:10]))
if missing:
    out.append("MISSING (%d): %s" % (len(missing), ", ".join(missing[:60])))
io.open(os.path.join(EV, "night89_audit.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print(out[0])
if len(missing) or dup:
    print("[INCOMPLETE] " + ("missing=%d " % len(missing) if missing else "") + ("dup=%d" % len(dup) if dup else ""))
else:
    print("[COMPLETE] all candidates decided")
