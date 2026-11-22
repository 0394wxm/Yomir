# -*- coding: utf-8 -*-
"""verify_readme_facts.py — 为 README.md（Night 65 合并后同步版）核对当前事实数字。只读。

打印的每个数字都与 README.md 的「数字」一节一一对应，改 README 前先跑这个：
  SHINJITAI_MAP / MERGE_WORDS / Rule E/F/G/H/I/J/K/L/M / night73 评测（N73 Rule M 上线后的 golden_4000 口径）
  / golden_4000 与 golden_7908 构成 / OCR GT 行数 / 割注右先率基线（night50 归档）／
  pytest 收集计数（N73 新增断言——N70 テスト行漂移漏网的再発防止＝N72 移交⑥）。
"""
import io
import json
import os
import re as _re0
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.kundoku_rules import (SHINJITAI_MAP, MERGE_WORDS, E_KANA_TO_KANJI,  # noqa: E402
                                   F_KANA_TO_KANJI, G_KANA_TO_KANJI, H_KANA_TO_KANJI,
                                   I_KANA_TO_KANJI, J_KANA_TO_KANJI, K_KANA_TO_KANJI,
                                   L_KANA_TO_KANJI, M_KANA_TO_KANJI)

print("SHINJITAI_MAP:", len(SHINJITAI_MAP), "对")
print("MERGE_WORDS:", len(MERGE_WORDS), "条")
print("Rule E/F/G/H/I/J 假名→汉字:", len(E_KANA_TO_KANJI), "/", len(F_KANA_TO_KANJI), "/",
      len(G_KANA_TO_KANJI), "/", len(H_KANA_TO_KANJI), "/", len(I_KANA_TO_KANJI), "/",
      len(J_KANA_TO_KANJI))
print("Rule K 假名→汉字:", len(K_KANA_TO_KANJI), "条")
print("Rule L 假名→汉字:", len(L_KANA_TO_KANJI), "条")
print("Rule M 假名→汉字:", len(M_KANA_TO_KANJI), "条")
s = json.load(io.open(os.path.join(ROOT, "eval/night73_results_4000.json"), encoding="utf-8"))
sm = s["summary"]
print("night73(golden_4000): total=%s n=%s exact=%s avgDist=%s errors=%s"
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

# ---------------------------------------------------------------------------
# N68b：README 比对段——上面打印的每个值逐项 grep README.md，断言在位。
# 只读；任一项不在位 → 打印 FAIL 井 exit 1（不再只是打印数值了事）。
import re as _re

cer = json.load(io.open(os.path.join(ROOT, "eval/night68_gt_cer.json"), encoding="utf-8"))
README = io.open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()

def _flat(s):
    return _re.sub(r"\s+", "", s)

_flat_readme = _flat(README)

CHECKS = [
    ("SHINJITAI 組数", "**%d 組**" % len(SHINJITAI_MAP)),
    ("MERGE_WORDS 語数", "**%d 語**" % len(MERGE_WORDS)),
    ("night73 golden_4000 avgDist", "**%s**" % sm["avg_edit_distance"]),
    ("night73 golden_4000 exact", "**%d/4000**" % sm["exact"]),
    ("golden_4000 組数", "**%d 組**" % g["total"]),
    ("golden_4000 ユニーク", str(g["uniq_hakubun"])),
    ("golden_7908 組数", "**%d 組**" % g7["total"]),
    ("OCR GT 行数", "**%d 行**" % (len(gt) - 1)),
    ("OCR CER raw", "**%s**" % round(cer["overall_cer_micro"], 4)),
    ("OCR CER norm", "**%s**" % round(cer["overall_cer_norm_micro"], 4)),
    ("右先率 off/on", "%0.2f%% / %0.2f%%" % (b["off"]["rate"], b["on"]["rate"])),
    ("右先率 严格層対数", "%d 対" % b["strict"]["n"]),
    ("Rule J 語数", "**%d 語**" % len(J_KANA_TO_KANJI)),
    ("Rule K 語数", "**%d 語**" % len(K_KANA_TO_KANJI)),
    ("Rule L 語数", "**%d 語**" % len(L_KANA_TO_KANJI)),
    ("Rule M 語数", "**%d 語**" % len(M_KANA_TO_KANJI)),
]

# N73 新增：テスト行の pytest 計数断言（N72 移交⑥；--collect-only で実行せず数える）
fails = []
_py = subprocess.run([sys.executable, "-m", "pytest", "tests", "--collect-only", "-q"],
                     capture_output=True, text=True, cwd=ROOT, timeout=300)
_m = _re0.search(r"(\d+) tests? collected", _py.stdout or "")
if not _m:
    print("README 比对 %-22s FAIL（pytest --collect-only 失敗）" % "pytest 計数")
    fails.append("pytest 計数")
else:
    n_tests = int(_m.group(1))
    print("pytest --collect-only: %d tests" % n_tests)
    CHECKS.append(("テスト行 pytest 計数", "**%d passed**" % n_tests))

for name, needle in CHECKS:
    ok = _flat(needle) in _flat_readme
    print("README 比对 %-22s %s（期望含 %r）" % (name, "OK" if ok else "FAIL", needle))
    if not ok:
        fails.append(name)
print("README 比对: %d/%d 对上" % (len(CHECKS) - len(fails), len(CHECKS)))
if fails:
    print("README 漂移项: %s" % ", ".join(fails))
    sys.exit(1)
