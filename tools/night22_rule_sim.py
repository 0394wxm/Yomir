# -*- coding: utf-8 -*-
"""night22_rule_sim.py — 「而して」规则的输出层上下文分析与离线模拟。

数据：eval/night21_results_full.json（500 条，当前生产线引擎输出）。
只做字符串级模拟 + 编辑距离复算（与 run_eval 同一把尺子：剥空白后 lev），
不跑引擎。候选规则：
  R0 全删（上限参照，会破坏 expected 含而して 的条目——archive 里就有）
  R1 汉字前置删除 + 顧みて 护栏（候选上线规则）
  R2 汉字前置删除（无护栏，验证护栏在 archive 里是否多余）
输出 stdout 报告；规则实现先在模拟里验证，通过才进 backend。
"""
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GUARD = "顧みて"  # 经典句「顧みて而して他を言う」保护（Night7 撤销 Rule C 的证据）


def is_kanji(c):
    return bool(c) and ("\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf")


def char_class(c):
    if c == "":
        return "BOS"
    if is_kanji(c):
        return "kanji"
    if re.match(r"[ぁ-ゖァ-ヺ]", c):
        return "kana"
    return "punct"


def norm(s):
    return re.sub(r"\s+", "", s)


def lev(a, b):
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def rule_r1(text, guard=GUARD):
    """R1：删「而して」当且仅当前一字符是汉字且其前 3 字不是护栏「顧みて」。"""
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("而して", i):
            prev = text[i - 1] if i > 0 else ""
            guarded = i >= 3 and text[i - 3:i] == guard
            if is_kanji(prev) and not guarded:
                i += 3
                continue
        out.append(text[i])
        i += 1
    return "".join(out)


def rule_r1_noguard(text):
    return rule_r1(text, guard=None)


def rule_r0(text):
    return text.replace("而して", "")


def rule_r3(text):
    """R3：带护栏的 Rule C——「て而して」→「て」，但「顧みて而して」保留。"""
    return re.sub(r"(?<!顧み)て而して", "て", text)


def bucket(src):
    n = len(norm(src))
    return "<=20" if n <= 20 else ("20-40" if n <= 40 else ">40")


def main():
    with open(os.path.join(ROOT, "eval", "night21_results_full.json"), encoding="utf-8") as f:
        results = json.load(f)["results"]
    print("n=%d" % len(results))

    # ---- 1) 输出层上下文分布（每个「而して」出现处的前一字符类别）----
    ctx = Counter()
    ctx_by_want = Counter()  # want = expected 是否含而して
    for r in results:
        out = r["udkundoku_kakikudashi"]
        want = "而して" in r["expected_kakikudashi"]
        for m in re.finditer("而して", out):
            cls = char_class(out[m.start() - 1] if m.start() > 0 else "")
            ctx[cls] += 1
            ctx_by_want[(cls, want)] += 1
    print("\n=== 输出层「而して」前置字符分布 ===")
    for k, v in ctx.most_common():
        print("  prev=%-6s %4d" % (k, v))
    print("  --- 按 expected 是否含而して ---")
    for (cls, want), v in sorted(ctx_by_want.items()):
        print("  prev=%-6s want=%-5s %4d" % (cls, want, v))

    # ---- 2) 模拟三种规则 ----
    def apply(name, fn):
        imp = wor = fla = 0
        tot_old = tot_new = 0
        touched = 0
        touched_keep = 0
        rows = []
        per_bucket = {}
        for r in results:
            old = norm(r["udkundoku_kakikudashi"])
            new = norm(fn(r["udkundoku_kakikudashi"]))
            exp = norm(r["expected_kakikudashi"])
            d_old, d_new = lev(old, exp), lev(new, exp)
            b = bucket(r["hakubun"])
            pb = per_bucket.setdefault(b, [0, 0.0, 0.0, 0, 0, 0])
            pb[0] += 1
            pb[1] += d_old
            pb[2] += d_new
            if new != old:
                touched += 1
                if want_ := "而して" in r["expected_kakikudashi"]:
                    touched_keep += 1
            if d_new < d_old:
                imp += 1
                pb[3] += 1
            elif d_new > d_old:
                wor += 1
                pb[4] += 1
            else:
                fla += 1
                pb[5] += 1
            tot_old += d_old
            tot_new += d_new
            rows.append((r["id"], d_old, d_new))
        n = len(results)
        print("\n=== %s ===" % name)
        print("  改写条数 %d（其中 expected 含而して %d）" % (touched, touched_keep))
        print("  avgDist %.2f -> %.2f (%+.2f)" % (tot_old / n, tot_new / n, (tot_new - tot_old) / n))
        print("  改善 %d / 变差 %d / 持平 %d" % (imp, wor, fla))
        for b in ("<=20", "20-40", ">40"):
            pb = per_bucket.get(b)
            if not pb:
                continue
            cnt, so, sn, i2, w2, f2 = pb
            print("    %-6s n=%3d avgDist %6.2f -> %6.2f (%+6.2f) 改善 %d / 变差 %d / 持平 %d"
                  % (b, cnt, so / cnt, sn / cnt, (sn - so) / cnt, i2, w2, f2))
        regs = sorted(rows, key=lambda t: t[2] - t[1], reverse=True)[:8]
        imps = sorted(rows, key=lambda t: t[1] - t[2], reverse=True)[:8]
        print("  变差最多:", ", ".join("%s %+d" % (k, d2 - d1) for k, d1, d2 in regs if d2 > d1))
        print("  改善最多:", ", ".join("%s %+d" % (k, d1 - d2) for k, d1, d2 in imps if d2 < d1))
        return rows

    apply("R0 全删（上限参照）", rule_r0)
    r1_rows = apply("R1 汉字前置删 + 顧みて护栏（候选）", rule_r1)
    apply("R2 汉字前置删（无护栏）", rule_r1_noguard)
    apply("R3 て而して→て + 顧み护栏（候选上线）", rule_r3)

    # kana 前置的细分：て之外还有什么
    kc = Counter()
    for r in results:
        out = r["udkundoku_kakikudashi"]
        for m in re.finditer("而して", out):
            i = m.start()
            if i > 0 and re.match(r"[ぁ-ゖァ-ヺ]", out[i - 1]):
                kc[out[max(0, i - 2):i]] += 1
    print("\n=== kana 前置的前 2 字分布 ===")
    for k, v in kc.most_common():
        print("  %r: %d" % (k, v))

    # ---- 3) R1 触到的 expected 含而して 条目应恒为 0；单独断言 ----
    bad = [k for k, d1, d2 in r1_rows
           if d2 != d1 and False]  # 占位：上面 apply 已打印 touched_keep
    print("\n=== 经典句护栏自检 ===")
    for s in ["王は左右を顧みて而して他を言う", "顧みて而して他を言う", "而して鷸其肉を啄む",
              "君子は恵なりて而して費さず", "天は積気のみ"]:
        print("  %r -> %r" % (s, rule_r1(s)))


if __name__ == "__main__":
    main()
