# -*- coding: utf-8 -*-
"""night68_mine.py — N68 第一步「解剖」：Rule J 候选挖掘（Night 64 方法论，照抄 night64_mine.py）。

基线 = eval/night67_results_8165.json（⑬补丁后全链真机归档，8165 条 0 error，
got 字段即 J 将看到的链尾文本——F/G/H/I 已跑完）。

任务书重点切面：
  * 子部 shibu02 长句段（N62 avgDist 24.691，全库最肥）；
  * [4000:7908) 段（Rule I 首次重跑后仍有残留）；
  * paren 新增 257 段（[7908:]）；
  * D14 拒案表重测证据（ごとし系 / 莫系 / ことなかれ系——用真实词形+护栏重测的前置计数）。
不重复挖已覆盖/已拒绝目标（ALREADY / REJECTED / _HANDLED_KANA，逐条注明）。
只读；输出 eval/night68_mine.json / night68_mine.txt。
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

# 汉字目标：已被 D/E/F/G/H/I 规则覆盖（护栏字）——不再作为挖掘对象
ALREADY = set("皆既旣猶豈唯亦何可之又所以謂相復只須蓋焉如夫惟毋")
# 已逐条定性「不可做/拒绝」的字（N14(D14)/N17/N55/N58 报告；ごとし/莫 按 N68 任务书重测）
REJECTED = set("冰弦")
# 假名串目标：已被既有规则处理或已拒绝/已翻案的 kana
_HANDLED_KANA = {
    "これ", "また", "それ", "ゆゑん", "いはゆる", "たがいに",
    "みな", "すでに", "なお", "あに", "ただ", "いかん",
    "べし", "べく", "べからず", "ことなかれ", "なかれ", "ごとし", "ごとく", "ごとき",
    "ゆえ", "ために", "べき", "べから", "のみ", "もの", "とき", "ところ",
    "けだし", "いずくんぞ", "もし", "なかれ",
}

THRESH_DELTA = 4  # exp-got 计数差进榜阈值（paren/长句字符稀，N58 的 5 会漏）


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


def section_of(url):
    m = re.search(r"kanbun\.info/([a-z0-9_]+)/", (url or "").lower())
    return m.group(1) if m else "?"


def main():
    doc = json.load(open(os.path.join(EV, "night67_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    # results 与 golden 同序断言（段切分的下标口径依赖它）
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序: %s vs %s" % (i, r["id"], g["id"])
    assert len(rows) == 8165, "基线行数 %d != 8165" % len(rows)

    seg_3908 = rows[4000:7908]
    seg_257 = rows[7908:]
    seg_shibu02 = [r for r in rows if section_of(r.get("source_url", "")) == "shibu02"]
    print("全库有效 %d 条 | [4000:7908) %d | paren[7908:] %d | shibu02 %d" % (
        len(rows), len(seg_3908), len(seg_257), len(seg_shibu02)), flush=True)

    def charcount(rs):
        e, g = collections.Counter(), collections.Counter()
        for r in rs:
            e.update(norm(r["expected_kakikudashi"]))
            g.update(norm(r["udkundoku_kakikudashi"]))
        return e, g

    lines = []

    # ---- A. 字符 delta：四个切面 ----
    def char_delta(rs, tag, thresh):
        e, g = charcount(rs)
        cand = []
        for c in set(e) | set(g):
            if not is_kanji(c):
                continue
            ec, gc = e.get(c, 0), g.get(c, 0)
            if ec >= thresh and ec > gc:
                cand.append({"char": c, "exp": ec, "got": gc, "delta": ec - gc})
        cand.sort(key=lambda x: -x["delta"])
        lines.append("=== A. %s 字符 delta（exp>=%d 且 exp>got，n=%d）===" % (tag, thresh, len(rs)))
        for r in cand[:40]:
            tag2 = ""
            if r["char"] in ALREADY:
                tag2 = "【已覆盖】"
            elif r["char"] in REJECTED:
                tag2 = "【已拒绝】"
            lines.append("  %-2s exp %4d got %4d Δ %5d %s" % (
                r["char"], r["exp"], r["got"], r["delta"], tag2))
        lines.append("")
        return cand[:40]

    cd_shibu02 = char_delta(seg_shibu02, "shibu02 长句段", THRESH_DELTA)
    cd_3908 = char_delta(seg_3908, "[4000:7908)", THRESH_DELTA)
    cd_257 = char_delta(seg_257, "paren 新增 257", THRESH_DELTA)
    cd_all = char_delta(rows, "全 8165", 8)

    # ---- B. 假名串 delta：got ≥5 次 且 exp ≤ got/4 ----
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
        lines.append("=== B. %s 假名串 delta（got>=5 且 exp<=got/4，按 got 降序，top 30）===" % tag)
        for r in cand[:30]:
            tag2 = "【已覆盖/已拒绝】" if r["kana"] in _HANDLED_KANA else ""
            lines.append("  %-12s got %4d exp %3d %s" % (r["kana"], r["got"], r["exp"], tag2))
            for ex in r["example"][:1]:
                lines.append("      %s" % ex["id"])
                lines.append("        got: %s" % ex["got"])
                lines.append("        exp: %s" % ex["exp"])
        lines.append("")
        return cand

    kd_shibu02 = kana_delta(seg_shibu02, "shibu02")
    kd_3908 = kana_delta(seg_3908, "[4000:7908)")
    kd_257 = kana_delta(seg_257, "paren 257")
    kd_all = kana_delta(rows, "全 8165")

    # ---- C. SHINJITAI 1:1 扫描（night64_mine.py 同款，现表 246 对）----
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
    exp_all, got_all = charcount(rows)
    shin_cand = []
    lines.append("=== C. SHINJITAI 1:1 候选（count>=2、表中无、exp 全库写旧形 0 次 & got>=2）===")
    for (g, e), n in pair_cnt.most_common():
        if n < 2 or g in SHINJITAI_MAP:
            continue
        exp_old = exp_all.get(g, 0)
        got_old = got_all.get(g, 0)
        ok = exp_old == 0 and got_old >= 2
        shin_cand.append({"old": g, "new": e, "align_cnt": n,
                          "exp_old": exp_old, "got_old": got_old, "ok": ok})
        lines.append("  %s→%s %4d | exp旧%d got旧%d %s" % (
            g, e, n, exp_old, got_old, "✅收" if ok else "（不收）"))
    lines.append("")

    # ---- D. D14 拒案表重测证据（真实词形计数 + 样例）----
    lines.append("=== D. D14 拒案表重测前置计数（任务书：真实词形+护栏重测）===")
    d14 = {}
    # ごとし系：D14 拒（护栏下 0 改写）。现在 I 已覆盖 もし→如し；重测 ごとし/ごとく/ごとき 三个词形
    for kana in ("ごとし", "ごとく", "ごとき"):
        gc = sum(1 for r in rows if kana in norm(r["udkundoku_kakikudashi"]))
        ec = sum(1 for r in rows if kana in norm(r["expected_kakikudashi"]))
        guard = sum(1 for r in rows if kana in norm(r["udkundoku_kakikudashi"])
                    and "如" in norm(r["hakubun"]))
        d14["kana_" + kana] = {"got": gc, "exp": ec, "got_with_guard": guard}
        lines.append("  %-6s got %3d exp %3d | got∧白文含如 %3d" % (kana, gc, ec, guard))
    # 莫系：D14 拒（词级判断方向不明）、N58 拒 ことなかれ→莫かれ（exp 混写）。列全部莫行样例
    mo_rows = [(r["id"], norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"]))
               for r in rows if "莫" in norm(r["expected_kakikudashi"])]
    d14["mo_rows_n"] = len(mo_rows)
    lines.append("  莫 exp 行数 %d（got 侧写法分布与样例）：" % len(mo_rows))
    mo_got = collections.Counter()
    for _id, got, exp in mo_rows:
        key = "".join(c for c in got if not is_kanji(c))[:8] or got[:8]
        mo_got[key] += 1
    for k, n in mo_got.most_common(12):
        lines.append("      got 假名形态 %-8s x%d" % (k, n))
    for _id, got, exp in mo_rows[:8]:
        lines.append("      %s" % _id)
        lines.append("        got: %s" % got[:70])
        lines.append("        exp: %s" % exp[:70])
    # ことなかれ：I 之后 got 变 こと毋かれ；exp 侧形态分布复查
    knc = [(r["id"], norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"]))
           for r in rows if "ことなかれ" in norm(r["expected_kakikudashi"])
           or "こと毋かれ" in norm(r["udkundoku_kakikudashi"])]
    d14["kotonakare_n"] = len(knc)
    lines.append("  ことなかれ 相关行 %d：" % len(knc))
    for _id, got, exp in knc[:6]:
        lines.append("      %s" % _id)
        lines.append("        got: %s" % got[:70])
        lines.append("        exp: %s" % exp[:70])

    out = {"n_all": len(rows), "n_3908": len(seg_3908), "n_257": len(seg_257),
           "n_shibu02": len(seg_shibu02),
           "char_delta_shibu02": cd_shibu02, "char_delta_3908": cd_3908,
           "char_delta_257": cd_257, "char_delta_all": cd_all,
           "kana_delta_shibu02": kd_shibu02, "kana_delta_3908": kd_3908,
           "kana_delta_257": kd_257, "kana_delta_all": kd_all,
           "shinjitai": shin_cand, "d14_retest": d14}
    json.dump(out, open(os.path.join(EV, "night68_mine.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    txt = "\n".join(lines)
    open(os.path.join(EV, "night68_mine.txt"), "w", encoding="utf-8",
         newline="\n").write(txt + "\n")
    print(txt, flush=True)
    print("\nwritten: eval/night68_mine.json / night68_mine.txt", flush=True)


if __name__ == "__main__":
    main()
