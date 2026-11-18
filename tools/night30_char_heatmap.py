# -*- coding: utf-8 -*-
"""night30_char_heatmap.py — Night 30：got/exp 字符级替换热图 → 正字化表候选。

方法：night29 归档（1705 条）上 difflib 对齐，收集 replace 块的字符配对：
  A) 汉字→汉字：SHINJITAI_MAP 候选（旧→新）或词典缺口
  B) 汉字→假名 / 假名→汉字：解析层差异（计数不动手）
先离线模拟候选（应用到 got 再算 dist），净赚且零回归才考虑上线。
"""
import difflib
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.kundoku_rules import SHINJITAI_MAP  # noqa: E402


def norm(s):
    return re.sub(r"\s+", "", s)


def is_kanji(c):
    return bool(c) and ("\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf")


def main():
    with open(os.path.join(ROOT, "eval", "night29_results_parallel.json"), encoding="utf-8") as f:
        rows = json.load(f)["results"]

    kanji2kanji = Counter()
    kanji2kana = Counter()
    kana2kanji = Counter()
    for r in rows:
        got = norm(r.get("udkundoku_kakikudashi") or "")
        exp = norm(r["expected_kakikudashi"])
        sm = difflib.SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op == "equal":
                continue
            g, e = got[a1:a2], exp[b1:b2]
            if len(g) == 1 and len(e) == 1:
                if is_kanji(g) and is_kanji(e):
                    kanji2kanji[(g, e)] += 1
                elif is_kanji(g):
                    kanji2kana[(g, e)] += 1
                elif is_kanji(e):
                    kana2kanji[(g, e)] += 1

    mapped = Counter()
    unmapped = Counter()
    for (g, e), n in kanji2kanji.most_common():
        if SHINJITAI_MAP.get(g) == e:
            mapped[(g, e)] += n
        else:
            unmapped[(g, e)] += n

    print("=== 汉字→汉字 1:1 替换（top 40）===")
    for (g, e), n in unmapped.most_common(40):
        tag = "MAP候选" if SHINJITAI_MAP.get(g) is None else ("表里已有但值不同!" if SHINJITAI_MAP.get(g) else "")
        print("  %s→%s  %4d  %s" % (g, e, n, tag))
    print("\n已映射的替换量（SHINJITAI_MAP 现行生效）:", sum(mapped.values()), "处")
    print("未映射的替换量:", sum(unmapped.values()), "处")

    print("\n=== 汉字→假名 1:1（top 15，解析层，不动手）===")
    for (g, e), n in kanji2kana.most_common(15):
        print("  %s→%s  %4d" % (g, e, n))
    print("\n=== 假名→汉字 1:1（top 10）===")
    for (g, e), n in kana2kanji.most_common(10):
        print("  %s→%s  %4d" % (g, e, n))

    # 离线模拟：把未映射的 汉字→汉字 top 候选加进一个临时映射再算 dist
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

    cands = {g: e for (g, e), n in unmapped.most_common(60) if n >= 5 and SHINJITAI_MAP.get(g) is None}
    print("\n=== 离线模拟：候选 %d 个（count>=5 且表中无）===" % len(cands))
    if cands:
        imp = wor = fla = 0
        tot_old = tot_new = 0
        worst = []
        for r in rows:
            got = norm(r.get("udkundoku_kakikudashi") or "")
            exp = norm(r["expected_kakikudashi"])
            new = "".join(cands.get(c, c) for c in got)
            d_o, d_n = lev(got, exp), lev(new, exp)
            if d_n < d_o:
                imp += 1
            elif d_n > d_o:
                wor += 1
                worst.append((r["id"], d_o, d_n))
            else:
                fla += 1
            tot_old += d_o
            tot_new += d_n
        n = len(rows)
        print("  avgDist %.2f -> %.2f (%+.2f)  改善 %d / 变差 %d / 持平 %d"
              % (tot_old / n, tot_new / n, (tot_new - tot_old) / n, imp, wor, fla))
        for id_, d_o, d_n in sorted(worst, key=lambda t: t[2] - t[1], reverse=True)[:10]:
            print("    变差 %s %+d (%d->%d)" % (id_, d_n - d_o, d_o, d_n))

    with open(os.path.join(ROOT, "eval", "night30_char_heatmap.json"), "w", encoding="utf-8") as f:
        json.dump({
            "kanji2kanji_top": [["%s" % g, "%s" % e, n] for (g, e), n in unmapped.most_common(200)],
            "mapped_total": sum(mapped.values()),
            "unmapped_total": sum(unmapped.values()),
            "kanji2kana_top": [["%s" % g, "%s" % e, n] for (g, e), n in kanji2kana.most_common(100)],
        }, f, ensure_ascii=False, indent=1)
    print("\nwritten: eval/night30_char_heatmap.json")


if __name__ == "__main__":
    main()
