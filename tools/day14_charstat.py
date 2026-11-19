# -*- coding: utf-8 -*-
"""day14_charstat.py — D14 第二步：expected vs got 的字符级频次差（找 kana->kanji 类候选）。

Rule D（これ→之）证明了一个模式：kanbun.info 的規範書き下し把某些汉语虚词写成
**汉字**，而引擎一律写成**假名**。D11 只挖了「之」一个。本次系统性地找同类：

  delta(c) = count_in_expected(c) - count_in_got(c)

delta 大的汉字 = expected 里大量出现、引擎却写成别的东西（多半是假名）。
再对每个这样的汉字，统计 got 里同位置出现的是什么假名串。

输出 eval/day14_charstat.json。
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


def is_kanji(c):
    return "\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf"


def main():
    with open(os.path.join(EV, "day11_results_1000.json"), encoding="utf-8") as f:
        doc = json.load(f)
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]

    exp_c = collections.Counter()
    got_c = collections.Counter()
    for r in rows:
        exp_c.update(norm(r["expected_kakikudashi"]))
        got_c.update(norm(r["udkundoku_kakikudashi"]))

    rowsout = []
    for c in set(exp_c) | set(got_c):
        if not is_kanji(c):
            continue
        e, g = exp_c.get(c, 0), got_c.get(c, 0)
        if e >= 10 and e > g:
            rowsout.append({"char": c, "exp": e, "got": g, "delta": e - g})
    rowsout.sort(key=lambda x: -x["delta"])

    print("=== 汉字：expected 多于 got（kana->kanji 候选）top 40 ===", flush=True)
    print("  %-4s %6s %6s %6s" % ("字", "exp", "got", "delta"), flush=True)
    for r in rowsout[:40]:
        print("  %-4s %6d %6d %6d" % (r["char"], r["exp"], r["got"], r["delta"]), flush=True)

    # 对每个候选字，看 expected 里它前后是什么（判断是不是固定词）
    ctx = collections.defaultdict(collections.Counter)
    for r in rows:
        exp = norm(r["expected_kakikudashi"])
        for i, c in enumerate(exp):
            if c in {x["char"] for x in rowsout[:40]}:
                ctx[c][exp[max(0, i - 1):i + 2]] += 1

    print("\n=== 候选字在 expected 里的三元上下文 top 5 ===", flush=True)
    for r in rowsout[:25]:
        c = r["char"]
        print("  %s: %s" % (c, ", ".join("%r×%d" % (k, v) for k, v in ctx[c].most_common(5))),
              flush=True)

    out = {"n": len(rows), "kanji_exp_gt_got": rowsout[:80],
           "ctx": {c: ctx[c].most_common(8) for c in ctx}}
    with open(os.path.join(EV, "day14_charstat.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nwritten: eval/day14_charstat.json", flush=True)


if __name__ == "__main__":
    main()
