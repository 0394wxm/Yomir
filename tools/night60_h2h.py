# -*- coding: utf-8 -*-
"""night60_h2h.py — N60：新增 1000 条上 规则引擎 vs guwenbert 逐条对决。

规则 = night60_results_4000.json[3000:]；guwenbert = night60_guwenbert_new1000.json。
输出 eval/night60_h2h.txt。
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

rules = {r["id"]: r for r in json.load(io.open(os.path.join(EV, "night60_results_4000.json"),
                                               encoding="utf-8"))["results"][3000:]}
gwb = {r["id"]: r for r in json.load(io.open(os.path.join(EV, "night60_guwenbert_new1000.json"),
                                             encoding="utf-8"))["results"]}

ids = [x["id"] for x in json.load(io.open(os.path.join(EV, "golden_4000.json"),
                                          encoding="utf-8"))[3000:]]
lines = []
out = lambda s="": (lines.append(s), print(s, flush=True))

common = [i for i in ids if i in rules and i in gwb
          and rules[i].get("edit_distance") is not None
          and gwb[i].get("edit_distance") is not None]
rules_err = [i for i in ids if i in rules and rules[i].get("edit_distance") is None]
gwb_err = [i for i in ids if i in gwb and gwb[i].get("edit_distance") is None]
out("新增段 %d 条 | 双方可比 %d | 规则 error %d %s | guwenbert error %d %s"
    % (len(ids), len(common), len(rules_err), rules_err, len(gwb_err), gwb_err))

rb = sum(rules[i]["edit_distance"] for i in common)
gb = sum(gwb[i]["edit_distance"] for i in common)
out("规则     avgDist %.3f | 精确 %d" % (rb / len(common),
                                        sum(1 for i in common if rules[i]["exact_match"])))
out("guwenbert avgDist %.3f | 精确 %d" % (gb / len(common),
                                          sum(1 for i in common if gwb[i]["exact_match"])))
better = sum(1 for i in common if rules[i]["edit_distance"] < gwb[i]["edit_distance"])
worse = sum(1 for i in common if rules[i]["edit_distance"] > gwb[i]["edit_distance"])
same = len(common) - better - worse
out("逐条对决：规则更好 %d | guwenbert 更好 %d | 持平 %d" % (better, worse, same))

# 差距最大的 5 条（供报告引用）
big = sorted(common, key=lambda i: gwb[i]["edit_distance"] - rules[i]["edit_distance"],
             reverse=True)[:5]
out("\n规则相对优势 top5：")
for i in big:
    out("  %s 规则 %d vs gwb %d | %s" % (i, rules[i]["edit_distance"],
                                         gwb[i]["edit_distance"], rules[i]["hakubun"][:30]))
big2 = sorted(common, key=lambda i: rules[i]["edit_distance"] - gwb[i]["edit_distance"],
              reverse=True)[:5]
out("\nguwenbert 相对优势 top5：")
for i in big2:
    out("  %s 规则 %d vs gwb %d | %s" % (i, rules[i]["edit_distance"],
                                         gwb[i]["edit_distance"], rules[i]["hakubun"][:30]))

io.open(os.path.join(EV, "night60_h2h.txt"), "w", encoding="utf-8",
        newline="\n").write("\n".join(lines) + "\n")
out("\nwritten: eval/night60_h2h.txt")
