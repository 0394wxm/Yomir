# -*- coding: utf-8 -*-
"""lexicon_stats.py — D3 词库统计（用于 REPORT_DAY3 的数据段）。"""
import collections
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.glossary_lexicon import GLOSSARY_LEXICON, _ordered_entries  # noqa: E402


def main():
    old = GLOSSARY_LEXICON[:209]
    new = GLOSSARY_LEXICON[209:]
    print("旧 %d / 扩充 %d / 合计 %d" % (len(old), len(new), len(GLOSSARY_LEXICON)))
    print("扩充 kind 分布：", collections.Counter(e.get("kind") for e in new))
    print("旧库 kind 标记：", collections.Counter(e.get("kind", "未标") for e in old))
    print("词长分布（扩充）：", collections.Counter(len(e["word"]) for e in new))
    print("最长条目：", sorted((len(e["word"]), e["word"]) for e in new)[-5:])
    print("reading 缺失：", sum(1 for e in new if not e.get("reading")))
    print("meaning 最长：", max(len(e["meaning"]) for e in new))
    print("排序后前 20 条：", [e["word"] for e in _ordered_entries()[:20]])
    print("排序后末 10 条：", [e["word"] for e in _ordered_entries()[-10:]])


if __name__ == "__main__":
    main()
