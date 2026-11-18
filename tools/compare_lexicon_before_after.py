# -*- coding: utf-8 -*-
"""compare_lexicon_before_after.py — D3 前后对照（同一批 10 句 + 200 条全量）。

「前」= 旧 209 条 + 旧逻辑（列表顺序、子串匹配、无覆盖消歧）；
「后」= 合并 500 条 + 新逻辑（内容词优先、长词优先、覆盖消歧）。
统计：句级命中率、平均命中数、内容词命中占比、每句前 3 条词。
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.glossary_lexicon import GLOSSARY_LEXICON, find_in_lexicon  # noqa: E402

OLD = GLOSSARY_LEXICON[: GLOSSARY_LEXICON and 209]
# 旧 209 条里没有 kind 字段；用当前标注回填，保证「前」的口径与历史实现一致（不看 kind）
OLD_FUNCTION = {e["word"] for e in GLOSSARY_LEXICON if e.get("kind") == "function"}


def before(text, max_hits=5):
    hits, seen = [], set()
    for item in OLD:
        w = item.get("word", "")
        if not w or w in seen:
            continue
        if w in text:
            hits.append(item["word"])
            seen.add(w)
            if len(hits) >= max_hits:
                break
    return hits


def after(text, max_hits=5):
    return [h["word"] for h in find_in_lexicon(text, max_hits=max_hits)]


def main():
    with io.open(os.path.join(ROOT, "eval", "golden.json"), encoding="utf-8") as f:
        golden = json.load(f)
    with io.open(os.path.join(ROOT, "eval", "night5_results_full_v3.json"), encoding="utf-8") as f:
        v3 = json.load(f)["results"]

    print("旧词库 %d 条 / 现词库 %d 条" % (len(OLD), len(GLOSSARY_LEXICON)))
    print()
    print("=== 前 10 条（Night1-3 多句故事，与 night8_lexicon_check 同口径） ===")
    print("%-10s %-2s %-34s %-34s" % ("id", "", "前(209条)", "后(500条)"))
    for g in golden[:10]:
        text = g["hakubun"] + " " + g["expected_kakikudashi"]
        b, a = before(text), after(text)
        print("%-10s %-2s %-34s %-34s" % (g["id"], len(a), ",".join(b), ",".join(a)))

    print()
    for name, rows, key_b, key_a in (
        ("前 10 条", golden[:10], None, None),
        ("全 200 条", v3, None, None),
    ):
        nb = na = 0
        tot_b = tot_a = 0
        content_b = content_a = 0
        empty_b = empty_a = 0
        for r in rows:
            text = r["hakubun"] + " " + r["expected_kakikudashi"]
            b, a = before(text), after(text)
            if b:
                nb += 1
            if a:
                na += 1
            if not b:
                empty_b += 1
            if not a:
                empty_a += 1
            tot_b += len(b)
            tot_a += len(a)
            content_b += sum(1 for w in b if w not in OLD_FUNCTION)
            content_a += sum(1 for w in a if w not in OLD_FUNCTION)
        n = len(rows)
        print("=== %s（n=%d） ===" % (name, n))
        print("  句级命中：前 %d/%d (%.0f%%) → 后 %d/%d (%.0f%%)"
              % (nb, n, 100.0 * nb / n, na, n, 100.0 * na / n))
        print("  平均命中数：%.2f → %.2f" % (1.0 * tot_b / n, 1.0 * tot_a / n))
        print("  零命中的句子：%d → %d" % (empty_b, empty_a))
        if tot_b:
            print("  内容词占比：%.0f%% → %.0f%%"
                  % (100.0 * content_b / tot_b, 100.0 * content_a / max(tot_a, 1)))


if __name__ == "__main__":
    main()
