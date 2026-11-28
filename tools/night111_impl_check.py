# -*- coding: utf-8 -*-
"""night111_impl_check.py — N111 実装関数 vs sim 逐位一致検証(15 行・temp)。
用法: python -I tools/night111_impl_check.py
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def lev(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def norm(s):
    return re.sub(r"\s+", "", s or "")


from backend.kundoku_rules import style_guard_followup  # noqa: E402

EV = os.path.join(ROOT, "eval")
doc = json.load(open(os.path.join(EV, "night107_results_8165.json"), encoding="utf-8"))
rows = {r["id"]: r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None}
sim = json.load(open(os.path.join(EV, "night111_sim.json"), encoding="utf-8"))
prf = sim["per_row_follow"]
out, ok = [], True
for rid, (d0, d1e) in prf.items():
    r = rows[rid]
    hb = norm(r["hakubun"] or "")
    got = norm(r["udkundoku_kakikudashi"])
    exp = norm(r["expected_kakikudashi"])
    new = style_guard_followup(got, hb)
    d1 = lev(new, exp)
    out.append("%s d_raw=%d d1=%d expect=%d %s" % (rid, d0, d1, d1e, "OK" if d1 == d1e else "MISMATCH"))
    if d1 != d1e:
        ok = False
out.append("ALL %s" % ("MATCH" if ok else "FAIL"))
open(os.path.join(EV, "night111_impl_vs_sim.txt"), "w", encoding="utf-8",
     newline="\n").write("\n".join(out) + "\n")
print("written ok=%s" % ok)
