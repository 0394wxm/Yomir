# -*- coding: utf-8 -*-
"""night23_genre_compare.py — 分文体对照表：故事名言 500 vs 論語 117（同一生产线、同一把尺子）。"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(s):
    return re.sub(r"\s+", "", s)


def bucket(src):
    n = len(norm(src))
    return "<=20" if n <= 20 else ("20-40" if n <= 40 else ">40")


def load(name, key="results"):
    with open(os.path.join(ROOT, "eval", name), encoding="utf-8") as f:
        return json.load(f)[key]


def stats(rows):
    ok = [r for r in rows if r.get("edit_distance") is not None]
    per = {}
    for r in ok:
        per.setdefault(bucket(r["hakubun"]), []).append(r["edit_distance"])
    return {
        "n": len(ok),
        "exact": sum(1 for r in ok if r["exact_match"]),
        "avg": sum(r["edit_distance"] for r in ok) / len(ok) if ok else -1,
        "buckets": {b: (len(v), sum(v) / len(v)) for b, v in per.items()},
    }


def main():
    koji = stats(load("night22_results_full.json"))
    rongo = stats(load("night23_results_rongo.json", key="results"))
    print("=== 分文体对照（当前生产线，Rule C' 后）===")
    print("%-10s %5s %8s %6s  %s" % ("文体", "n", "avgDist", "exact", "分档"))
    for name, st in (("故事名言", koji), ("論語", rongo)):
        bs = "  ".join("%s %.2f(n=%d)" % (b, a, n) for b, (n, a) in sorted(st["buckets"].items()))
        print("%-10s %5d %8.2f %3d/%-3d  %s" % (name, st["n"], st["avg"], st["exact"], st["n"], bs))


if __name__ == "__main__":
    main()
