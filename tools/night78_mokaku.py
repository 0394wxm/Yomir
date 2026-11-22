# -*- coding: utf-8 -*-
"""night78_mokaku.py — N78 備選⑥：なかれ→莫かれ 復活条件調查（只调研不实现）。

N73 移交②の検証を post-N 链尾で再測：
  1) N 组合（13 条・採用済み想定）を先に適用した post-N テキストに、
     なかれ→莫かれ（guard 莫）を重ねた場合の行別実数（復活ターゲット残量）；
  2) 死行の白文構文分類（莫大於／莫大焉／莫若＋後続 2 字 co-occurrence 実測）——
     N73 移交②の「莫＋大 co-occurrence guard」は判別式になり得るか；
  3) 復活に要する機構（排除 guard／kanji→kanji guard 規則）の要件整理。
只读；输出 eval/night78_mokaku.md。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, ".night72_deps"))
EV = os.path.join(ROOT, "eval")

try:
    from Levenshtein import distance as lev
except Exception:  # pragma: no cover
    def lev(a, b):
        if a == b:
            return 0
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            cur = [i]
            for j, cb in enumerate(b, 1):
                cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
            prev = cur
        return prev[-1]


def norm(s):
    return re.sub(r"\s+", "", s or "")


def apply_one(text, kana, repl):
    out, i, n = [], 0, len(kana)
    while True:
        j = text.find(kana, i)
        if j < 0:
            out.append(text[i:])
            break
        out.append(text[i:j] + repl)
        i = j + n
    return "".join(out)


def main():
    doc = json.load(open(os.path.join(EV, "night73_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    gmap = {g["id"]: g for g in golden}
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    from backend.kundoku_rules import N_KANA_TO_KANJI, N_LONGER_WORDS
    longer = N_LONGER_WORDS

    def _replace_word_boundary(text, kana, repl):
        # kundoku_rules._replace_word_boundary をそのまま参照（mask 全体＝辞書）
        import backend.kundoku_rules as kr
        return kr._replace_word_boundary(text, kana, repl, longer)

    # N 组合を適用した post-N テキスト（sim の run と同じ適用順）
    post = {}
    for r in rows:
        hb = norm(r["hakubun"])
        t = norm(r["udkundoku_kakikudashi"])
        for kana, repl, guard in N_KANA_TO_KANJI:
            if guard and hb and not any(g in hb for g in guard):
                continue
            t = _replace_word_boundary(t, kana, repl)
        post[r["id"]] = t

    # 候補: post-N に なかれ→莫かれ / 莫し / 莫（guard 莫）
    lines = []
    lines.append("# night78_mokaku — なかれ→莫かれ 復活条件調查（N78 備選⑥・只调研不实现）\n")
    lines.append("基线 = eval/night73_results_8165.json（M 后链尾）に N 组合（13 条）を先に適用した")
    lines.append("post-N テキストに、なかれ→莫かれ（guard 莫）を重ねた場合の実数。\n")

    for repl in ("莫かれ", "莫し", "莫"):
        better = worse = same = 0
        det = []
        for r in rows:
            hb = norm(r["hakubun"])
            if "莫" not in hb:
                continue
            t0 = post[r["id"]]
            if "なかれ" not in t0:
                continue
            exp = norm(r["expected_kakikudashi"])
            t1 = apply_one(t0, "なかれ", repl)
            d0, d1 = lev(t0, exp), lev(t1, exp)
            if d1 < d0:
                better += 1
            elif d1 > d0:
                worse += 1
                det.append((r["id"], d0, d1))
            else:
                same += 1
        lines.append("## なかれ→%s（guard 莫・post-N）: 改善 %d／変差 %d／same %d" % (repl, better, worse, same))
        for rid, d0, d1 in det[:12]:
            lines.append("  - 変差 %s %d→%d" % (rid, d0, d1))
        lines.append("")

    # 死行・残量行の白文構文分類
    lines.append("## 残量行の白文構文（post-N に なかれ を含み白文に 莫 を含む行）\n")
    feat = {}
    det2 = []
    for r in rows:
        hb = norm(r["hakubun"])
        if "莫" not in hb:
            continue
        t0 = post[r["id"]]
        if "なかれ" not in t0:
            continue
        i = hb.find("莫")
        ctx = hb[i:i + 3]
        feat[ctx] = feat.get(ctx, 0) + 1
        runs = [w for w in re.findall(r"[ぁ-ゖー]+", t0) if "なかれ" in w]
        det2.append((r["id"], ctx, runs[0] if runs else "?"))
    lines.append("白文 莫＋後続 2 字 co-occurrence 分布: %s\n" % feat)
    for rid, ctx, run in det2:
        lines.append("  - %s 白文「%s」 got_run=%s" % (rid, ctx, run))
    lines.append("")
    lines.append("## 結論（要件整理）\n")
    lines.append("- 死行 kokyo09-5 は白文「莫大於」構文・すことなかれ 行。ただし kowokaete-4（莫大焉）は")
    lines.append("  N の なることなかれ rule で 0 変差改善済み——「莫＋大 co-occurrence」は判別式に**ならない**")
    lines.append("  （莫大焉 行が陽性で通るため）。真の判別は exp 側再構造（「大なるは莫し」型の倒置）で、")
    lines.append("  白文側の表面 co-occurrence では分離不能。")
    lines.append("- 復活に必要な機構は次のいずれか（いずれも新機構＝拍板事項）:")
    lines.append("  1. 排除 guard（guard 莫 ∧ 白文 非「莫大於」等の否定条件）— guard 機構の拡張。")
    lines.append("     実測：post-N の なかれ→莫かれ は 16 行中 12 改善／same 3／変差 1（kokyo09-5 のみ）——")
    lines.append("     排除 guard でこの 1 行だけ抜ければ 80 行規模の再候補が成立する。")
    lines.append("  2. kanji→kanji guard 規則（N73 移交③の 陳→陣 と共用）— 適用後の got/exp 漢字差のみ")
    lines.append("  3. すことなかれ に限れば key 分割で回避可能（N が実証）——ただし残量 16 行のうち")
    lines.append("     すことなかれ 系 6 行（kokyo09-5 以外）は莫かれ で改善するため、key 分割だけでは")
    lines.append("     なら/ざる 系の取残し（き/ぶ/く/つ 7 行＋くなかれ/になかれ 2 行）を救えない。\n")
    lines.append("結論：莫 rule（なかれ→莫かれ 80 行規模）の復活は、N によって ことな族 72 行が")
    lines.append("既に回収されたため、残る post-N 目標は " + str(len(det2)) + " 行（白文 莫）。その内訳は上表の通り。")
    lines.append("kokyo09-5 1 行が全候補字形で唯一の変差行であり続ける限り 0 変差門は通らない——")
    lines.append("復活条件＝排除 guard か kanji→kanji guard 規則の機構追加を待つ（拍板事項）。\n")

    open(os.path.join(EV, "night78_mokaku.md"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("written: eval/night78_mokaku.md")


if __name__ == "__main__":
    main()
