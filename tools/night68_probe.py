# -*- coding: utf-8 -*-
"""night68_probe.py — N68 第二步：候选取证（照抄 night64_probe.py 骨架 + D14 拒案重测精查）。

  A. SHINJITAI 第二遍「计数判据」（N58/N64 教训：difflib 1:1 块会漏多字对齐里的对）：
     全部汉字（不在表中）exp 全库写 0 次 && got 全库 >=2 次 → 候选；
     目标形 = 等长替换块逐位多数票；再核 exp 全库写过新形 >=1 次。
  B. kana 候选精查（D14 教训：词形按 expected 真实形态；护栏按白文实际用字分工）：
     * ごとし/ごとき/ごとく：got 行按白文护栏（如/若/其他）拆分，exp 目标词形逐格计数
       （漢詩段白文写 若 时 exp 写 若し——D14 当年只试了 如 一个目标）；
     * もし 残量（Rule I 之后仍有 44+25 行）：白文含若时 exp 写 若し → 候选 もし→若し；
     * ため：got ため/がため 计数、exp 目标分布（為に/為/…）、白文含為 命中数；
     * 莫：白文含莫的行，got 侧写法 × exp 侧莫词形交叉计数（D14「词级判断」重测）；
     * べき：核 F 的可し/可く 是否漏了 可き（完族检查）。
只读；输出 eval/night68_probe.json / night68_probe.txt。
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
sys.path.insert(0, ROOT)
from backend.kundoku_rules import SHINJITAI_MAP  # noqa: E402


def norm(s):
    return re.sub(r"\s+", "", s or "")


def is_kanji(c):
    return bool(c) and ("\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf")


def main():
    doc = json.load(open(os.path.join(EV, "night67_results_8165.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    exp_all = collections.Counter()
    got_all = collections.Counter()
    for r in rows:
        exp_all.update(norm(r["expected_kakikudashi"]))
        got_all.update(norm(r["udkundoku_kakikudashi"]))
    lines = []

    # ---- A. SHINJITAI 计数判据 + 多数票定目标形 ----
    votes = collections.defaultdict(collections.Counter)  # old -> Counter(target)
    for r in rows:
        got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        sm = SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op == "equal":
                continue
            g, e = got[a1:a2], exp[b1:b2]
            if len(g) == len(e):  # 等长替换块内逐位取 1:1（多字块也不漏）
                for gc, ec in zip(g, e):
                    if is_kanji(gc) and is_kanji(ec):
                        votes[gc][ec] += 1
    shin2 = []
    for c in set(list(got_all) + list(exp_all)):
        if not is_kanji(c) or c in SHINJITAI_MAP:
            continue
        if exp_all.get(c, 0) == 0 and got_all.get(c, 0) >= 2:
            vc = votes.get(c)
            tgt, n = vc.most_common(1)[0] if vc else (None, 0)
            exp_new = exp_all.get(tgt, 0) if tgt else 0
            shin2.append({"old": c, "new": tgt, "vote": n, "got_old": got_all[c],
                          "exp_new_count": exp_new,
                          "accept": bool(tgt) and exp_new >= 1,
                          "all_votes": vc.most_common(3) if vc else []})
    shin2.sort(key=lambda x: -x["got_old"])
    lines.append("=== A. SHINJITAI 计数判据（exp 旧形全库 0 次 & got>=2、多数票、exp 新形>=1）===")
    for x in shin2:
        mark = "✅收" if x["accept"] else "（不收：exp 未写过新形）"
        lines.append("  %s→%s vote %d/%d | exp新形 %d | 全票 %s %s" % (
            x["old"], x["new"], x["vote"], x["got_old"], x["exp_new_count"],
            " ".join("%s:%d" % kv for kv in x["all_votes"]), mark))

    # ---- B1. ごとし系：按白文护栏拆目标 ----
    lines.append("\n=== B1. ごとし系按白文护栏拆分（got∧kana 的行里：白文含如/若/两有/两无；exp 目标词形计数）===")
    gotokugatu = {}
    for kana in ("ごとし", "ごとき", "ごとく"):
        sub = [r for r in rows if kana in norm(r["udkundoku_kakikudashi"])]
        buckets = {"如のみ": [], "若のみ": [], "如若両有": [], "両無": []}
        for r in sub:
            hb = norm(r["hakubun"])
            has_jo, has_nyo = "若" in hb, "如" in hb
            if has_jo and has_nyo:
                buckets["如若両有"].append(r)
            elif has_nyo:
                buckets["如のみ"].append(r)
            elif has_jo:
                buckets["若のみ"].append(r)
            else:
                buckets["両無"].append(r)
        exp_targets = collections.Counter()
        for t in ("如し", "如き", "如く", "若し", "若き", "若く"):
            exp_targets[t] = sum(norm(r["expected_kakikudashi"]).count(t) for r in sub)
        gotokugatu[kana] = {"got_rows": len(sub),
                            "buckets": {k: len(v) for k, v in buckets.items()},
                            "exp_targets": dict(exp_targets)}
        lines.append("  %s got行 %3d | 如のみ %3d 若のみ %3d 両有 %2d 両無 %2d | exp词形 %s" % (
            kana, len(sub), len(buckets["如のみ"]), len(buckets["若のみ"]),
            len(buckets["如若両有"]), len(buckets["両無"]), dict(exp_targets)))
        for bk, rs in buckets.items():
            for r in rs[:2]:
                lines.append("      [%s] %s | got: %s" % (bk, r["id"], norm(r["udkundoku_kakikudashi"])[:52]))
                lines.append("      %s | exp: %s" % (" " * (len(bk) + len(r["id"]) + 4),
                                                     norm(r["expected_kakikudashi"])[:52]))
    # 长词检查：ことごとく 等
    for w in ("ことごとく", "ことごとし", "ことごとき", "ごとくは", "おのごとし"):
        n = sum(norm(r["udkundoku_kakikudashi"]).count(w) for r in rows)
        lines.append("  [长词检查] got 侧「%s」 %d 次" % (w, n))

    # ---- B2. もし 残量（I 之后）：白文含若 → exp 若し？ ----
    lines.append("\n=== B2. もし 残量（got 含もし，I 只转了白文含如的行）===")
    mo_sub = [r for r in rows if "もし" in norm(r["udkundoku_kakikudashi"])]
    mo_jo = [r for r in mo_sub if "若" in norm(r["hakubun"])]
    mo_jo_exp_wakushi = [r for r in mo_jo if "若し" in norm(r["expected_kakikudashi"])]
    lines.append("  got もし行 %d | 白文含若 %d | 其中 exp 写若し %d" % (
        len(mo_sub), len(mo_jo), len(mo_jo_exp_wakushi)))
    for r in mo_jo_exp_wakushi[:6]:
        lines.append("      %s | got: %s" % (r["id"], norm(r["udkundoku_kakikudashi"])[:52]))
        lines.append("      %s | exp: %s" % (" " * len(r["id"]), norm(r["expected_kakikudashi"])[:52]))

    # ---- B3. ため：词形与目标分布 ----
    lines.append("\n=== B3. ため（exp 目标分布 / 白文含為 命中）===")
    tame_rows = [r for r in rows if "ため" in norm(r["udkundoku_kakikudashi"])]
    gatame = [r for r in tame_rows if "がため" in norm(r["udkundoku_kakikudashi"])]
    tame_exp = collections.Counter()
    for r in tame_rows:
        e = norm(r["expected_kakikudashi"])
        for t in ("為に", "為の", "為す", "為る", "為り", "為れ", "為ん", "為し"):
            if t in e:
                tame_exp[t] += 1
    tame_guard = [r for r in tame_rows if "為" in norm(r["hakubun"])]
    gatame_exp_nini = [r for r in gatame if "為に" in norm(r["expected_kakikudashi"])]
    lines.append("  got ため行 %d（うち がため %d） | 白文含為 %d | がため∧exp写為に %d | exp 目标 %s" % (
        len(tame_rows), len(gatame), len(tame_guard), len(gatame_exp_nini), dict(tame_exp)))
    for r in gatame_exp_nini[:5]:
        lines.append("      %s | got: %s" % (r["id"], norm(r["udkundoku_kakikudashi"])[:52]))
        lines.append("      %s | exp: %s" % (" " * len(r["id"]), norm(r["expected_kakikudashi"])[:52]))
    non_nini = [r for r in gatame if "為に" not in norm(r["expected_kakikudashi"])]
    lines.append("  がため行中 exp 不写為に的 %d 行（变差风险样例）：" % len(non_nini))
    for r in non_nini[:5]:
        lines.append("      %s | got: %s" % (r["id"], norm(r["udkundoku_kakikudashi"])[:52]))
        lines.append("      %s | exp: %s" % (" " * len(r["id"]), norm(r["expected_kakikudashi"])[:52]))

    # ---- B4. 莫：白文含莫的行，got 写法 × exp 词形 ----
    lines.append("\n=== B4. 莫（白文含莫 行的 got 写法 × exp 词形；D14 词级判断重测）===")
    mo_hb = [r for r in rows if "莫" in norm(r["hakubun"])]
    lines.append("  白文含莫 %d 行" % len(mo_hb))
    exp_mo_form = collections.Counter()
    cross = collections.Counter()
    for r in mo_hb:
        got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        form = None
        for t in ("莫かれ", "莫き", "莫し", "莫から", "莫く", "莫ら"):
            if t in exp:
                form = t
                break
        exp_mo_form[form or "(莫のない書き方)"] += 1
        gotmark = ("ことなく" if "ことなく" in got else
                   "なかれ" if "なかれ" in got else
                   "毋かれ" if "毋かれ" in got else
                   "なく" if "なく" in got else "(その他)")
        cross[(gotmark, form or "(無)")] += 1
    lines.append("  exp 词形分布：%s" % dict(exp_mo_form))
    lines.append("  got 写法 × exp 词形（top 12）：")
    for (gm, ef), n in cross.most_common(12):
        lines.append("      got %-8s × exp %-10s : %d" % (gm, ef, n))
    cand_a = [r for r in mo_hb if "ことなく" in norm(r["udkundoku_kakikudashi"])
              and "莫き" in norm(r["expected_kakikudashi"])]
    cand_b = [r for r in mo_hb if "ことなく" in norm(r["udkundoku_kakikudashi"])
              and "莫き" not in norm(r["expected_kakikudashi"])]
    lines.append("  候选 ことなく→莫き（guard 莫）：exp 写莫き %d 行 / 不写 %d 行" % (len(cand_a), len(cand_b)))
    for r in (cand_a[:3] + cand_b[:3]):
        lines.append("      %s | got: %s" % (r["id"], norm(r["udkundoku_kakikudashi"])[:52]))
        lines.append("      %s | exp: %s" % (" " * len(r["id"]), norm(r["expected_kakikudashi"])[:52]))

    # ---- B5. べき 完族检查（F 只收了 可し/可く）----
    lines.append("\n=== B5. べき 完族检查 ===")
    for kana, tgt in (("べき", "可き"), ("べから", "可から"), ("べかり", "可かり")):
        gc = sum(norm(r["udkundoku_kakikudashi"]).count(kana) for r in rows)
        ec = sum(norm(r["expected_kakikudashi"]).count(tgt) for r in rows)
        eg = sum(norm(r["expected_kakikudashi"]).count(kana) for r in rows)
        lines.append("  %-6s got %3d exp %3d | exp 写%s %3d" % (kana, gc, eg, tgt, ec))

    out = {"shinjitai_count": shin2, "gotokugatu": gotokugatu}
    json.dump(out, open(os.path.join(EV, "night68_probe.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    txt = "\n".join(lines)
    open(os.path.join(EV, "night68_probe.txt"), "w", encoding="utf-8",
         newline="\n").write(txt + "\n")
    print(txt, flush=True)
    print("\nwritten: eval/night68_probe.json / night68_probe.txt", flush=True)


if __name__ == "__main__":
    main()
