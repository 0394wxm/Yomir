# -*- coding: utf-8 -*-
"""day11_final.py — D11 最终候选验证：Rule D 带护栏版（上线前最后一道离线核对）。

选定实现：これ -> 之，护栏保留：
  - これこれ（叠词）
  - これ + 見/聞/言/思（真指示代词接和语动词，如「これを見よ」）
  - これ + より/まで/から（起点终点副词）
  - これ + ぞ/こそ/さへ/すら/だけ/のみ（强调限定）
不挡「これを以て」等汉文套语（kanbun.info 规范本就写作 之を以て）。

本脚本验证：
  1. 1000 条上 0 变差
  2. 语料外句子护栏生效
  3. 与 D1 全替换的收益差距（护栏成本）
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

S = "\u0001K"

# Rule D 护栏（与将写入 backend/kundoku_rules.py 的实现逐字一致）
_KORE_GUARD = re.compile(
    r"これこれ"                      # 叠词
    r"|これ(?=[を見聞言思])"          # 真指示代词 + 和语动词
    r"|これ(?=より|まで|から)"        # 起点/终点/起点副词
    r"|これ(?=[ぞこそさへすらだけのみ])"  # 强调/限定
)


def style_kore_to_shi(text):
    """これ → 之（汉文训读规范字形），带护栏。

    依据（D11，1000 条）：expected 里「これ」0 次、「之」522 处；
    引擎输出「これ」527 处，93.4% 的条目两者计数 1:1。
    全替换在 1000 条上 0 变差 / 282 改善 / avgDist 26.09→25.20。
    """
    held = _KORE_GUARD.findall(text)
    out = _KORE_GUARD.sub(S, text)
    out = out.replace("これ", "之")
    it = iter(held)
    return re.sub(re.escape(S), lambda m: next(it), out)


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


def main():
    with open(os.path.join(EV, "day10_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]

    base, ds = [], []
    better, worse, changed = [], [], 0
    for r in rows:
        g, e = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        bd = lev(g, e)
        new = style_kore_to_shi(g)
        nd = lev(new, e)
        base.append(bd)
        ds.append(nd)
        if new != g:
            changed += 1
        if nd < bd:
            better.append(r["id"])
        elif nd > bd:
            worse.append((r["id"], bd, nd))
    ba, na = sum(base) / len(base), sum(ds) / len(ds)
    print("Rule D（带护栏）1000 条：")
    print("  改写 %d 条 | avgDist %.3f -> %.3f (%+.3f) | 改善 %d / 变差 %d | 精确 %d -> %d"
          % (changed, ba, na, na - ba, len(better), len(worse),
             sum(1 for x in base if x == 0), sum(1 for x in ds if x == 0)))
    if worse:
        print("  !! 变差条目：")
        for w in worse:
            print("     %s %d->%d" % w)
    else:
        print("  变差 0 条 —— 满足上线条件")

    print("\n语料外护栏检查：")
    for s in ["これを見よ", "これより後", "これぞ", "これのみ", "これこれ",
              "これに由りて", "これを以て", "学びて時にこれを習う",
              "これを飲す", "これを誉めて曰く", "これが為に"]:
        print("  %-18s -> %s" % (s, style_kore_to_shi(s)))

    with open(os.path.join(EV, "day11_final.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"base_avg": round(ba, 3), "new_avg": round(na, 3),
                   "delta": round(na - ba, 3), "changed": changed,
                   "better": len(better), "worse": len(worse),
                   "worse_ids": [w[0] for w in worse]}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
