# -*- coding: utf-8 -*-
"""pick_lexicon_targets.py — 从 lexicon_targets.txt 里筛出可入词库的净候选，按频次排队。

排除：
  * 旧字体/异体字（有正字条目在列）；只保留新字体形；
  * 与旧词库同形不同写的近似重复（陷/陥/譽/擧/旣 等）；
  * 数字单字、单字假名碎片。

输出 eval/lexicon_targets_clean.txt（序号 \t word \t freq \t pos）
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OLD_FORMS = set("爲為對対國国與与黃黄廣広惡悪亞亜圖図禮礼體体氣気滿満會会歲歳藥薬畫画顏顔"
                "屬属續続辭辞歸帰變変譯訳邊辺圓円獻献鐵鉄經経縣県顯顕濟済齊斉隨随醫医榮栄"
                "衞衛實実傳伝轉転舉挙覺覚靈霊溫温淨浄壹壱參参兩両嚴厳錢銭專専擇択澤沢驛駅"
                "數数點点譽誉飮飲獸獣應応餘余將将圍囲觸触釋釈當当戰戦挾挟從従盡尽對対"
                "諸諸漢漢樂楽學学敎教說説萬万衆衆"
                "陷陥 觀観 號号 竊窃 隱隠 廢廃 發発 來来 惠恵 德徳 聲声 亂乱 寶宝 晉晋"
                "顚顛 繼継 脩修 冰氷 弐貳 旣既 彊強 恥恥 兎兔 鬻鬻 巵卮")

NEAR_DUP = {"陷", "陥", "譽", "擧", "旣", "晉", "竊", "隱", "廢", "發", "來", "惠", "德",
            "聲", "亂", "寶", "顚", "繼", "脩", "冰", "弐", "彊", "觀", "號", "冰", "嘗",
            "且", "意", "所", "豈", "蓋", "得", "焉", "其", "彼", "曰", "之"}


def main():
    rows = []
    with io.open(os.path.join(ROOT, "eval", "lexicon_targets.txt"), encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 3:
                continue
            w, c, pos = p[0], int(p[1]), p[2]
            if len(w) == 1 and (w in OLD_FORMS or w in NEAR_DUP):
                continue
            if len(w) == 1 and w.isdigit():
                continue
            rows.append((w, c, pos))

    # 复合词优先排在前面（同频次时），单字其后
    rows.sort(key=lambda r: (-r[1], -len(r[0]), r[0]))
    out = os.path.join(ROOT, "eval", "lexicon_targets_clean.txt")
    with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
        for i, (w, c, pos) in enumerate(rows, 1):
            fh.write("%d\t%s\t%d\t%s\n" % (i, w, c, pos))
    print("clean candidates: %d" % len(rows))
    for k in (10, 8, 6, 5, 4, 3, 2):
        print("  freq>=%d: %d" % (k, sum(1 for _, c, _ in rows if c >= k)))
    print("written:", out)


if __name__ == "__main__":
    main()
