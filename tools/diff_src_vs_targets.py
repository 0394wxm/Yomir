# -*- coding: utf-8 -*-
"""diff_src_vs_targets.py — 对照源表与语料候选，找出漏收的高频词与收录的低价值词。"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def main():
    src = {}
    for line in io.open(os.path.join(ROOT, "eval", "lexicon_extra_src.txt"), encoding="utf-8"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        f = s.split("\t")
        src[f[0]] = f[3]

    targets = {}
    for line in io.open(os.path.join(ROOT, "eval", "lexicon_targets.txt"), encoding="utf-8"):
        f = line.rstrip("\n").split("\t")
        if len(f) >= 3:
            targets[f[0]] = int(f[1])

    missing = [(w, c) for w, c in sorted(targets.items(), key=lambda kv: -kv[1])
               if w not in src][:40]
    print("收录 %d 条；候选池 %d 条" % (len(src), len(targets)))
    print("\n=== 未收录的高频候选（前 40） ===")
    for w, c in missing:
        print("  %s  %d  len=%d" % (w, c, len(w)))
    low = sorted(((targets.get(w, 0), w, k) for w, k in src.items()))[:30]
    print("\n=== 已收录但语料频次较低（前 30） ===")
    for c, w, k in low:
        print("  %s  %d  kind=%s" % (w, c, k))


if __name__ == "__main__":
    main()
