# -*- coding: utf-8 -*-
"""hit_quality.py — 量化命中质量：单字词 vs 多字词、疑似误配。"""
import collections
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.glossary_lexicon import find_in_lexicon  # noqa: E402


def main():
    with io.open(os.path.join(ROOT, "eval", "night5_results_full_v3.json"), encoding="utf-8") as f:
        items = json.load(f)["results"]
    lens = collections.Counter()
    words = collections.Counter()
    for r in items:
        text = r["hakubun"] + " " + r["expected_kakikudashi"]
        for h in find_in_lexicon(text, max_hits=5):
            lens[len(h["word"])] += 1
            words[h["word"]] += 1
    tot = sum(lens.values())
    print("命中总数 %d（200 句 × 最多 5 条）" % tot)
    print("按词长：", dict(sorted(lens.items())))
    print("单字占：%.0f%%" % (100.0 * lens[1] / tot))
    print("最高频命中：", words.most_common(15))


if __name__ == "__main__":
    main()
