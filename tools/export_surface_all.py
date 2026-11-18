# -*- coding: utf-8 -*-
"""export_surface_all.py — 语料里所有含汉字的表面形 + 频次（D3 扩词的全集依据）。

输出 eval/lexicon_surface_all.txt，两列：word \t freq
"""
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from mecab_shim import tagger  # noqa: E402

KANJI_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")


def main():
    with open(os.path.join(ROOT, "eval", "night5_results_full_v3.json"), encoding="utf-8") as f:
        items = json.load(f)["results"]

    cnt = collections.Counter()
    for r in items:
        for seg in (r["hakubun"], r["expected_kakikudashi"]):
            for line in re.sub(r"\s+", "", seg).split("。"):
                if not line.strip():
                    continue
                for tok in tagger.parse(line).splitlines():
                    if tok in ("EOS", "") or "\t" not in tok:
                        continue
                    form, feat = tok.split("\t")
                    if not KANJI_RE.search(form):
                        continue
                    cnt[form] += 1

    out = os.path.join(ROOT, "eval", "lexicon_surface_all.txt")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        for w, c in cnt.most_common():
            fh.write("%s\t%d\n" % (w, c))
    print("unique surface forms: %d" % len(cnt))
    for lo, hi in [(50, 10 ** 9), (20, 49), (10, 19), (5, 9), (3, 4), (2, 2), (1, 1)]:
        n = sum(1 for _, c in cnt.items() if lo <= c <= hi)
        print("  freq %s-%s: %d 条" % (lo, "inf" if hi == 10 ** 9 else hi, n))
    print("written:", out)


if __name__ == "__main__":
    main()
