# -*- coding: utf-8 -*-
"""verify_readme_facts.py — 为 ROADMAP Night 61 任务条核对当前事实数字。只读。"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.kundoku_rules import SHINJITAI_MAP, MERGE_WORDS, E_KANA_TO_KANJI, F_KANA_TO_KANJI, G_KANA_TO_KANJI, H_KANA_TO_KANJI  # noqa: E402

print("SHINJITAI_MAP:", len(SHINJITAI_MAP), "对")
print("MERGE_WORDS:", len(MERGE_WORDS), "条")
print("Rule E/F/G/H 假名→汉字:", len(E_KANA_TO_KANJI), "/", len(F_KANA_TO_KANJI), "/",
      len(G_KANA_TO_KANJI), "/", len(H_KANA_TO_KANJI))
s = json.load(io.open(os.path.join(ROOT, "eval/night60_results_4000.json"), encoding="utf-8"))
sm = s["summary"]
print("night60: n=%s exact=%s avgDist=%s" % (sm["n"], sm["exact"], sm["avg_edit_distance"]))
g = json.load(io.open(os.path.join(ROOT, "eval/golden_4000_stats.json"), encoding="utf-8"))
print("golden_4000: total=%s uniq_hakubun=%s" % (g["total"], g["uniq_hakubun"]))
