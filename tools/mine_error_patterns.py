# -*- coding: utf-8 -*-
"""
mine_error_patterns.py — 从基线 diff 里挖高频错误模式（NIGHT4 规则设计的证据源）。

两类挖掘：
1) 助词类：kanji 序列相同、假名不同的 replace 块，记 (got假名, expected假名) 频次
2) 切分类：expected 里的 2~3 汉字串 W，在 got 里被拆成 W[0]+<1~3个假名>+W[1:]
   （典型：宋人 → 宋の人），记 W 频次（排除已在 MERGE_WORDS 的）

用法: python -X utf8 tools/mine_error_patterns.py eval/night4_results_baseline.json [N]
"""
import collections
import difflib
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.kundoku_rules import MERGE_WORDS  # noqa: E402


def is_kanji(c):
    return "\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf"


def kanji_only(s):
    return "".join(c for c in s if is_kanji(c))


def kana_only(s):
    return "".join(c for c in s if not is_kanji(c))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "eval/night4_results_baseline.json"
    topn = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    full = path if os.path.isabs(path) else os.path.join(ROOT, path)
    with open(full, encoding="utf-8") as f:
        d = json.load(f)

    particle_pairs = collections.Counter()
    particle_ctx = {}
    split_words = collections.Counter()
    split_ctx = {}
    for r in d["results"]:
        got = r.get("udkundoku_kakikudashi", "").strip()
        exp = r["expected_kakikudashi"].strip()
        if got == exp:
            continue
        sm = difflib.SequenceMatcher(a=got, b=exp)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            g, e = got[i1:i2], exp[j1:j2]
            # —— 助词类（细化）：只统计“短纯假名”差异块 ——
            # 1) 替换块：两侧都 ≤2 字纯假名
            if g and e and len(g) <= 2 and len(e) <= 2 \
               and not kanji_only(g) and not kanji_only(e):
                key = (g, e)
                particle_pairs[key] += 1
                particle_ctx.setdefault(key, []).append(
                    (r["id"], got[max(0, i1 - 6):i1] + "[" + g + "→" + e + "]" + exp[j2:j2 + 6]))
                continue
            # 2) got 多余的假名（expected 侧为空）
            if g and not e and len(g) <= 2 and not kanji_only(g):
                key = (g, "∅")
                particle_pairs[key] += 1
                particle_ctx.setdefault(key, []).append(
                    (r["id"], got[max(0, i1 - 6):i1] + "[" + g + "→∅]"))
                continue
            # 3) expected 有而 got 没有的假名
            if e and not g and len(e) <= 2 and not kanji_only(e):
                key = ("∅", e)
                particle_pairs[key] += 1
                particle_ctx.setdefault(key, []).append(
                    (r["id"], "[∅→" + e + "]" + exp[j2:j2 + 6]))
                continue
            # —— 切分类：expected 的汉字串在 got 里被假名拆开 ——
            if kanji_only(g) != kanji_only(e):
                for wlen in (3, 2):
                    done = False
                    for k in range(len(e) - wlen + 1):
                        w = e[k:k + wlen]
                        if not all(is_kanji(c) for c in w) or w in MERGE_WORDS:
                            continue
                        # got 里存在 W[0] + 1~3个假名 + W[1:]，且 got 里没有整词 W
                        pat = re.compile(re.escape(w[0]) + "[\u3040-\u309f]{1,3}" + re.escape(w[1:]))
                        if pat.search(got) and w not in got:
                            split_words[w] += 1
                            split_ctx.setdefault(w, []).append(
                                (r["id"], got[max(0, got.find(w[0]) - 4):got.find(w[0]) + wlen + 4]))
                            done = True
                            break
                    if done:
                        break
    print("=== 助词类 top%d（got假名 -> expected假名）===" % topn)
    for (gk, ek), n in particle_pairs.most_common(topn):
        ctx = particle_ctx[(gk, ek)][0][1]
        print("  %-4s -> %-4s  x%d   例: %s" % (gk, ek, n, ctx[:60]))
    print("=== 切分类 top%d（expected 整词，got 被假名拆开）===" % topn)
    for w, n in split_words.most_common(topn):
        print("  %-4s x%d   例: %s" % (w, n, split_ctx[w][0][1][:60]))


if __name__ == "__main__":
    main()
