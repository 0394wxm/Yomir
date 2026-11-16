# -*- coding: utf-8 -*-
"""eval_summary.py — 汇总两份评测 JSON：精确数/平均编辑距离/10 条子集/逐条对比。

用法: python -X utf8 tools/eval_summary.py <a.json> <b.json>...
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = __import__("os").path.dirname(__file__)


def load(name):
    import os
    path = name if os.path.isabs(name) else os.path.join(ROOT, "..", "eval", name)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def summarize(name):
    d = load(name)
    rs = d["results"]
    dists = [r["edit_distance"] for r in rs if "edit_distance" in r]
    avg = sum(dists) / len(dists) if dists else -1
    first10 = [r for r in rs if r["id"].split("-")[1] == "1"]
    e10 = sum(1 for r in first10 if r.get("exact_match"))
    print("%-32s exact %2d/%d  avgDist %.1f  first10子集 %d/%d"
          % (name, d["exact_match_count"], d["total"], avg, e10, len(first10)))
    return d


def main():
    docs = [summarize(n) for n in sys.argv[1:]]
    if len(docs) == 2:
        a, b = docs
        ba = {r["id"]: r for r in a["results"]}
        bb = {r["id"]: r for r in b["results"]}
        improved = worsened = same = 0
        for rid in ba:
            da = ba[rid].get("edit_distance", 999)
            db_ = bb.get(rid, {}).get("edit_distance", 999)
            if db_ < da:
                improved += 1
            elif db_ > da:
                worsened += 1
            else:
                same += 1
        print("\n%s vs %s: 编辑距离改善 %d 条 / 变差 %d 条 / 持平 %d 条"
              % (sys.argv[2], sys.argv[1], improved, worsened, same))
        for rid in sorted(ba):
            da = ba[rid].get("edit_distance", 999)
            db_ = bb.get(rid, {}).get("edit_distance", 999)
            if db_ != da:
                print("  %-12s dist %d -> %d" % (rid, da, db_))


if __name__ == "__main__":
    main()
