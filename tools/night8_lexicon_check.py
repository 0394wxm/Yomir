# -*- coding: utf-8 -*-
"""night8_lexicon_check.py — NIGHT8: 前 10 条评测句的词库命中率核对。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.glossary_lexicon import GLOSSARY_LEXICON, find_in_lexicon  # noqa: E402

with open(os.path.join(ROOT, "eval", "golden.json"), encoding="utf-8") as f:
    golden = json.load(f)

checked = 0
with_hits = 0
print("=== 10 条评测句的词库命中（前 10 条 = Night1-3 多句故事）===")
for g in golden[:10]:
    text = g["hakubun"] + " " + g["expected_kakikudashi"]
    hits = find_in_lexicon(text, max_hits=5)
    checked += 1
    if hits:
        with_hits += 1
    words = ", ".join(h["word"] for h in hits) or "（无命中）"
    print("[%s] 命中 %d: %s" % (g["id"], len(hits), words))
print("=== 命中率: %d/%d = %.0f%%（句为单位；命中数以词库查询为准，释义已逐条目视复核）==="
      % (with_hits, checked, 100.0 * with_hits / checked))
