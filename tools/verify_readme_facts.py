# -*- coding: utf-8 -*-
"""verify_readme_facts.py — 为 README.md（Night 61 日语重写版）核对当前事实数字。只读。

打印的每个数字都与 README.md 的「数字」一节一一对应，改 README 前先跑这个：
  SHINJITAI_MAP / MERGE_WORDS / Rule E/F/G/H / night60 评测 / golden_4000 构成
  / OCR GT 行数 / 割注右先率基线（night50 归档）。
"""
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
print("night60: total=%s n=%s exact=%s avgDist=%s"
      % (s.get("total"), sm["n"], sm["exact"], sm["avg_edit_distance"]))
g = json.load(io.open(os.path.join(ROOT, "eval/golden_4000_stats.json"), encoding="utf-8"))
print("golden_4000: total=%s uniq_hakubun=%s" % (g["total"], g["uniq_hakubun"]))
gt = io.open(os.path.join(ROOT, "eval/ocr_gt_100.tsv"), encoding="utf-8").read().splitlines()
print("ocr_gt_100.tsv: %d 行（GT %d 行＋表头 1 行）" % (len(gt), len(gt) - 1))
o = json.load(io.open(os.path.join(ROOT, "eval/night50_order_rate.json"), encoding="utf-8"))
b = o["baseline"]
print("割注右先率基线: off=%.2f%% on=%.2f%% strict=%.1f%%"
      % (b["off"]["rate"], b["on"]["rate"], b["strict"]["rate"]))
