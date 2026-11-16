# -*- coding: utf-8 -*-
"""find_ortho_pairs.py — 从基线评测输出里挖「got 有而 expected 无」的旧字体候选对。

方法：对每条结果，统计 got 中出现而 expected 未出现的汉字 c，
若该条 expected 中存在另一汉字 d 使得...（无法自动对齐），退而求其次：
直接列出 got 独有汉字的频次表，人工核对是否旧字体。
用法: python -X utf8 tools/find_ortho_pairs.py [night3_results_baseline.json]
"""
import collections
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "night3_results_baseline.json"
    with open(os.path.join(ROOT, "eval", name), encoding="utf-8") as f:
        d = json.load(f)
    freq = collections.Counter()
    where = {}
    for r in d["results"]:
        got = set(r["udkundoku_kakikudashi"])
        exp = set(r["expected_kakikudashi"])
        for c in got - exp:
            if "\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf":
                freq[c] += 1
                where.setdefault(c, []).append(r["id"])
    for c, n in freq.most_common(40):
        print("%s x%d  %s" % (c, n, ",".join(where[c][:6])))


if __name__ == "__main__":
    main()
