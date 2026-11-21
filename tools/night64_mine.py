# -*- coding: utf-8 -*-
"""night64_mine.py — N64 第一步「解剖」：golden_4000 全量（基线 = night60 真机归档，全链）挖 Rule I 候选。

方法论 = Night 22 / D14 / N55 / N58（沿用 night58_mine.py 骨架，语料换成 4000 条）：
  A. 字符 delta：新增 1000 条（golden_4000[3000:]，toushisen 漢詩短句）exp-got 汉字计数，
     与全 4000 对照；再对全 4000 单独排一遍（长句段的字不因短句阈值漏掉）。
  B. 假名串 delta：got 侧假名连续段（≥2 字）计数 vs exp 侧同串计数——got 远多于 exp 的串
     是 kana→kanji 候选的直接信号（Rule D 的 これ、F/G/H 的 また 系都是这么发现的）。
  C. SHINJITAI 1:1 扫描（night58_sim.py 同款）：difflib 1:1 汉字→汉字替换 count>=2、
     不在表中，判据 = exp 全库写旧形 0 次。
不重复挖已覆盖/已拒绝的目标（ALREADY / REJECTED / _HANDLED_KANA，逐条注明）。
只读；输出 eval/night64_mine.json / night64_mine.txt。
"""
import collections
import json
import os
import re
import sys
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

# 汉字目标：已被 E/F/G/H/D 规则覆盖（护栏字）——不再作为挖掘对象
ALREADY = set("皆既旣猶豈唯亦何可之又所以謂相復只須")
# 已逐条定性「不可做/拒绝」的字（N14/N17/N55/N58 报告）
REJECTED = set("勿焉如若莫為不与冰弦")
# 假名串目标：已被既有规则处理或已拒绝的 kana
_HANDLED_KANA = {
    "これ", "また", "それ", "ゆゑん", "いはゆる", "たがいに",
    "みな", "すでに", "なお", "あに", "ただ", "いかん",
    "べし", "べく", "べからず", "ことなかれ", "なかれ", "ごとし", "ごとく", "ごとき",
    "ゆえ", "ために", "べき", "べから", "のみ", "もの", "とき", "ところ",
}

THRESH_DELTA = 4  # exp-got 计数差进榜阈值（漢詩短句字符稀，N58 的 5 会漏）


def norm(s):
    return re.sub(r"\s+", "", s or "")


def is_kanji(c):
    return bool(c) and ("\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf")


_KANA_RE = re.compile(r"[ぁ-ゖー]+")


def kana_runs(s):
    return _KANA_RE.findall(s)


def lev(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def main():
    doc = json.load(open(os.path.join(EV, "night60_results_4000.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    golden_ids_new = {it["id"] for it in json.load(
        open(os.path.join(EV, "golden_4000.json"), encoding="utf-8"))[3000:]}
    rows_new = [r for r in rows if r["id"] in golden_ids_new]
    rows_old = [r for r in rows if r["id"] not in golden_ids_new]
    assert len(rows_new) >= 990, "新增段切分异常: %d" % len(rows_new)
    print("全库有效 %d 条 | 新增段(toushisen1000) %d / 前 3000 %d" % (
        len(rows), len(rows_new), len(rows_old)), flush=True)

    def charcount(rs):
        e, g = collections.Counter(), collections.Counter()
        for r in rs:
            e.update(norm(r["expected_kakikudashi"]))
            g.update(norm(r["udkundoku_kakikudashi"]))
        return e, g

    exp_n, got_n = charcount(rows_new)
    exp_o, got_o = charcount(rows_old)
    exp_a, got_a = charcount(rows)

    lines = []

    # ---- A. 字符 delta：新增 1000 + 全 4000 两个口径 ----
    def char_delta(rows_main, rows_rest, tag, thresh):
        e, g = charcount(rows_main)
        if rows_rest:
            re_, rg_ = charcount(rows_rest)
        else:
            re_, rg_ = collections.Counter(), collections.Counter()
        cand = []
        for c in set(e) | set(g):
            if not is_kanji(c):
                continue
            ec, gc = e.get(c, 0), g.get(c, 0)
            if ec >= thresh and ec > gc:
                cand.append({"char": c, "exp": ec, "got": gc, "delta": ec - gc})
        cand.sort(key=lambda x: -x["delta"])
        lines.append("=== A. %s 字符 delta（exp>=%d 且 exp>got）===" % (tag, thresh))
        for r in cand[:50]:
            tag2 = ""
            if r["char"] in ALREADY:
                tag2 = "【已覆盖】"
            elif r["char"] in REJECTED:
                tag2 = "【已拒绝/不可做】"
            lines.append("  %-2s exp %4d got %4d Δ %5d %s" % (
                r["char"], r["exp"], r["got"], r["delta"], tag2))
        return cand[:50]

    cand_new = char_delta(rows_new, rows_old, "新增 1000（toushisen）", THRESH_DELTA)
    lines.append("")
    cand_all = char_delta(rows, [], "全 4000", 8)

    # ---- B. 假名串 delta：got ≥5 次 且 exp=0（或 exp<<got）----
    def kana_delta(rs, tag):
        gc, ec = collections.Counter(), collections.Counter()
        examples = collections.defaultdict(list)
        for r in rs:
            got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
            for w in kana_runs(got):
                if len(w) >= 2:
                    gc[w] += 1
                    if len(examples[w]) < 2:
                        examples[w].append((r["id"], got, exp))
            for w in set(kana_runs(exp)):
                if len(w) >= 2:
                    ec[w] += 1
        cand = []
        for w, n in gc.most_common(400):
            if n < 5:
                break
            m = ec.get(w, 0)
            if m <= n // 4:  # exp 出现次数 ≤ got 的 1/4（含 0）→ 引擎系统性多写
                cand.append({"kana": w, "got": n, "exp": m,
                             "example": [{"id": i, "got": g[:60], "exp": e[:60]}
                                         for i, g, e in examples[w]]})
        lines.append("\n=== B. %s 假名串 delta（got>=5 且 exp<=got/4，按 got 降序，top 40）===" % tag)
        for r in cand[:40]:
            tag2 = "【已覆盖/已拒绝】" if r["kana"] in _HANDLED_KANA else ""
            lines.append("  %-10s got %4d exp %3d %s" % (r["kana"], r["got"], r["exp"], tag2))
            for ex in r["example"][:1]:
                lines.append("      %s" % ex["id"])
                lines.append("        got: %s" % ex["got"])
                lines.append("        exp: %s" % ex["exp"])
        return cand

    kana_cand_all = kana_delta(rows, "全 4000")
    kana_cand_new = kana_delta(rows_new, "新增 1000")

    # ---- C. SHINJITAI 1:1 扫描（night58_sim.py 同款判据）----
    sys.path.insert(0, ROOT)
    from backend.kundoku_rules import SHINJITAI_MAP  # noqa: E402
    pair_cnt = collections.Counter()
    for r in rows:
        got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        sm = SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op == "equal":
                continue
            g, e = got[a1:a2], exp[b1:b2]
            if len(g) == 1 and len(e) == 1 and is_kanji(g) and is_kanji(e) \
                    and SHINJITAI_MAP.get(g) != e:
                pair_cnt[(g, e)] += 1
    shin_cand = []
    lines.append("\n=== C. SHINJITAI 1:1 候选（count>=2、表中无、exp 全库写旧形 0 次）===")
    for (g, e), n in pair_cnt.most_common():
        if n < 2 or g in SHINJITAI_MAP:
            continue
        exp_old = exp_a.get(g, 0)
        got_old = got_a.get(g, 0)
        ok = exp_old == 0 and got_old >= 2
        shin_cand.append({"old": g, "new": e, "align_cnt": n,
                          "exp_old": exp_old, "got_old": got_old, "ok": ok})
        lines.append("  %s→%s %4d | exp旧%d got旧%d %s" % (
            g, e, n, exp_old, got_old, "✅收" if ok else "（不收）"))

    out = {"n_all": len(rows), "n_new": len(rows_new),
           "char_delta_new": cand_new, "char_delta_all": cand_all,
           "kana_delta_all": kana_cand_all, "kana_delta_new": kana_cand_new,
           "shinjitai": shin_cand}
    json.dump(out, open(os.path.join(EV, "night64_mine.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    txt = "\n".join(lines)
    open(os.path.join(EV, "night64_mine.txt"), "w", encoding="utf-8",
         newline="\n").write(txt + "\n")
    print(txt, flush=True)
    print("\nwritten: eval/night64_mine.json / night64_mine.txt", flush=True)


if __name__ == "__main__":
    main()
