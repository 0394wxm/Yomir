# -*- coding: utf-8 -*-
"""night71_h2h.py — N71③：规则 vs guwenbert 全量 8165 逐条对决（night62/67_h2h 同款口径）。

对照面：规则引擎最新全量归档（night70_results_8165.json，J/K 全链）vs
guwenbert 全量（night71_guwenbert_8165.json）。输出：规则胜／gwb 胜／持平、
双方 avgDist/exact、分档×文体交叉表、双方相对优势 top10。
输出控制台表 + eval/night71_h2h.txt。

用法：python tools/night71_h2h.py [--rules night70_results_8165.json]
                                  [--gwb night71_guwenbert_8165.json]
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


def bucket_of(hb):
    n = len(norm(hb))
    return "≤20字" if n <= 20 else "21-40字" if n <= 40 else "41-60字" if n <= 60 else ">60字"


def genre_of(url):
    u = (url or "").lower()
    if "/syubu/shikyo" in u:
        return "詩経"
    if "/syubu/" in u:
        return "漢詩"
    if "/keibu/daigaku" in u:
        return "大学"
    if "/keibu/kokyo" in u:
        return "孝経"
    if "/keibu/rongo" in u:
        return "論語"
    if "/koji/" in u:
        return "故事"
    return "その他"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="night70_results_8165.json")
    ap.add_argument("--gwb", default="night71_guwenbert_8165.json")
    arg = ap.parse_args()

    rdoc = json.load(open(os.path.join(EV, arg.rules), encoding="utf-8"))
    gdoc = json.load(open(os.path.join(EV, arg.gwb), encoding="utf-8"))
    rmap = {r["id"]: r for r in rdoc["results"]}
    gmap = {r["id"]: r for r in gdoc["results"]}
    all_ids = [r["id"] for r in rdoc["results"]]

    both = [i for i in all_ids if rmap[i].get("edit_distance") is not None
            and gmap.get(i, {}).get("edit_distance") is not None]
    g_only_missing = [i for i in all_ids if gmap.get(i, {}).get("edit_distance") is None]

    r_avg = sum(rmap[i]["edit_distance"] for i in both) / len(both)
    g_avg = sum(gmap[i]["edit_distance"] for i in both) / len(both)
    r_exact = sum(1 for i in both if rmap[i]["exact_match"])
    g_exact = sum(1 for i in both if gmap[i]["exact_match"])
    better_r = [i for i in both if rmap[i]["edit_distance"] < gmap[i]["edit_distance"]]
    better_g = [i for i in both if gmap[i]["edit_distance"] < rmap[i]["edit_distance"]]
    tie = len(both) - len(better_r) - len(better_g)

    lines = []
    lines.append("全量对照（规则=%s vs guwenbert=%s）" % (arg.rules, arg.gwb))
    lines.append("总条数 %d | 双方可比 %d | guwenbert error %d %s"
                 % (len(all_ids), len(both), len(g_only_missing), g_only_missing[:5]))
    lines.append("规则     avgDist %.3f | 精确 %d" % (r_avg, r_exact))
    lines.append("guwenbert avgDist %.3f | 精确 %d" % (g_avg, g_exact))
    lines.append("逐条对决：规则更好 %d | guwenbert 更好 %d | 持平 %d"
                 % (len(better_r), len(better_g), tie))

    # 分档×文体交叉表
    cross = collections.defaultdict(lambda: {"n": 0, "r": 0, "g": 0,
                                             "rwin": 0, "gwin": 0, "tie": 0})
    for i in both:
        k = (bucket_of(rmap[i]["hakubun"]), genre_of(rmap[i].get("source_url", "")))
        c = cross[k]
        c["n"] += 1
        c["r"] += rmap[i]["edit_distance"]
        c["g"] += gmap[i]["edit_distance"]
        if rmap[i]["edit_distance"] < gmap[i]["edit_distance"]:
            c["rwin"] += 1
        elif gmap[i]["edit_distance"] < rmap[i]["edit_distance"]:
            c["gwin"] += 1
        else:
            c["tie"] += 1
    lines.append("\n分档×文体（规则 avg vs gwb avg | n | 规则胜/gwb胜/平）：")
    for (bk, gn), c in sorted(cross.items(), key=lambda kv: -kv[1]["n"]):
        lines.append("  %-8s %-6s n=%4d | 规则 %7.3f vs gwb %8.3f | %d/%d/%d"
                     % (bk, gn, c["n"], c["r"] / c["n"], c["g"] / c["n"],
                        c["rwin"], c["gwin"], c["tie"]))

    def top(ids, key):
        return sorted(ids, key=key)[:10]

    r_top = top(better_r, lambda i: rmap[i]["edit_distance"] - gmap[i]["edit_distance"])
    g_top = top(better_g, lambda i: gmap[i]["edit_distance"] - rmap[i]["edit_distance"])
    lines.append("\n规则相对优势 top10：")
    for i in r_top:
        lines.append("  %-24s 规则 %3d vs gwb %4d | %s"
                     % (i, rmap[i]["edit_distance"], gmap[i]["edit_distance"],
                        rmap[i]["hakubun"][:40]))
    lines.append("\nguwenbert 相对优势 top10：")
    for i in g_top:
        lines.append("  %-24s 规则 %3d vs gwb %4d | %s"
                     % (i, gmap[i]["edit_distance"], rmap[i]["edit_distance"],
                        rmap[i]["hakubun"][:40]))

    print("\n".join(lines))
    with open(os.path.join(EV, "night71_h2h.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("\nwritten: eval/night71_h2h.txt")


if __name__ == "__main__":
    main()
