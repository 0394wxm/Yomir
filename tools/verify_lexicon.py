# -*- coding: utf-8 -*-
"""verify_lexicon.py — 逐条核验词库扩充（D3）。

三项硬检查：
  1. 每条 word 必须出现在 200 条语料（白文 + expected 書き下し文）里；
  2. 无重复 word（扩充内部、以及与旧 209 条）；
  3. reading/meaning 非空、meaning ≤ 60 字。
另外统计「内容词 vs 功能词」比例与排序效果。

退出码 0 = 全过；1 = 有不合格条目（会逐条列出）。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.glossary_lexicon import GLOSSARY_LEXICON  # noqa: E402
from backend.glossary_lexicon_extra import LEXICON_EXTRA_SOURCE, as_dicts  # noqa: E402


def old_entries():
    import backend.glossary_lexicon as gl
    return gl.GLOSSARY_LEXICON[: gl._OLD_SIZE]


def main():
    with open(os.path.join(ROOT, "eval", "night5_results_full_v3.json"), encoding="utf-8") as f:
        items = json.load(f)["results"]
    corpus = "\n".join(r["hakubun"] + "\n" + r["expected_kakikudashi"] for r in items)

    extra = as_dicts()
    old = old_entries()
    old_words = {e["word"] for e in old}
    problems = []
    seen = {}
    present = 0
    for d in extra:
        w = d["word"]
        if w in seen:
            problems.append("扩充内部重复：%s" % w)
        seen[w] = 1
        if w in old_words:
            problems.append("与旧词库重复：%s" % w)
        if w not in corpus:
            problems.append("语料中未出现：%s" % w)
        else:
            present += 1
        if not d.get("reading"):
            problems.append("缺 reading：%s" % w)
        m = d.get("meaning", "")
        if not m:
            problems.append("缺 meaning：%s" % w)
        elif len(m) > 60:
            problems.append("meaning 过长(%d)：%s" % (len(m), w))

    total = len(old) + len(extra)
    print("旧词库 %d 条 + 扩充 %d 条 = %d 条（目标 500）" % (len(old), len(extra), total))
    print("语料命中：%d / %d" % (present, len(extra)))
    fn = sum(1 for d in extra if d.get("kind") == "function")
    print("内容词 %d / 功能词 %d" % (len(extra) - fn, fn))
    print("SOURCE: %s" % LEXICON_EXTRA_SOURCE)

    # 全库去重（合并后）
    merged = {}
    for e in GLOSSARY_LEXICON:
        merged[e["word"]] = merged.get(e["word"], 0) + 1
    dups = {w: c for w, c in merged.items() if c > 1}
    if dups:
        problems.append("合并后仍有重复条目：%s" % ", ".join("%s×%d" % (w, c) for w, c in dups.items()))

    if total != 500:
        problems.append("总数不是 500：%d" % total)
    if problems:
        print("\n不合格 %d 条：" % len(problems))
        for p in problems:
            print("  -", p)
        return 1
    print("\n全部通过（500 条，无重复，全部语料内）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
