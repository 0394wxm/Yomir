# -*- coding: utf-8 -*-
"""day14_shape.py — D14 修正步：每个候选字在 expected 里的**后接假名**统计。

三个测试失败暴露了两个必须回答的问题：
  1. すでに → 「既」还是「既に」？（expected 里是 既に 吗）
  2. みな → 「皆」还是「皆な」？会不会误伤 みなす（看做）？

做法：把 expected 里每个候选字后面 1~3 字原样统计，看它是否带送り仮名。
再对比 got 里假名串的实际形态。
"""
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

KANA = re.compile(r"[\u3041-\u309f\u30a0-\u30ff]")


def norm(s):
    return re.sub(r"\s+", "", s or "")


PAIRS = [("みな", "皆"), ("すでに", "既"), ("なお", "猶"), ("あに", "豈"), ("ただ", "唯")]


def main():
    with open(os.path.join(EV, "day11_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]

    for kana, kanji in PAIRS:
        tail = collections.Counter()
        for r in rows:
            exp = norm(r["expected_kakikudashi"])
            for m in re.finditer(re.escape(kanji), exp):
                i = m.end()
                nxt = exp[i:i + 2]
                # 取紧随其后的假名串（0~2 字）
                run = ""
                for c in nxt:
                    if KANA.match(c):
                        run += c
                    else:
                        break
                tail[run or "(汉字/标点)"] += 1
        print("\n=== expected 里「%s」的后接假名 ===" % kanji, flush=True)
        for t, n in tail.most_common(8):
            print("    %-8s %3d" % (t, n), flush=True)

        # got 里假名串的实际形态（看是否被别的假名包住）
        forms = collections.Counter()
        for r in rows:
            got = norm(r["udkundoku_kakikudashi"])
            for m in re.finditer(re.escape(kana), got):
                i, j = m.start(), m.end()
                prev = got[i - 1] if i > 0 else ""
                nxt = got[j] if j < len(got) else ""
                forms["%s[%s]%s" % (prev if KANA.match(prev) else "·", kana,
                                    nxt if KANA.match(nxt) else "·")] += 1
        print("  got 里「%s」的邻接形态 top 6：" % kana, flush=True)
        for f, n in forms.most_common(6):
            print("    %-16s %3d" % (f, n), flush=True)


if __name__ == "__main__":
    main()
