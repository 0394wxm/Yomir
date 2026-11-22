# -*- coding: utf-8 -*-
"""night79_reclassify.py — N79 一時補助：接続系 7 条の cat を function→content に変更。

理由：find_in_lexicon 系は「内容词先→功能词后」の二段走査で、function に置いた
かな混じり複合形（而る後 等）は 1 字内容词（後・而・何）に位置を先取され、
自分の語料行で絶対に命中しない＝死条目化する（dry-run で実証）。
D3 の旧 209 条の function 分類（glossary_lexicon.py）は変更しない（読み取り専用制約）。
用法: python -I tools/night79_reclassify.py
"""
import io
import re

FILES = [
    "eval/night79_decisions_000.json",
    "eval/night79_decisions_050.json",
    "eval/night79_decisions_100.json",
]
PATTERN = (r'("word": "(?:而る後|而ち|奈何|何如|如何|以為|嗚呼)"[^}]*?"cat": ")function(")')


def main():
    for fn in FILES:
        t = io.open(fn, encoding="utf-8").read()
        n, cnt = re.subn(PATTERN, r"\g<1>content\g<2>", t)
        io.open(fn, "w", encoding="utf-8", newline="\n").write(n)
        print("%s: changed %d" % (fn, cnt))


if __name__ == "__main__":
    main()
