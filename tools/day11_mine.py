# -*- coding: utf-8 -*-
"""day11_mine.py — D11 第一步：1000 条误差解剖（找可规则化的表面模式）。

输入 eval/day10_results_1000.json（规则引擎 1000 条结果）。
输出 eval/day11_mine.json + stdout 摘要。

做法（照 Night 22 的方法论，但扩大到 1000 条）：
  1. 对每条做「输出 vs expected」的字符级 diff（difflib），抽取替换/删除/插入片段；
  2. 统计高频片段（n>=8）及其方向（输出多余 / 输出缺失）；
  3. 对每个高频片段计算「删除它」或「替换它」的语料影响（改善/变差/持平）；
  4. 词元级：把 diff 片段按 1-3 字 n-gram 聚合，找「输出里重复出现但 expected 里从不出现」的串。
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


def levenshtein(a, b):
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
        doc = json.load(f)
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    print("载入 %d 条结果" % len(rows), flush=True)

    # ---- 1. 字符级 diff 片段统计 ----
    del_frag = collections.Counter()   # 输出有、expected 没有（多余）
    ins_frag = collections.Counter()   # expected 有、输出没有（缺失）
    rep_frag = collections.Counter()   # 替换 (got -> exp)

    for r in rows:
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        sm = difflib.SequenceMatcher(None, got, exp, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "delete":
                frag = got[i1:i2]
                if 1 <= len(frag) <= 6:
                    del_frag[frag] += 1
            elif tag == "insert":
                frag = exp[j1:j2]
                if 1 <= len(frag) <= 6:
                    ins_frag[frag] += 1
            elif tag == "replace":
                a, b = got[i1:i2], exp[j1:j2]
                if 1 <= len(a) <= 6 and 1 <= len(b) <= 6:
                    rep_frag[(a, b)] += 1

    print("\n=== 输出多余片段 top 25（删除候选） ===", flush=True)
    for frag, n in del_frag.most_common(25):
        print("  %-8s %4d" % (frag, n), flush=True)

    print("\n=== 输出缺失片段 top 15 ===", flush=True)
    for frag, n in ins_frag.most_common(15):
        print("  %-8s %4d" % (frag, n), flush=True)

    print("\n=== 替换 top 25 ===", flush=True)
    for (a, b), n in rep_frag.most_common(25):
        print("  %-8s -> %-8s %4d" % (a, b, n), flush=True)

    # ---- 2. 候选规则的语料影响模拟 ----
    base_dist = [levenshtein(norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"]))
                 for r in rows]
    base_avg = sum(base_dist) / len(base_dist)
    print("\n基线 avgDist %.2f（n=%d）" % (base_avg, len(rows)), flush=True)

    def simulate(name, fn):
        ds = []
        changed = 0
        better = worse = same = 0
        keep_changed = 0
        for r, bd in zip(rows, base_dist):
            got = norm(r["udkundoku_kakikudashi"])
            exp = norm(r["expected_kakikudashi"])
            new = fn(got)
            if new != got:
                changed += 1
            nd = levenshtein(new, exp)
            ds.append(nd)
            if nd < bd:
                better += 1
            elif nd > bd:
                worse += 1
            else:
                same += 1
        avg = sum(ds) / len(ds)
        print("  %-34s 改写 %4d | avgDist %6.2f (delta %+6.2f) | 改善 %3d / 变差 %3d / 持平 %3d"
              % (name, changed, avg, avg - base_avg, better, worse, same), flush=True)
        return {"name": name, "changed": changed, "avg": round(avg, 3),
                "delta": round(avg - base_avg, 3), "better": better, "worse": worse,
                "same": same}

    print("\n=== 候选模拟（删除多余片段） ===", flush=True)
    sims = []
    # 只对 >=8 次的片段做模拟
    for frag, n in del_frag.most_common(12):
        if n < 8:
            continue
        sims.append(simulate("delete %r" % frag, lambda t, f=frag: t.replace(f, "")))

    print("\n=== 候选模拟（替换） ===", flush=True)
    for (a, b), n in rep_frag.most_common(12):
        if n < 8:
            continue
        sims.append(simulate("%r->%r" % (a, b), lambda t, x=a, y=b: t.replace(x, y)))

    out = {
        "n": len(rows),
        "base_avg": round(base_avg, 3),
        "del_frag": del_frag.most_common(80),
        "ins_frag": ins_frag.most_common(50),
        "rep_frag": [{"got": a, "exp": b, "n": n} for (a, b), n in rep_frag.most_common(60)],
        "simulations": sims,
    }
    with open(os.path.join(EV, "day11_mine.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nwritten: eval/day11_mine.json", flush=True)


if __name__ == "__main__":
    main()
