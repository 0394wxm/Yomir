# -*- coding: utf-8 -*-
"""night25_pattern_scan.py — 論語特有書き下し约定的定向计数（对 got/exp 两侧）。"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATTS = [
    ("にして（而→にして 读法）", "にして"),
    ("相＋动词（相近し/相遠し）", "相[ぁ-ゖァ-ヺ一-龠]{1,4}"),
    ("こと名物化（〜こと弘からず）", "こと[ぁ-ゖァ-ヺ]{1,5}"),
    ("而して 残存（got）", "而して"),
    ("可からず（vs べからず）", "可からず"),
    ("べからず", "べからず"),
]


def load(name):
    with open(os.path.join(ROOT, "eval", name), encoding="utf-8") as f:
        return json.load(f)["results"]


def main():
    koji = load("night22_results_full.json")
    rongo = load("night23_results_rongo.json")
    print("%-28s %10s %10s %10s %10s" % ("pattern", "koji_got", "koji_exp", "rongo_got", "rongo_exp"))
    for label, pat in PATTS:
        rx = re.compile(pat)
        row = []
        for rows, field in ((koji, "udkundoku_kakikudashi"), (koji, "expected_kakikudashi"),
                            (rongo, "udkundoku_kakikudashi"), (rongo, "expected_kakikudashi")):
            n = sum(len(rx.findall(re.sub(r"\s+", "", r[field] or ""))) for r in rows)
            row.append(n)
        print("%-28s %10d %10d %10d %10d" % (label, *row))

    # got 里残存而して的 rongo 案例（Rule C' 范围外）：前置字符分布
    print("\n=== rongo got 残存而して的前置字符 ===")
    from collections import Counter
    c = Counter()
    ex = []
    for r in rongo:
        out = re.sub(r"\s+", "", r.get("udkundoku_kakikudashi") or "")
        for m in re.finditer("而して", out):
            prev = out[m.start() - 1] if m.start() > 0 else "BOS"
            cls = ("kana" if re.match(r"[ぁ-ゖァ-ヺ]", prev) else
                   ("kanji" if "\u3400" <= prev <= "\u9fff" else "punct"))
            c[cls] += 1
            if len(ex) < 8:
                s = max(0, m.start() - 8)
                ex.append("%s …%s【而して】%s…" % (r["id"], out[s:m.start()], out[m.end():m.end() + 5]))
    print(dict(c))
    for e in ex:
        print("  ", e)


if __name__ == "__main__":
    main()
