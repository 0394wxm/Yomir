# -*- coding: utf-8 -*-
"""day11_pick2.py — D11：护栏收紧版。目标——1000 条上 0 变差 + 明确护栏。

设计依据（来自前几轮的实测）：
  * 语料 93.4% 的条目 これ 数 == 之 数（1:1），引擎的「これ」几乎全是汉文「之」的训读；
  * expected 里「これ」出现 0 次 —— 语料内无一处需要保留假名；
  * 所以护栏只需要挡「明显不是汉文之」的现代和文特征：
      これを見よ型（指示代词 + 和语动词命令/意志）
      これより/まで/から（起点终点副词）
      これぞ/こそ/さへ/すら/だけ/のみ（强调限定助词）
    而「これを以て」这类汉文套语按 kanbun.info 规范**就该写 之を以て**，
    不再把它当护栏（前一版把它当护栏反而少改了 130 处）。

候选：
  D8  只挡「和语动词」+「强调/限定」+「より/まで/から」
  D9  D8 再加「これこれ」叠词
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


S = "\u0001KORE\u0001"

# D8：只挡真·现代和文用法
D8_RX = re.compile(r"これ(?=[を見聞言思]|より|まで|から|ぞ|こそ|さへ|すら|だけ|のみ)")
# D9：D8 + 叠词
D9_RX = re.compile(r"これ(?:これ|(?=[を見聞言思]|より|まで|から|ぞ|こそ|さへ|すら|だけ|のみ))")


def make(rx, double=False):
    def fn(t):
        t2 = rx.sub(S, t)
        t2 = t2.replace("これ", "之")
        t2 = t2.replace(S, "これ")
        if double:
            t2 = t2.replace("之之", "これこれ")
        return t2
    return fn


def main():
    with open(os.path.join(EV, "day10_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]

    base = [lev(norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])) for r in rows]
    base_avg = sum(base) / len(base)
    print("基线 %.3f（精确 %d）\n" % (base_avg, sum(1 for x in base if x == 0)))

    cands = [
        ("D8 严格护栏", make(D8_RX)),
        ("D9 严格护栏+叠词", make(D9_RX, double=True)),
    ]
    rows_best = []
    for name, fn in cands:
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
        print("%-20s 改写 %3d | avg %.3f (%+.3f) | 改善 %3d / 变差 %3d | 精确 %d"
              % (name, changed, avg, avg - base_avg, len(better), len(worse),
                 sum(1 for x in ds if x == 0)))
        for w in worse:
            print("   !! [%s] %d->%d  got:%s" % (w[0], w[1], w[2], w[3][:60]))
            print("                          new:%s" % w[4][:60])
            print("                          exp:%s" % w[5][:60])
        rows_best.append({"name": name, "changed": changed, "avg": round(avg, 3),
                          "delta": round(avg - base_avg, 3), "better": len(better),
                          "worse": len(worse)})
        print()

    print("=== D8 护栏在语料外句子的行为 ===")
    fn = make(D8_RX)
    for s in ["これを見よ", "これより後", "これを以て", "これぞ", "これのみ",
              "これに由りて", "学びて時にこれを習う", "これを飲す", "これが為に",
              "これを誉めて曰く", "これこれ", "これすなわち"]:
        print("  %-18s -> %s" % (s, fn(s)))

    with open(os.path.join(EV, "day11_pick2.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"base_avg": round(base_avg, 3), "candidates": rows_best},
                  f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
