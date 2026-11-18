# -*- coding: utf-8 -*-
"""mine_kundoku_words.py — 从 expected 書き下し文里抽真实训读词形（汉字+送假名）。

与 lexicon_targets.txt（MeCab 切出的裸汉字）互补：本脚本抓的是用户实际会查的
「問う」「好む」「学ぶ」这类词形，含送假名，因此词库条目可以和语料逐字对齐。

输出 eval/kundoku_words.txt（word \t freq \t sample）
"""
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.glossary_lexicon import GLOSSARY_LEXICON  # noqa: E402

KANJI = "\u4e00-\u9fff\u3400-\u4dbf"
# 汉字串 + 送假名（平假名/片假名）串；也允许汉字串结尾（无送假名）
PAT = re.compile("([%s]+[ぁ-んァ-ヶ]+|[%s]{2,})" % (KANJI, KANJI))


def main():
    with open(os.path.join(ROOT, "eval", "night5_results_full_v3.json"), encoding="utf-8") as f:
        items = json.load(f)["results"]
    have = {e["word"] for e in GLOSSARY_LEXICON}

    cnt = collections.Counter()
    sample = {}
    for r in items:
        text = re.sub(r"\s+", "", r["expected_kakikudashi"])
        for w in PAT.findall(text):
            if w in have:
                continue
            cnt[w] += 1
            sample.setdefault(w, r["id"])

    rows = cnt.most_common()
    out = os.path.join(ROOT, "eval", "kundoku_words.txt")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        for w, c in rows:
            fh.write("%s\t%d\t%s\n" % (w, c, sample[w]))
    print("unique kundoku word forms（未收于旧词库）: %d" % len(rows))
    for k in (10, 5, 3, 2):
        print("  freq>=%d: %d" % (k, sum(1 for _, c in rows if c >= k)))
    print("written:", out)


if __name__ == "__main__":
    main()
