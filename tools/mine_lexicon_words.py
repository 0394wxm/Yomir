# -*- coding: utf-8 -*-
"""mine_lexicon_words.py — 用 mecab-kanbun 切 200 条语料，统计「词库里还没有的内容词」（D3 选词依据）。

输出：按频次排序的候选词 + POS + 例句出处，供人工/agent 挑通用词条。
用法: python tools/mine_lexicon_words.py [--min N] [--top K]
"""
import argparse
import collections
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mecab_shim import tagger  # noqa: E402  (见同目录 mecab_shim.py)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=2)
    ap.add_argument("--top", type=int, default=300)
    ap.add_argument("--src", default="night5_results_full_v3.json")
    arg = ap.parse_args()

    with open(os.path.join(ROOT, "eval", arg.src), encoding="utf-8") as f:
        items = json.load(f)["results"]

    from backend.glossary_lexicon import GLOSSARY_LEXICON
    have = {e["word"] for e in GLOSSARY_LEXICON}

    cnt = collections.Counter()
    pos_of = {}
    ex = collections.defaultdict(list)

    for r in items:
        for line in r["expected_kakikudashi"].replace("\n", "").split("。"):
            if not line.strip():
                continue
            for tok in tagger.parse(line).splitlines():
                if tok in ("EOS", "") or "\t" not in tok:
                    continue
                form, feat = tok.split("\t")
                f = feat.split(",")
                # f[0]=品詞大類 f[1]=細分類 f[6]=lemma(字典形) f[7]=読み? 见 udkanbun 注释
                lemma = f[6] if len(f) > 6 and f[6] != "*" else form
                pos = f[0] + ("-" + f[1] if len(f) > 1 and f[1] != "*" else "")
                key = lemma
                if key in have or form in have:
                    continue
                if f[0] in ("助詞", "助動詞", "記号", "接尾辞", "接頭辞", "フィラー"):
                    continue
                cnt[key] += 1
                pos_of.setdefault(key, pos)
                if len(ex[key]) < 2:
                    ex[key].append(r["id"] + ":" + r["expected_kakikudashi"][:40])

    print("候选（lemma, 频次≥%d，已排除词库已有与纯语法词）：" % arg.min)
    n = 0
    for w, c in cnt.most_common(2000):
        if c < arg.min:
            break
        print("%-8s %3d  %-14s %s" % (w, c, pos_of[w], " | ".join(ex[w])))
        n += 1
        if n >= arg.top:
            break


if __name__ == "__main__":
    main()
