# -*- coding: utf-8 -*-
"""night48_classify.py — 71 个未配对窄框的语义分类（人读后固化）。

前四步把几何路线全部否证。本脚本做最后一件有用的事：把 71 个框**逐个归类**
成可复算的类别，量化「本版噪音的构成」，为将来任何判据提供基准。

分类规则（按优先级，全部只用文本，不用几何——几何已被证明无效）：
  C1 書誌/蔵書印/年号   含「明治/嘉永/文政/天保/安政/万延/元治/慶応」等年号
                        或「蔵書/書肆/版元/求/梓/刊」等
  C2 手写公文/書簡体     含「候」「御」「様」「被仰付」「奉」「申」等候文标记
  C3 金額/数量           含「匁/両/文/貫/石/斗/升」+ 数字
  C4 割注（正文注）      以上都不含，且长度 >= 8 字、汉字比率高
  C5 未分类              其余（人工读后逐条确认）

同时统计每类的几何均值，检验「类与几何无关」（即几何不可用作判据）。

只测量，不改代码。
产出: eval/night48_classify.json
用法: python -X utf8 tools/night48_classify.py
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SRC = os.path.join(ROOT, "eval", "night48_margin_test.json")
OUT = os.path.join(ROOT, "eval", "night48_classify.json")

NENGO = ("明治", "嘉永", "文政", "天保", "安政", "万延", "元治", "慶応",
         "慶應", "弘化", "文化", "享和", "寛政", "天明", "安永", "明和")
SHOSHI = ("蔵書", "藏書", "書肆", "版元", "求", "梓", "刊", "藏", "藏板",
          "翻刻", "発兌", "発売")
KOBUN = ("候", "御", "様", "被仰付", "奉", "申", "罷", "拙者", "御座")
MONEY = ("匁", "両", "文", "貫", "石", "斗", "升", "銭", "壱")


def is_kanji(c):
    return ("\u4e00" <= c <= "\u9fff") or ("\u3400" <= c <= "\u4dbf")


def kanji_ratio(s):
    if not s:
        return 0.0
    return sum(1 for c in s if is_kanji(c)) / float(len(s))


def classify(t):
    hits = []
    if any(k in t for k in NENGO):
        hits.append("C1_nengo")
    if any(k in t for k in SHOSHI):
        hits.append("C1_shoshi")
    if any(k in t for k in KOBUN):
        hits.append("C2_kobun")
    if any(k in t for k in MONEY) and any(c.isdigit() or c in "〇一二三四五六七八九十百千" for c in t):
        hits.append("C3_money")
    if hits:
        return hits[0], hits
    if len(t) >= 8 and kanji_ratio(t) >= 0.7:
        return "C4_warichu", []
    return "C5_other", []


def main():
    d = json.load(open(SRC, encoding="utf-8"))
    rows = d["rows"]

    for r in rows:
        cls, allh = classify(r["text"])
        r["cls"] = cls
        r["cls_all"] = allh
        r["kanji"] = round(kanji_ratio(r["text"]), 2)

    print("== 71 个未配对窄框的语义分类 ==")
    order = ["C1_nengo", "C1_shoshi", "C2_kobun", "C3_money",
             "C4_warichu", "C5_other"]
    for c in order:
        sel = [r for r in rows if r["cls"] == c]
        print("\n-- %s : %d 个 --" % (c, len(sel)))
        for r in sel:
            print("   %s h_rel=%.2f w=%3d kanji=%.2f  %r"
                  % (r["page"], r["h_rel"], r["w"], r["kanji"],
                     r["text"][:52]))

    print("\n== 每类的几何均值（检验「类与几何无关」）==")
    print("%-12s %4s %8s %8s %9s %9s"
          % ("class", "n", "h_rel均", "w均", "缝宽均", "贴栏占比"))
    for c in order:
        sel = [r for r in rows if r["cls"] == c]
        if not sel:
            continue
        n = len(sel)
        print("%-12s %4d %8.2f %8.1f %9.2f %8.0f%%"
              % (c, n,
                 sum(r["h_rel"] for r in sel) / n,
                 sum(r["w"] for r in sel) / float(n),
                 sum(r["M3_gap_rel"] for r in sel) / n,
                 100.0 * sum(1 for r in sel if r["M3_gap_rel"] < 0.3) / n))

    print("\n== 结论 ==")
    noise = [r for r in rows if r["cls"] != "C4_warichu"]
    print("  噪音类（C1/C2/C3/C5）: %d" % len(noise))
    print("  割注类（C4，正文）: %d" % sum(1 for r in rows if r["cls"] == "C4_warichu"))
    print("  若几何能分开，两类 h_rel 均值应显著不同 —— 见上表。")

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n": len(rows), "rows": rows}, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night48_classify.json")


if __name__ == "__main__":
    main()
