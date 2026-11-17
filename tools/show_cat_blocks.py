# -*- coding: utf-8 -*-
"""show_cat_blocks.py — 抽看某错误类别的实际差异块（人工审查分类器质量用）。
用法: python -X utf8 tools/show_cat_blocks.py eval/xxx_classified.json 切分错 [N]
"""
import difflib
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    path = sys.argv[1] if os.path.isabs(sys.argv[1]) else os.path.join(ROOT, sys.argv[1])
    cat = sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    shown = 0
    for pe in d["per_entry"]:
        if cat not in pe["cats"] or shown >= n:
            continue
        rid = pe["id"]
        # 找回原文
        src = None
        for cand in (ROOT + "/eval/night4_results_baseline.json",):
            if src is None:
                with open(cand, encoding="utf-8") as f:
                    dd = json.load(f)
                src = {r["id"]: r for r in dd["results"]}
        r = src[rid]
        got = r.get("udkundoku_kakikudashi_norm", "")
        exp = r.get("expected_kakikudashi", "").replace("\n", "")
        shown += 1
        print("%s" % rid)
        sm = difflib.SequenceMatcher(a=got, b=exp)
        cnt = 0
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal" or cnt >= 3:
                continue
            print("   …%s❮%s→%s❯%s…" % (got[max(0, i1 - 8):i1], got[i1:i2][:14],
                                          exp[j1:j2][:14], exp[j2:j2 + 8]))
            cnt += 1


if __name__ == "__main__":
    main()
