# -*- coding: utf-8 -*-
"""day5_why_verb_dead.py — 定位「动词活用错」分支的结构性失效原因。

分支条件（classify_errors.py:70）：
    VERB_TAIL_RX.search(e) and kanji_only(e) and kanji_only(e) in kanji_only(g)

问题：difflib 的 replace 块里，got 侧与 expected 侧的**汉字通常是差异本身**
（如 got=「す」exp=「ぼせり」），所以 kanji_only(e) 几乎不可能出现在 kanji_only(g) 中。
本脚本量化这一点：在 50 条的全部 diff 块上，逐个检查该条件的三个合取项。
"""
import difflib
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from classify_errors import VERB_TAIL_RX, kanji_only  # noqa: E402


def main():
    with io.open(os.path.join(ROOT, "eval", "day5_label_50.tsv"), encoding="utf-8") as f:
        rows = [l.split("\t") for l in f.read().strip().split("\n")[1:] if l.count("\t") >= 3]

    n_tail = n_kanji = n_in = 0
    all_blocks = 0
    for p in rows:
        got, exp = p[2], p[3]
        sm = difflib.SequenceMatcher(a=got, b=exp)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            all_blocks += 1
            g, e = got[i1:i2], exp[j1:j2]
            a = bool(e and VERB_TAIL_RX.search(e))
            b = bool(kanji_only(e))
            c = bool(kanji_only(e)) and kanji_only(e) in kanji_only(g)
            n_tail += a
            n_kanji += b
            n_in += c
    print("50 条共 %d 个非 equal 差异块" % all_blocks)
    print("  ① expected 片段以文语活用尾结尾：%d 块" % n_tail)
    print("  ② 且 expected 片段含汉字：        %d 块" % n_kanji)
    print("  ③ 且该汉字串出现在 got 片段里：    %d 块  ← 实际能触发的" % n_in)

    # 举例说明 ③ 为何几乎不可能：列出 ①② 都成立但 ③ 失败的块
    print()
    print("=== ①② 成立但 ③ 失败的块（前 15 个）===")
    shown = 0
    for p in rows:
        got, exp = p[2], p[3]
        sm = difflib.SequenceMatcher(a=got, b=exp)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            g, e = got[i1:i2], exp[j1:j2]
            if e and VERB_TAIL_RX.search(e) and kanji_only(e) and kanji_only(e) not in kanji_only(g):
                print("  %-14s got=%-8r exp=%-8r  kanji(exp)=%r  kanji(got)=%r"
                      % (p[0], g, e, kanji_only(e), kanji_only(g)))
                shown += 1
                if shown >= 15:
                    return


if __name__ == "__main__":
    main()
