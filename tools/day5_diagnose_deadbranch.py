# -*- coding: utf-8 -*-
"""day5_diagnose_deadbranch.py — 为什么「动词活用错」「旧字体」从不触发。

逐步复现 classify_pair 里的两个分支，对 50 条逐条打印判定路径。
不改分类器，只做只读诊断。
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

from backend.kundoku_rules import MERGE_WORDS, SHINJITAI_MAP  # noqa: E402
from day5_manual_labels import MANUAL  # noqa: E402
from classify_errors import PARTICLE_KANA, VERB_TAIL_RX, kanji_only  # noqa: E402


def trace(got, exp):
    sm = difflib.SequenceMatcher(a=got, b=exp)
    out = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        g, e = got[i1:i2], exp[j1:j2]
        why = []
        if g and e and "".join(SHINJITAI_MAP.get(c, c) for c in g) == e:
            why.append("OLD_FONT")
        if any(w in e and w not in got for w in MERGE_WORDS):
            why.append("PROPER")
        if e and len(e) <= 2 and all(c in PARTICLE_KANA for c in e) and kanji_only(g) == kanji_only(e):
            why.append("PARTICLE")
        if e and VERB_TAIL_RX.search(e) and kanji_only(e) and kanji_only(e) in kanji_only(g):
            why.append("VERB")
        out.append((op, g, e, why or ["SEG-or-kana"]))
    return out


def main():
    with io.open(os.path.join(ROOT, "eval", "night5_results_full_v3.json"), encoding="utf-8") as f:
        rows = {r["id"]: r for r in json.load(f)["results"]}

    print("SHINJITAI_MAP 条目数:", len(SHINJITAI_MAP))
    print("MERGE_WORDS 条目数:", len(MERGE_WORDS))
    print()

    # 1) 旧字体分支为何不触发：检查 diff 块里 got 侧是否真的含旧字体字
    print("=== 人工标了旧字体、但分类器没判的 16 条：diff 块里 got 侧是否含 SHINJITAI_MAP 的 key ===")
    for rid in MANUAL:
        if "旧字体" not in MANUAL[rid]:
            continue
        r = rows[rid]
        got = r.get("udkundoku_kakikudashi_norm") or r.get("udkundoku_kakikudashi", "")
        exp = re.sub(r"\s+", "", r["expected_kakikudashi"])
        old_chars = [(c, SHINJITAI_MAP[c]) for c in got if c in SHINJITAI_MAP]
        blocks = trace(got, exp)
        print("%-14s got中的旧字体字=%s" % (rid, old_chars or "（无）"))
        if not old_chars:
            print("                → 旧字体字不在 got 里（已在上游 normalize_shinjitai 转新字），"
                  "故分类器的 oldfont 分支无从命中")

    # 2) 动词活用分支为何不触发：VERB_TAIL_RX 与 expected 片段对照
    print()
    print("=== 人工标了动词活用错、但分类器没判的 45 条：第一个非 equal 块的 expected 片段 ===")
    shown = 0
    for rid in MANUAL:
        if "动词活用错" not in MANUAL[rid]:
            continue
        r = rows[rid]
        got = r.get("udkundoku_kakikudashi_norm") or r.get("udkundoku_kakikudashi", "")
        exp = re.sub(r"\s+", "", r["expected_kakikudashi"])
        blocks = trace(got, exp)
        first = next((b for b in blocks if "VERB" not in b[3]), None)
        if first and shown < 12:
            op, g, e, why = first
            print("%-14s 首块 %-7s got=%-10r exp=%-10r VERB尾?=%s 汉字包含?=%s why=%s"
                  % (rid, op, g, e, bool(VERB_TAIL_RX.search(e or "")),
                     (kanji_only(e) in kanji_only(g)) if kanji_only(e) else None, why))
            shown += 1

    # 3) 统计：所有 50 条里，VERB 分支是否曾触发过一次
    print()
    trig_verb = trig_old = trig_proper = 0
    for rid in MANUAL:
        r = rows[rid]
        got = r.get("udkundoku_kakikudashi_norm") or r.get("udkundoku_kakikudashi", "")
        exp = re.sub(r"\s+", "", r["expected_kakikudashi"])
        for op, g, e, why in trace(got, exp):
            if "VERB" in why:
                trig_verb += 1
            if "OLD_FONT" in why:
                trig_old += 1
            if "PROPER" in why:
                trig_proper += 1
    print("50 条里各分支触发次数：VERB=%d  OLD_FONT=%d  PROPER=%d" % (trig_verb, trig_old, trig_proper))


if __name__ == "__main__":
    main()
