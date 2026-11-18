# -*- coding: utf-8 -*-
"""check_hits.py — 打印词库对若干句子的命中，验证内容词优先。"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from backend.glossary_lexicon import GLOSSARY_LEXICON as G, lexicon_size, find_in_lexicon

print("size", lexicon_size(),
      "content", sum(1 for e in G if e.get("kind") == "content"),
      "function", sum(1 for e in G if e.get("kind") == "function"),
      "unmarked", sum(1 for e in G if "kind" not in e))
for t in ["子曰、學而時習之、不亦説乎。",
          "君子曰、學不可以已。",
          "天將以夫子爲木鐸。",
          "學不可以已。青、取之於藍、而青於藍。"]:
    print(t, "=>", [h["word"] for h in find_in_lexicon(t, 5)])
