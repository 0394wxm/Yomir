# -*- coding: utf-8 -*-
"""list_lexicon_targets.py — 从 200 条语料生成「必须收录」的候选词（严格语料内）。

规则：
  * 只取 MeCab 切出的、在语料（白文 + expected 書き下し文）中真实出现的表面形；
  * 含汉字；
  * 不含旧字体/异体字噪音（由 NOISE 表排除）；
  * 排除旧词库已有的；
  * 排除纯数字与单字假名碎片。

输出 eval/lexicon_targets.txt（word \t freq \t pos \t 例句）
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
from backend.glossary_lexicon import GLOSSARY_LEXICON  # noqa: E402

KANJI_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")

# 旧字体/异体字：另有正字条目，或只作字形变体，不作独立词条
NOISE = set("爲為對対國国與与黃黄廣広惡悪亞亜圖図禮礼體体氣気滿満會会歲歳藥薬畫画顏顔"
            "屬属續続辭辞歸帰變変譯訳邊辺圓円獻献鐵鉄經経縣県顯顕濟済齊斉隨随醫医榮栄"
            "衞衛實実傳伝轉転舉挙覺覚靈霊溫温淨浄壹壱參参兩両嚴厳錢銭專専擇択澤沢驛駅"
            "數数點点譽誉飮飲獸獣應応餘余將将圍囲觸触釋釈當当戰戦挾挟從従盡尽對対"
            "諸諸漢漢樂楽學学敎教說説顏顔萬万衆衆")


def main():
    with open(os.path.join(ROOT, "eval", "night5_results_full_v3.json"), encoding="utf-8") as f:
        items = json.load(f)["results"]
    have = {e["word"] for e in GLOSSARY_LEXICON}

    cnt = collections.Counter()
    pos_of = {}
    ex = {}
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
                    if form in have:
                        continue
                    if len(form) == 1 and form in NOISE:
                        continue
                    cnt[form] += 1
                    pos_of.setdefault(form, feat.split(",")[0])
                    ex.setdefault(form, r["id"] + "|" + line[:24])

    rows = [(w, c) for w, c in cnt.most_common()]
    out = os.path.join(ROOT, "eval", "lexicon_targets.txt")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        for w, c in rows:
            fh.write("%s\t%d\t%s\t%s\n" % (w, c, pos_of[w], ex[w]))

    print("候选总数（语料内，排除旧词库与旧字噪音）：%d" % len(rows))
    for k in (10, 8, 6, 5, 4, 3, 2, 1):
        print("  freq>=%d: %d" % (k, sum(1 for _, c in rows if c >= k)))
    print("written:", out)


if __name__ == "__main__":
    main()
