# -*- coding: utf-8 -*-
"""day11_pick.py — D11 最终候选定选：带护栏的 Rule D 在 1000 条上的表现。

候选 D7（推荐）：これ->之，但保留以下情况（护栏）：
  * これ + 見/聞/言/思（真指示代词作宾语、后接和语动词）
  * これ + より/まで/から（时间/起点副词）
  * これ + ぞ/こそ/さへ/すら/だけ/のみ（强调/限定，现代和文用法）
  * これを以て / これに由りて（汉文训读固定套语中，两种写法都合规）
其余（尤其 これを/これに/これが/これの/これは/これと + 汉文动词）一律改为 之。

对比 D1（无护栏）。全部列出变差条目。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def lev(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


# 护栏：这些形态保留「これ」原样
GUARD_PATTERNS = [
    r"これ(?=[を見聞言思])",        # 真指示代词 + 和语动词
    r"これ(?=より|まで|から)",       # 起点/终点副词
    r"これ(?=[ぞこそ])",            # 强调
    r"これ(?=さへ|すら|だけ|のみ)",    # 限定
    r"これ(?=を以て|に由りて)",       # 汉文固定套语
]
GUARD_RX = re.compile("|".join(GUARD_PATTERNS))
SENTINEL = "\u0001KORE\u0001"


def rule_d_guarded(t):
    t2 = GUARD_RX.sub(SENTINEL, t)
    t2 = t2.replace("これ", "之")
    return t2.replace(SENTINEL, "これ")


def rule_d_plain(t):
    return t.replace("これ", "之")


def main():
    with open(os.path.join(EV, "day10_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]

    base = [lev(norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])) for r in rows]
    base_avg = sum(base) / len(base)

    for name, fn in [("D1 全替换（无护栏）", rule_d_plain),
                     ("D7 带护栏（推荐）", rule_d_guarded)]:
        ds, better, worse, changed = [], [], [], 0
        for r, bd in zip(rows, base):
            g, e = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
            new = fn(g)
            if new != g:
                changed += 1
            nd = lev(new, e)
            ds.append(nd)
            if nd < bd:
                better.append(r["id"])
            elif nd > bd:
                worse.append((r["id"], bd, nd, g, new, e))
        avg = sum(ds) / len(ds)
        exact = sum(1 for x in ds if x == 0)
        print("%-22s 改写 %3d | avg %.3f (%+.3f) | 改善 %3d / 变差 %3d | 精确 %d"
              % (name, changed, avg, avg - base_avg, len(better), len(worse), exact))
        for w in worse:
            print("   !! [%s] %d->%d" % (w[0], w[1], w[2]))
            print("      got: %s" % w[3][:80])
            print("      new: %s" % w[4][:80])
            print("      exp: %s" % w[5][:80])
        print()

    # 护栏在语料外句子的行为
    print("=== 护栏在语料外句子的行为 ===")
    cases = ["これを見よ", "これより後", "これを以て", "これぞ", "これのみ",
             "これに由りて", "学びて時にこれを習う", "これを飲す", "これが為に",
             "これを誉めて曰く"]
    for s in cases:
        print("  %-20s -> %s" % (s, rule_d_guarded(s)))


if __name__ == "__main__":
    main()
