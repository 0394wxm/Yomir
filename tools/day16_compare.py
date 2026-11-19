# -*- coding: utf-8 -*-
"""day16_compare.py — D16：规则引擎 vs guwenbert 在新增 1000 条上的对比。

两边都是同一批 1000 条（golden_2000[1000:]），同一套 norm() + Levenshtein。
输出 eval/day16_compare.json 并打印分档/文体/逐条 win-lose。
"""
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
    if "/keibu/daigaku" in u:
        return "大学"
    if "/keibu/kokyo" in u:
        return "孝経"
    if "/keibu/rongo" in u:
        return "論語"
    if "/koji/" in u:
        return "故事"
    return "その他"


def stats(rows):
    ok = [r for r in rows if r["edit_distance"] is not None]
    n = len(ok)
    return {
        "n": n,
        "exact": sum(1 for r in ok if r["exact_match"]),
        "avg": round(sum(r["edit_distance"] for r in ok) / n, 3) if n else None,
    }


def by(rows, keyfn):
    d = collections.defaultdict(list)
    for r in rows:
        d[keyfn(r)].append(r)
    return {k: stats(v) for k, v in d.items()}


def main():
    rule_all = json.load(open(os.path.join(EV, "day16_results_2000.json"),
                              encoding="utf-8"))["results"]
    rule = rule_all[1000:]
    gwb = json.load(open(os.path.join(EV, "day16_guwenbert_new1000.json"),
                         encoding="utf-8"))["results"]
    assert len(rule) == len(gwb) == 1000
    assert [r["id"] for r in rule] == [r["id"] for r in gwb], "两边 id 顺序不一致"

    sr, sg = stats(rule), stats(gwb)
    print("=== 新增 1000 条：规则引擎 vs guwenbert ===", flush=True)
    print("规则引擎   n=%d  avg %.3f  exact %d" % (sr["n"], sr["avg"], sr["exact"]), flush=True)
    print("guwenbert  n=%d  avg %.3f  exact %d" % (sg["n"], sg["avg"], sg["exact"]), flush=True)
    print("Δ(规则-guберт) %+.3f" % (sr["avg"] - sg["avg"]), flush=True)

    print("\n--- 分档 ---", flush=True)
    br = by(rule, lambda r: bucket_of(r["hakubun"]))
    bg = by(gwb, lambda r: bucket_of(r["hakubun"]))
    print("%-9s %6s %9s %9s %9s" % ("分档", "n", "规则", "guwenbert", "Δ"), flush=True)
    for b in ["≤20字", "21-40字", "41-60字", ">60字"]:
        if b in br:
            print("%-9s %6d %9.3f %9.3f %+9.3f"
                  % (b, br[b]["n"], br[b]["avg"], bg[b]["avg"], br[b]["avg"] - bg[b]["avg"]),
                  flush=True)

    print("\n--- 文体 ---", flush=True)
    gr = by(rule, lambda r: genre_of(r.get("source_url", "")))
    gg = by(gwb, lambda r: genre_of(r.get("source_url", "")))
    print("%-7s %6s %9s %9s %9s" % ("文体", "n", "规则", "guwenbert", "Δ"), flush=True)
    for g_ in ["故事", "大学", "孝経"]:
        if g_ in gr:
            print("%-7s %6d %9.3f %9.3f %+9.3f"
                  % (g_, gr[g_]["n"], gr[g_]["avg"], gg[g_]["avg"],
                     gr[g_]["avg"] - gg[g_]["avg"]), flush=True)

    better = worse = same = 0
    for a, b in zip(rule, gwb):
        da, db = a["edit_distance"], b["edit_distance"]
        if da is None or db is None:
            continue
        if da < db:
            better += 1
        elif da > db:
            worse += 1
        else:
            same += 1
    print("\n--- 逐条 ---", flush=True)
    print("规则更好 %d | guwenbert 更好 %d | 持平 %d" % (better, worse, same), flush=True)

    out = {
        "rule": sr, "guwenbert": sg, "delta": round(sr["avg"] - sg["avg"], 3),
        "by_bucket": {b: {"rule": br[b], "guwenbert": bg.get(b)} for b in br},
        "by_genre": {g_: {"rule": gr[g_], "guwenbert": gg.get(g_)} for g_ in gr},
        "pairwise": {"rule_better": better, "guwenbert_better": worse, "same": same},
        "guwenbert_runtime_sec": 3802,
        "guwenbert_build_sec": 110,
    }
    json.dump(out, open(os.path.join(EV, "day16_compare.json"), "w",
                        encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("\nwritten: eval/day16_compare.json", flush=True)


if __name__ == "__main__":
    main()
