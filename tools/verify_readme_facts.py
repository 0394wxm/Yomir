# -*- coding: utf-8 -*-
"""verify_readme_facts.py — 为 README.md（Night 65 合并后同步版）核对当前事实数字。只读。

打印的每个数字都与 README.md 的「数字」一节一一对应，改 README 前先跑这个：
  SHINJITAI_MAP / MERGE_WORDS / Rule E/F/G/H/I / night64 评测（N64 合并后口径）
  / golden_4000 与 golden_7908 构成 / OCR GT 行数 / 割注右先率基线（night50 归档）。
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.kundoku_rules import (SHINJITAI_MAP, MERGE_WORDS, E_KANA_TO_KANJI,  # noqa: E402
                                   F_KANA_TO_KANJI, G_KANA_TO_KANJI, H_KANA_TO_KANJI,
                                   I_KANA_TO_KANJI)

print("SHINJITAI_MAP:", len(SHINJITAI_MAP), "对")
print("MERGE_WORDS:", len(MERGE_WORDS), "条")
print("Rule E/F/G/H/I 假名→汉字:", len(E_KANA_TO_KANJI), "/", len(F_KANA_TO_KANJI), "/",
      len(G_KANA_TO_KANJI), "/", len(H_KANA_TO_KANJI), "/", len(I_KANA_TO_KANJI))
s = json.load(io.open(os.path.join(ROOT, "eval/night64_results_4000.json"), encoding="utf-8"))
sm = s["summary"]
print("night64(golden_4000): total=%s n=%s exact=%s avgDist=%s errors=%s"
      % (s.get("total"), sm["n"], sm["exact"], sm["avg_edit_distance"], sm["errors"]))
g = json.load(io.open(os.path.join(ROOT, "eval/golden_4000_stats.json"), encoding="utf-8"))
print("golden_4000: total=%s uniq_hakubun=%s" % (g["total"], g["uniq_hakubun"]))
g7 = json.load(io.open(os.path.join(ROOT, "eval/golden_7908_stats.json"), encoding="utf-8"))
print("golden_7908: total=%s uniq_hakubun=%s（已入库；默认评测口径仍 golden_4000）"
      % (g7["total"], g7["uniq_hakubun"]))
gt = io.open(os.path.join(ROOT, "eval/ocr_gt_100.tsv"), encoding="utf-8").read().splitlines()
print("ocr_gt_100.tsv: %d 行（GT %d 行＋表头 1 行）" % (len(gt), len(gt) - 1))
o = json.load(io.open(os.path.join(ROOT, "eval/night50_order_rate.json"), encoding="utf-8"))
b = o["baseline"]
print("割注右先率基线: off=%.2f%% on=%.2f%% strict=%.1f%%"
      % (b["off"]["rate"], b["on"]["rate"], b["strict"]["rate"]))
