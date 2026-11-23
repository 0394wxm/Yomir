# -*- coding: utf-8 -*-
"""night79_gap_check.py — N79: N76 §3.5 覆蓋缺口 3 条（而る後／而ち／利す）の
golden_8165 全行チェック。行数（文書頻度）と出現回数の両方を出し、
N76 の「19 例 / 8 例」の口径を確定させる。全命中行を人読用 txt に落とす。

用法: python -I tools/night79_gap_check.py
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")

WORDS = ["而る後", "而ち", "利す"]


def main():
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    out = []
    for w in WORDS:
        n_lines = 0
        n_occ = 0
        out.append("")
        out.append("######## %s" % w)
        for g in golden:
            kkd = re.sub(r"\s+", "", g.get("expected_kakikudashi", ""))
            hak = re.sub(r"\s+", "", g.get("hakubun", ""))
            k_n = kkd.count(w)
            h_n = hak.count(w)
            if k_n or h_n:
                n_lines += 1
                n_occ += k_n + h_n
                out.append("%s | occ k=%d h=%d | %s" % (g.get("id", ""), k_n, h_n, kkd[:80]))
        out.append("## %s: lines=%d occurrences=%d" % (w, n_lines, n_occ))
        print("%s: lines=%d occurrences=%d" % (w, n_lines, n_occ), flush=True)
    path = os.path.join(EV, "night79_gap_lines.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    print("written:", path, flush=True)


if __name__ == "__main__":
    main()
