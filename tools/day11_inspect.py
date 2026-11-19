# -*- coding: utf-8 -*-
"""day11_inspect.py — 检查某个候选片段在 1000 条里的上下文分布。

用法: python tools/day11_inspect.py これ 之
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


def main():
    frag = sys.argv[1] if len(sys.argv) > 1 else "これ"
    want = sys.argv[2] if len(sys.argv) > 2 else "之"
    with open(os.path.join(EV, "day10_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]

    ctx = collections.Counter()
    hits = []
    need_keep = []
    for r in rows:
        g, e = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        if frag not in g:
            continue
        for m in re.finditer(re.escape(frag), g):
            ctx[g[max(0, m.start() - 2):m.start() + len(frag) + 2]] += 1
        if want in e and frag not in e:
            hits.append(r)
        elif frag in e:
            need_keep.append(r)

    print("含 %r 的条目：改写候选 %d / expected 也需要 %r 的 %d"
          % (frag, len(hits), frag, len(need_keep)))
    print("\n上下文 top 20:")
    for k, v in ctx.most_common(20):
        print("  %-10s %d" % (k, v))

    print("\n=== 候选改写样例（输出） ===")
    for r in hits[:8]:
        print(" [%s] got: %s" % (r["id"], norm(r["udkundoku_kakikudashi"])[:90]))
        print("       exp: %s" % norm(r["expected_kakikudashi"])[:90])

    print("\n=== expected 也含 %r 的样例（会误伤） ===" % frag)
    for r in need_keep[:8]:
        print(" [%s] got: %s" % (r["id"], norm(r["udkundoku_kakikudashi"])[:90]))
        print("       exp: %s" % norm(r["expected_kakikudashi"])[:90])


if __name__ == "__main__":
    main()
