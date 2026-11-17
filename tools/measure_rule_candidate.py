# -*- coding: utf-8 -*-
"""measure_rule_candidate.py — 在 full_v2 结果上测量候选规则的命中数与方向一致性。
统计 got 中含「て而して」的条目数，及这些位置 expected 是否含有 而して/而。用法:
    python -X utf8 tools/measure_rule_candidate.py eval/night4_results_full_v2.json
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    path = sys.argv[1] if os.path.isabs(sys.argv[1]) else os.path.join(ROOT, sys.argv[1])
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    hit = helps = hurts = neutral = 0
    for r in d["results"]:
        got = r.get("udkundoku_kakikudashi_norm", "")
        exp = re.sub(r"\s+", "", r["expected_kakikudashi"])
        if "て而して" not in got:
            continue
        hit += 1
        # 期望侧同一片段是否还有而して/而
        gpos = got.find("て而して")
        ctx_g = got[gpos:gpos + 12]
        has_re_exp = "而" in exp[max(0, exp.find(ctx_g[1:4]) - 4):exp.find(ctx_g[1:4]) + 20] if ctx_g[1:4] in exp else "而" in exp
        if has_re_exp:
            neutral += 1
        else:
            helps += 1
        print("%-16s got[%s] exp_has_while=%s" % (r["id"], ctx_g, has_re_exp))
    print("hit=%d, expected无而(规则可能有帮助)=%d, expected有而(不动为妙)=%d" % (hit, helps, neutral))


if __name__ == "__main__":
    main()
