# -*- coding: utf-8 -*-
"""show_label_table.py — 打印 D5 标注表的可读版本（带对齐差异）。"""
import difflib
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    path = os.path.join(ROOT, "eval", "day5_label_50.tsv")
    rows = io.open(path, encoding="utf-8").read().strip().split("\n")[1:]
    for i, line in enumerate(rows, 1):
        p = line.split("\t")
        if len(p) < 4:
            continue
        rid, cat, got, exp = p[0], p[1], p[2], p[3]
        print("#%02d %-14s [%s]" % (i, rid, cat))
        print("   got: %s" % got)
        print("   exp: %s" % exp)
        sm = difflib.SequenceMatcher(a=got, b=exp)
        diffs = []
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            diffs.append("%s %r->%r" % (op, got[i1:i2], exp[j1:j2]))
        print("   diff: %s" % " | ".join(diffs))
        print()


if __name__ == "__main__":
    main()
