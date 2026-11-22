# -*- coding: utf-8 -*-
"""night79_roadmap_append.py — N79 helper: ROADMAP.md 末尾に 1 行追加（既存バイトは書き換えない）。"""
import io
import os

LINE = (
    "- 状態: DONE - Night 79(2026-11-23,分支 night79-lexicon-expand):词库扩充 500→824"
    "(golden_8165 汉字复合词频次挖矿 503 候选→逐条 weblio+语料双证据入库 324/排除 179/剩余 0;"
    "N76 §3.5 缺口 而る後/而ち/利す 全收录;本体 GLOSSARY_LEXICON 500 条不动"
    "(N75/N77 size 不变式维持),合并查找在 llm 层 find_in_lexicon2;"
    "golden_4000 与 night77 归档逐位一致 13.517/24/0;tests 363=363;"
    "accept 79 PASS fail=0 skip=0)\n"
)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "ROADMAP.md")
    with io.open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(LINE)
    print("appended 1 line to ROADMAP.md")


if __name__ == "__main__":
    main()
