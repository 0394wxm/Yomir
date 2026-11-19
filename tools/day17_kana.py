# -*- coding: utf-8 -*-
"""day17_kana.py — D17 第二步：候选假名→汉字 的 1:1 交叉验证（含白文护栏成本）。

对每个候选 (假名, 目标词形, 白文字)：
  A = 白文含该字 & 输出含该假名      → 可改写的潜在收益（护栏内）
  B = 白文含该字 & 输出不含假名      → 不动
  C = 白文不含该字 & 输出含该假名    → **护栏成本**（必须为 0，否则会误改）
  exp 假名数 = expected 里该假名残留（应尽量 0，说明 expected 用汉字）
  exp 汉字数 / got 汉字数

只读，输出 eval/day17_kana.json。
"""
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

# (假名, 目标词形, 白文护栏字集合, 说明)
CANDIDATES = [
    ("また",   "亦た", ("亦",),  "亦た — D14 因亦/又歧义拒绝，现用白文消歧"),
    ("また",   "又",   ("又",),  "又 — 同上，另一个方向"),
    ("ごとく", "若く", ("若",),  "若く"),
    ("ごとし", "若し", ("若",),  "若し"),
    ("ごとき", "若き", ("若",),  "若き"),
    ("べし",   "可し", ("可",),  "可し（べし系列，词形多，先看量）"),
    ("べき",   "可き", ("可",),  "可き"),
    ("べく",   "可く", ("可",),  "可く"),
    ("べから", "可から", ("可",), "可から（べからず）"),
    ("なし",   "莫し", ("莫",),  "莫し"),
    ("なし",   "無し", ("無",),  "無し（对照：这个引擎已在写）"),
    ("ともに", "与に", ("与",),  "与に"),
    ("いかん", "如何", ("何",),  "如何（いかん）"),
]


def norm(s):
    return re.sub(r"\s+", "", s or "")


def main():
    doc = json.load(open(os.path.join(EV, "day16_results_2000.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    print("样本 %d 条\n" % len(rows), flush=True)

    hdr = "%-6s %-7s %-4s %7s %7s %7s %7s %7s %8s"
    print(hdr % ("假名", "词形", "护栏", "A有字有", "B有字无", "C无字有", "exp假名",
                 "exp汉字", "got汉字"), flush=True)
    out = []
    for kana, repl, guard, note in CANDIDATES:
        A = B = C = 0
        exp_kana = got_kana = exp_kanji = got_kanji = 0
        for r in rows:
            hb = norm(r["hakubun"])
            exp = norm(r["expected_kakikudashi"])
            got = norm(r["udkundoku_kakikudashi"])
            has_guard = any(g in hb for g in guard)
            has_kana = kana in got
            if has_guard and has_kana:
                A += 1
            elif has_guard and not has_kana:
                B += 1
            elif not has_guard and has_kana:
                C += 1
            exp_kana += exp.count(kana)
            got_kana += got.count(kana)
            exp_kanji += exp.count(repl[0])
            got_kanji += got.count(repl[0])
        print(hdr % (kana, repl, "+".join(guard), A, B, C, exp_kana, exp_kanji, got_kanji),
              flush=True)
        out.append({"kana": kana, "repl": repl, "guard": guard, "note": note,
                    "A": A, "B": B, "C": C, "exp_kana": exp_kana, "got_kana": got_kana,
                    "exp_kanji": exp_kanji, "got_kanji": got_kanji})

    print("\nA/C 的含义：A 是护栏内可改写的条目数；C 必须为 0（白文无字却改写=误改）", flush=True)
    json.dump({"n": len(rows), "candidates": out},
              open(os.path.join(EV, "day17_kana.json"), "w",
                   encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written: eval/day17_kana.json", flush=True)


if __name__ == "__main__":
    main()
