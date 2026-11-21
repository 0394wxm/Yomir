# -*- coding: utf-8 -*-
"""night62_h2h.py — N62：新增段 规则 vs guwenbert 逐条对决（night60_h2h 同款口径）。

用法：python tools/night62_h2h.py [--rules night62_results_7430.json]
                                  [--gwb night62_guwenbert_new3430.json]
输出控制台表 + eval/night62_h2h.txt。
"""
import argparse
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default=None)
    ap.add_argument("--gwb", default=None)
    arg = ap.parse_args()

    def pick(prefix):
        cands = [f for f in os.listdir(EV) if f.startswith(prefix) and f.endswith(".json")]
        return max(cands) if cands else None

    rules_fn = arg.rules or pick("night62_results_")
    gwb_fn = arg.gwb or pick("night62_guwenbert_new")
    rdoc = json.load(open(os.path.join(EV, rules_fn), encoding="utf-8"))
    gdoc = json.load(open(os.path.join(EV, gwb_fn), encoding="utf-8"))
    rmap = {r["id"]: r for r in rdoc["results"]}
    gmap = {r["id"]: r for r in gdoc["results"]}

    new_ids = [x["id"] for x in json.load(open(os.path.join(EV, rdoc["golden"]),
                                               encoding="utf-8"))[4000:]]
    both = [i for i in new_ids if i in rmap and i in gmap
            and rmap[i].get("edit_distance") is not None
            and gmap[i].get("edit_distance") is not None]
    r_err = [i for i in new_ids if i in rmap and rmap[i].get("edit_distance") is None]
    g_err = [i for i in new_ids if i in gmap and gmap[i].get("edit_distance") is None]

    r_avg = sum(rmap[i]["edit_distance"] for i in both) / len(both)
    g_avg = sum(gmap[i]["edit_distance"] for i in both) / len(both)
    r_exact = sum(1 for i in both if rmap[i]["exact_match"])
    g_exact = sum(1 for i in both if gmap[i]["exact_match"])
    better_r = [i for i in both if rmap[i]["edit_distance"] < gmap[i]["edit_distance"]]
    better_g = [i for i in both if gmap[i]["edit_distance"] < rmap[i]["edit_distance"]]
    tie = len(both) - len(better_r) - len(better_g)

    lines = []
    lines.append("新增段 %d 条 | 双方可比 %d | 规则 error %d %s | guwenbert error %d %s"
                 % (len(new_ids), len(both), len(r_err), r_err[:5], len(g_err), g_err[:5]))
    lines.append("规则     avgDist %.3f | 精确 %d" % (r_avg, r_exact))
    lines.append("guwenbert avgDist %.3f | 精确 %d" % (g_avg, g_exact))
    lines.append("逐条对决：规则更好 %d | guwenbert 更好 %d | 持平 %d"
                 % (len(better_r), len(better_g), tie))

    def top(ids, reverse_key):
        return sorted(ids, key=reverse_key)[:5]

    r_top = top(better_r, lambda i: rmap[i]["edit_distance"] - gmap[i]["edit_distance"])
    g_top = top(better_g, lambda i: gmap[i]["edit_distance"] - rmap[i]["edit_distance"])
    lines.append("\n规则相对优势 top5：")
    for i in r_top:
        lines.append("  %-24s 规则 %2d vs gwb %2d | %s"
                     % (i, rmap[i]["edit_distance"], gmap[i]["edit_distance"],
                        rmap[i]["hakubun"]))
    lines.append("\nguwenbert 相对优势 top5：")
    for i in g_top:
        lines.append("  %-24s 规则 %2d vs gwb %2d | %s"
                     % (i, rmap[i]["edit_distance"], gmap[i]["edit_distance"],
                        rmap[i]["hakubun"]))

    print("\n".join(lines))
    with open(os.path.join(EV, "night62_h2h.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("\nwritten: eval/night62_h2h.txt")


if __name__ == "__main__":
    main()
