# -*- coding: utf-8 -*-
"""show_pattern_ctx.py — 展示某类助词差异块的前后文（人工抽查用）。
用法: python -X utf8 tools/show_pattern_ctx.py eval/night4_results_baseline.json <got假名> <expected假名> [N]
expected假名 传 ∅ 表示缺失。
"""
import difflib
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def kanji_only(s):
    return "".join(c for c in s if "\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf")


def main():
    path = sys.argv[1] if os.path.isabs(sys.argv[1]) else os.path.join(ROOT, sys.argv[1])
    want_g, want_e, n = sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 10
    want_e = None if want_e == "∅" else want_e
    want_g = None if want_g == "∅" else want_g
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    shown = 0
    for r in d["results"]:
        if shown >= n:
            break
        got = r.get("udkundoku_kakikudashi", "").strip().replace("\n", "")
        exp = r["expected_kakikudashi"].strip()
        if got == exp:
            continue
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=got, b=exp).get_opcodes():
            if op == "equal":
                continue
            g = got[i1:i2] if want_g is not None else None
            e = exp[j1:j2] if want_e is not None else None
            gok = (want_g is None and not got[i1:i2]) or (want_g is not None and got[i1:i2] == want_g)
            eok = (want_e is None and not exp[j1:j2]) or (want_e is not None and exp[j1:j2] == want_e)
            if gok and eok and len(got[i1:i2]) <= 2 and len(exp[j1:j2]) <= 2:
                print("%-12s %s" % (r["id"], got[max(0, i1 - 10):i1] + "❮" + got[i1:i2] + "→" + exp[j1:j2] + "❯" + exp[j2:j2 + 12]))
                shown += 1
                break


if __name__ == "__main__":
    main()
