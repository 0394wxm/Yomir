# -*- coding: utf-8 -*-
"""night72_probe.py — N72 Rule L 候选行级取证（基线 night70_results_8165）。

对象（mine C/B 切面产出）：
  P1 つひに→終に（guard 終；N69 拒案 つひに→ついに 的真实词形翻案）
  P2 がため→が為に／が為／為に／為（guard 爲——N69 死因「守り為 0 命中」是搜了新字体、
     白文写旧字 爲；92/92 命中。目标字形 4 变体逐个测）
  P3 とも→と／与に（N69 拒案复核：与に 目標行的白文守り字取证）
  P4 はざる→わざる／はざるなり→わざるなり（N69 拒案复核：唯一変差行 24shihin10-4 的
     分离可能性——目標行白文字交集 ∖ 変差行白文字＝候选守り字）
  P5 いずくんぞ→安んぞ（guard 安；Rule I 焉护栏外的残量，exp 写 安んぞ——Xぞ族同型）
  P6 べからず→可らず（guard 可；H 須いず 分工后的残量）
  P7 ただ→只だ（guard 只；E 唯/I 惟 分工后的残量）
  P8 ゆえ→故に（guard 故）
  P9 はじめ→始め（guard 始）
输出 eval/night72_probe.txt（逐行证据）；guard 可能性判定（目標行白文字交集）。
"""
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")


def norm(s):
    return re.sub(r"\s+", "", s or "")


CANDS = [
    # (tag, kana, repl 候补s, guard 候补字, exp 目標候补s, 全行表示上限)
    ("P1", "つひに", ("終に", "終"), ("終",), ("終に", "終り", "終わり", "つひに"), 21),
    ("P2", "がため", ("が為に", "が為", "為に", "為"), ("爲", "為"), ("が為に", "が為", "為に", "為す", "為る", "為り", "為", "がため"), 8),
    ("P3", "とも", ("と", "与に"), ("与", "共", "與"), ("と", "与に", "共に", "とも"), 8),
    ("P4", "はざる", ("わざる",), (), ("わざる", "わざるなり", "わざるか", "わざるを", "わざら", "奪われ", "われ"), 39),
    ("P5", "いずくんぞ", ("安んぞ", "安くんぞ", "悪んぞ"), ("安", "焉", "悪", "惡"), ("安んぞ", "安くんぞ", "悪んぞ", "悪くんぞ", "悪く", "焉くんぞ", "焉んぞ", "安け", "いずくんぞ"), 40),
    ("P6", "べからず", ("可からず",), ("可", "須"), ("可からず", "可らず", "須いず", "べからず", "べからざる"), 8),
    ("P7", "ただ", ("但だ",), ("但", "只"), ("但だ", "但", "只だ", "唯だ", "惟だ", "ただ"), 26),
    ("P8", "ゆえ", ("由", "故に"), ("由", "故"), ("由り", "由る", "由って", "由", "故に", "故", "ゆえ"), 23),
    ("P9", "はじめ", ("始め",), ("始",), ("始め", "初め", "はじめ"), 30),
    ("P10", "べず", ("可ず",), ("可",), ("可ず", "可らず", "可らざる", "べず"), 21),
]


def main():
    doc = json.load(open(os.path.join(EV, "night70_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    gmap = {g["id"]: g for g in golden}
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    lines = []

    for tag, kana, repls, guards, targets, cap in CANDS:
        lines.append("=== %s %s → 目標 %s（守り候補 %s）===" % (tag, kana, "/".join(repls), "/".join(guards) or "-"))
        rws = []
        for r in rows:
            got = norm(r["udkundoku_kakikudashi"])
            if kana not in got:
                continue
            exp = norm(r["expected_kakikudashi"])
            hb = norm(gmap[r["id"]]["hakubun"])
            gs = [x for x in guards if x in hb]
            tg = [t for t in targets if t in exp]
            # kana 语境：後続 2 字（長仮名串拆分の設計用）
            j = got.find(kana)
            nxt = got[j + len(kana):j + len(kana) + 2]
            rws.append({"id": r["id"], "guards": gs, "targets": tg, "next": nxt,
                        "got": got[:96], "exp": exp[:96]})
        gcnt = collections.Counter("/".join(r["guards"]) or "-" for r in rws)
        tcnt = collections.Counter("/".join(r["targets"]) or "-" for r in rws)
        ncnt = collections.Counter(r["next"][:1] for r in rws)
        lines.append("  行数 %d | 守り: %s" % (len(rws), dict(gcnt)))
        lines.append("  exp 目標: %s" % dict(tcnt))
        lines.append("  kana 直後 1 字: %s" % dict(ncnt))
        for r in rws[:cap]:
            lines.append("  %s 守り=%s 目標=%s 後=%s" % (r["id"], "/".join(r["guards"]) or "-", "/".join(r["targets"]) or "-", r["next"]))
            lines.append("      got: %s" % r["got"])
            lines.append("      exp: %s" % r["exp"])
        # ---- guard 可能性判定：目標行白文字交集 ∖ 非目標行白文字 ----
        # 目標行 = exp 含主目標（repls[0]）的行；候補守り字 = 交集字符，且
        # 「非目標行」的白文里 0 命中 → 该守り字能把目標行全捞、非目標行全漏。
        main_t = repls[0]
        hit = [r for r in rws if main_t in r["targets"]]
        miss = [r for r in rws if main_t not in r["targets"]]
        if hit:
            inter = None
            for r in hit:
                s = set(norm(gmap[r["id"]]["hakubun"]))
                inter = s if inter is None else (inter & s)
            miss_chars = set()
            for r in miss:
                miss_chars |= set(norm(gmap[r["id"]]["hakubun"]))
            cand = sorted(c for c in (inter - miss_chars) if "\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf")
            lines.append("  [guard 判定] 目標(%s)行 %d / 非目標行 %d | 交集∖非目標=%s" % (
                main_t, len(hit), len(miss), "".join(cand) if cand else "無し（正 guard 不可達）"))
        else:
            lines.append("  [guard 判定] 主目標 %s 命中 0 行" % main_t)
        lines.append("")

    print("\n".join(lines))
    open(os.path.join(EV, "night72_probe.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("written:", os.path.join(EV, "night72_probe.txt"))


if __name__ == "__main__":
    main()
