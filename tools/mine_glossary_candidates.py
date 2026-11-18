# -*- coding: utf-8 -*-
"""mine_glossary_candidates.py — 从 200 条评测语料里挖「词库里还没有」的高频候选词（D3）。

只输出候选 + 频次 + 出处样例，不做自动选定（选词由人/agent 判断通用性）。
用法: python tools/mine_glossary_candidates.py
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

KANJI = r"\u4e00-\u9fff\u3400-\u4dbf"
KANA = r"\u3041-\u309f\u30a0-\u30ff"


def load(name="night5_results_full_v3.json"):
    with open(os.path.join(ROOT, "eval", name), encoding="utf-8") as f:
        return json.load(f)["results"]


def main():
    items = load()
    existing = {e["word"] for e in GLOSSARY_LEXICON}
    # 已知的「功能词」——即使高频也不作为新词条首选（它们是语法词）
    func_like = {"の", "に", "を", "は", "が", "と", "て", "して", "なり", "ざる", "べし",
                 "たる", "き", "し", "く", "る", "れ", "よ", "や", "か", "ぞ", "な", "ね",
                 "ば", "ど", "ども", "とも", "ながら", "のみ", "こそ", "さへ", "すら"}

    # 1) expected（正解の書き下し文）から漢字を含む 2〜4 字の連続を数える
    cnt = collections.Counter()
    src = collections.defaultdict(set)
    for r in items:
        txt = re.sub(r"\s+", "", r["expected_kakikudashi"])
        for n in (2, 3, 4):
            for i in range(len(txt) - n + 1):
                w = txt[i:i + n]
                if not re.fullmatch("[%s]+" % KANJI, w):
                    continue
                cnt[w] += 1
                src[w].add(r["id"])

    print("=== expected 里出现≥4 次的汉字串（前 120，已排除词库已有）===")
    shown = 0
    for w, c in cnt.most_common(400):
        if c < 4 or w in existing or w in func_like:
            continue
        # 长词优先：若它是某个更高频更长词的子串，跳过
        print("%-6s %3d  %s" % (w, c, ",".join(sorted(src[w])[:3])))
        shown += 1
        if shown >= 120:
            break

    # 2) 白文（原文）里的高频汉字串 —— 适合做「故事成語・人名・地名」候选
    print("\n=== 白文里出现≥6 次的汉字串（前 60）===")
    cnt2 = collections.Counter()
    src2 = collections.defaultdict(set)
    for r in items:
        txt = re.sub(r"\s+", "", r["hakubun"])
        for n in (2, 3, 4):
            for i in range(len(txt) - n + 1):
                w = txt[i:i + n]
                if not re.fullmatch("[%s]+" % KANJI, w):
                    continue
                cnt2[w] += 1
                src2[w].add(r["id"])
    shown = 0
    for w, c in cnt2.most_common(500):
        if c < 6 or w in existing:
            continue
        print("%-6s %3d  %s" % (w, c, ",".join(sorted(src2[w])[:3])))
        shown += 1
        if shown >= 60:
            break

    # 3) 词库条目在 200 条里的命中情况（哪些条目从没命中过 = 可能没用）
    print("\n=== 词库条目命中次数（200 条 expected+白文合计）===")
    alltext = "\n".join(re.sub(r"\s+", "", r["expected_kakikudashi"] + r["hakubun"]) for r in items)
    hit = []
    for e in GLOSSARY_LEXICON:
        w = e["word"]
        c = alltext.count(w) if w else 0
        hit.append((c, w))
    zero = [w for c, w in hit if c == 0]
    print("命中 0 次的条目：%d / %d" % (len(zero), len(hit)))
    print("例：", zero[:40])


if __name__ == "__main__":
    main()
