# -*- coding: utf-8 -*-
"""night69_probe.py — N69 Rule K 候选行级取证（基线 night68_results_8165）。

仮名遣い族（歴史的→現代，Rule A ふ→う 同型・exp 侧源字 0 结构性）：
  K1 ひて→いて（517 行）、K2 へて→えて（246 行）、K3 はず→わず（137 行）、
  K4 はざる→わざる（39 行）、K5 へず→えず（20 行）
漢字化族：K6 いやしくも→苟くも（24 行）
Xぞ族拆分（N68 拒案 なんぞ→何ぞ 的翻案尝试）：K7 盍ぞ guard 盍、K8 奚ぞ guard 奚、K9 曷ぞ guard 曷
争议复核：K10 とも→と（exp 皆无 とも）、K11 がため→が為に（N68 R_gatame 续）、K12 つひに→ついに（exp 无目标字形）
输出 eval/night69_probe.txt。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def main():
    doc = json.load(open(os.path.join(EV, "night68_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    gmap = {g["id"]: g for g in golden}
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    lines = []

    def rows_with(w):
        return [r for r in rows if w in norm(r["udkundoku_kakikudashi"])]

    def exp_char(c):
        return sum(norm(r["expected_kakikudashi"]).count(c) for r in rows)

    def exp_rows(w):
        return sum(1 for r in rows if w in norm(r["expected_kakikudashi"]))

    def show(rs, n=4):
        for r in rs[:n]:
            g = norm(r["udkundoku_kakikudashi"])
            e = norm(r["expected_kakikudashi"])
            i = g.find("なんぞ") if "なんぞ" in g else 0
            lines.append("  %s" % r["id"])
            lines.append("    got: ...%s..." % g[max(0, i - 10):i + 30])
            lines.append("    exp: %s" % e[:70])

    # ---- 仮名遣い族：源字 exp 侧字符级计数（结构性 0 验证）----
    lines.append("=== K1-K5 仮名遣い族：源字 exp 侧字符级（结构性 0 = 0 変差保证前提）===")
    for c in ("ひ", "へ", "は"):
        lines.append("  exp 字符 %s: %d" % (c, exp_char(c)))
    lines.append("  exp 行 いて %d | えて %d | わず %d | わざる %d | えず %d" % (
        exp_rows("いて"), exp_rows("えて"), exp_rows("わず"), exp_rows("わざる"), exp_rows("えず")))
    for tag, w in (("K1 ひて", "ひて"), ("K2 へて", "へて"), ("K3 はず", "はず"),
                   ("K4 はざる", "はざる"), ("K5 へず", "へず")):
        rs = rows_with(w)
        lines.append("  %s: got %d 行" % (tag, len(rs)))
        show(rs, 3)
    lines.append("  -- 风险行：got ひて/へて/はず 且 exp 含源字 --")
    for r in rows:
        g, e = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        src = [w for w in ("ひて", "へて", "はず", "はざる", "へず") if w in g]
        if src and any(c in e for c in "ひへは"):
            lines.append("  %s src=%s | exp ひ/へ/は 含" % (r["id"], ",".join(src)))
            lines.append("    got: %s" % g[:100])
            lines.append("    exp: %s" % e[:100])
    lines.append("")

    # ---- K6 いやしくも ----
    lines.append("=== K6 いやしくも→苟くも：got 全行（守り=白文含苟）===")
    n6 = hit6 = 0
    for r in rows:
        g, e = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        if "いやしくも" not in g:
            continue
        n6 += 1
        g_hit = "苟" in norm(gmap[r["id"]]["hakubun"])
        hit6 += g_hit
        lines.append("  %s 守り苟=%s exp苟くも=%s" % (
            r["id"], g_hit, "苟くも" in e))
        lines.append("    got: %s" % g[:96])
        lines.append("    exp: %s" % e[:96])
    lines.append("  got %d 行 / 白文含苟 %d 行 / exp 苟くも %d 行" % (n6, hit6, exp_rows("苟くも")))
    lines.append("")

    # ---- K7-K9 Xぞ族 ----
    lines.append("=== K7-K9 なんぞ Xぞ族：全行守り字＋exp 目標 ===")
    multi = []
    for r in rows:
        g, e = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        if "なんぞ" not in g:
            continue
        hb = norm(gmap[r["id"]]["hakubun"])
        gs = [x for x in ("奚", "曷", "盍") if x in hb]
        if len(gs) > 1:
            multi.append((r["id"], gs))
        tg = [t for t in ("奚んぞ", "奚ぞ", "曷んぞ", "曷ぞ", "盍ぞ", "何ぞ") if t in e]
        lines.append("  %s 守り=%s 目標=%s" % (r["id"], "/".join(gs) or "-", "/".join(tg) or "-"))
    lines.append("  多守り行（順序依存チェック用）: %s" % (multi or "無し"))
    lines.append("  exp 行 盍ぞ %d | 奚ぞ %d | 曷ぞ %d | 奚んぞ %d | 曷んぞ %d" % (
        exp_rows("盍ぞ"), exp_rows("奚ぞ"), exp_rows("曷ぞ"), exp_rows("奚んぞ"), exp_rows("曷んぞ")))
    lines.append("")

    # ---- K10-K12 争议复核 ----
    lines.append("=== K10 とも→と：got %d 行 / exp 含とも %d 行（→0 は目標 と 一意の証）===" % (
        len(rows_with("とも")), exp_rows("とも")))
    show(rows_with("とも"), 3)
    lines.append("=== K11 がため→が為に：got %d 行 / exp 為に %d / exp 為 %d（混写証）===" % (
        len(rows_with("がため")), exp_rows("為に"), exp_char("為")))
    show(rows_with("がため"), 3)
    lines.append("=== K12 つひに→ついに：got %d 行 / exp ついに %d / exp 終に %d（無目標証）===" % (
        len(rows_with("つひに")), exp_rows("ついに"), exp_rows("終に")))
    show(rows_with("つひに"), 3)

    print("\n".join(lines))
    open(os.path.join(EV, "night69_probe.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("written:", os.path.join(EV, "night69_probe.txt"))


if __name__ == "__main__":
    main()
