# -*- coding: utf-8 -*-
"""day14_mine.py — D14 Rule E 第一步：在 Rule D 之后的基线上重新解剖 1000 条。

与 day11_mine.py 的区别：
  * 输入换成 eval/day11_results_1000.json（Rule D 已上线，avgDist 25.201）；
  * D11 已经把「これ→之」这类**整词替换**挖过，本次只看**它没碰过的层**
    （Rule D 之后仍然存在的误差）；
  * 额外做「短片段 × 前后文」交叉，避免只按单字统计导致候选不可判定。

输出 eval/day14_mine.json。
"""
import collections
import difflib
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
    with open(os.path.join(EV, "day11_results_1000.json"), encoding="utf-8") as f:
        doc = json.load(f)
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    base = sum(r["edit_distance"] for r in rows) / len(rows)
    print("载入 %d 条（当前生产线基线 avgDist %.3f）\n" % (len(rows), base), flush=True)

    del_frag = collections.Counter()
    ins_frag = collections.Counter()
    rep_frag = collections.Counter()
    del_ctx = collections.defaultdict(collections.Counter)   # 片段 -> 前2字上下文
    ins_ctx = collections.defaultdict(collections.Counter)

    for r in rows:
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        sm = difflib.SequenceMatcher(None, got, exp, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "delete":
                frag = got[i1:i2]
                if 1 <= len(frag) <= 6:
                    del_frag[frag] += 1
                    del_ctx[frag][got[max(0, i1 - 2):i1]] += 1
            elif tag == "insert":
                frag = exp[j1:j2]
                if 1 <= len(frag) <= 6:
                    ins_frag[frag] += 1
                    ins_ctx[frag][exp[max(0, j1 - 2):j1]] += 1
            elif tag == "replace":
                a, b = got[i1:i2], exp[j1:j2]
                if 1 <= len(a) <= 6 and 1 <= len(b) <= 6:
                    rep_frag[(a, b)] += 1

    print("=== 输出多余片段 top 30 ===", flush=True)
    for frag, n in del_frag.most_common(30):
        print("  %-8s %4d   前置: %s"
              % (frag, n, ", ".join("%r×%d" % (c, k) for c, k in del_ctx[frag].most_common(3))),
              flush=True)

    print("\n=== 输出缺失片段 top 20 ===", flush=True)
    for frag, n in ins_frag.most_common(20):
        print("  %-8s %4d   前置: %s"
              % (frag, n, ", ".join("%r×%d" % (c, k) for c, k in ins_ctx[frag].most_common(3))),
              flush=True)

    print("\n=== 替换 top 35 ===", flush=True)
    for (a, b), n in rep_frag.most_common(35):
        print("  %-6s -> %-6s %4d" % (a, b, n), flush=True)

    out = {
        "n": len(rows), "base_avg": round(base, 3),
        "del_frag": [{"frag": f, "n": n,
                      "ctx": del_ctx[f].most_common(5)} for f, n in del_frag.most_common(80)],
        "ins_frag": [{"frag": f, "n": n,
                      "ctx": ins_ctx[f].most_common(5)} for f, n in ins_frag.most_common(50)],
        "rep_frag": [{"got": a, "exp": b, "n": n} for (a, b), n in rep_frag.most_common(60)],
    }
    with open(os.path.join(EV, "day14_mine.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nwritten: eval/day14_mine.json", flush=True)


if __name__ == "__main__":
    main()
