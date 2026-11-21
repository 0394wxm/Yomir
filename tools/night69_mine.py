# -*- coding: utf-8 -*-
"""night69_mine.py — N69 第四步「解剖」：Rule K 候选挖掘（Night 68 方法论第三遍）。

基线 = eval/night68_results_8165.json（Rule J 上线后全链真机归档，8165 条 0 error——
got 字段即 K 将看到的链尾文本，E/F/G/H/I/J 已全部跑完）。

切面：
  A. 字符 delta（四切面，阈值同 N68）——SHINJITAI 275 对后的残量验证；
  B. 假名串 delta（got>=4、exp<=got/4，比 N68 的 got>=5 更宽——第三遍只剩低频词）；
  C. Xぞ族专切：なんぞ got 行逐行取证（exp 目标字形 + 白文守り字 奚/曷/盍/何）
     ——N68 拒案（なんぞ→何ぞ 2 变差：奚んぞ/曷んぞ 三字形）的拆分前取证；
  D. SHINJITAI 1:1 扫描（275 表外残量验证）。
ALREADY/REJECTED/_HANDLED_KANA 更新到 N68 后状态（まさに/ごとし族 已收 → handled）。
只读；输出 eval/night69_mine.json / night69_mine.txt。
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

ALREADY = set("皆既旣猶豈唯亦何可之又所以謂相復只須蓋焉如夫惟毋方")
REJECTED = set("冰弦")
_HANDLED_KANA = {
    "これ", "また", "それ", "ゆゑん", "いはゆる", "たがいに",
    "みな", "すでに", "なお", "あに", "ただ", "いかん",
    "べし", "べく", "べからず", "ことなかれ", "なかれ", "ごとし", "ごとく", "ごとき",
    "ゆえ", "ために", "べき", "べから", "のみ", "もの", "とき", "ところ",
    "けだし", "いずくんぞ", "もし", "なかれ", "まさに",
}
THRESH_DELTA = 4


def norm(s):
    return re.sub(r"\s+", "", s or "")


def is_kanji(c):
    return bool(c) and ("\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf")


_KANA_RE = re.compile(r"[ぁ-ゖー]+")


def kana_runs(s):
    return _KANA_RE.findall(s)


def section_of(url):
    m = re.search(r"kanbun\.info/([a-z0-9_]+)/", (url or "").lower())
    return m.group(1) if m else "?"


def main():
    doc = json.load(open(os.path.join(EV, "night68_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序" % i
    assert len(rows) == 8165, "基线行数 %d != 8165" % len(rows)
    # 基线必须是 J 后链尾（night68 归档）
    n68 = json.load(open(os.path.join(EV, "night68_combo_changed_rows.json"), encoding="utf-8"))
    n68_ids = {c["id"] for c in n68}
    # 基线必须是 J 后链尾（night68 归档）：norm 后与 combo 的 new_text 逐字一致
    spot = next(r for r in rows if r["id"] in n68_ids)
    c0 = next(c for c in n68 if c["id"] == spot["id"])
    assert norm(c0["new_text"]) == norm(spot["udkundoku_kakikudashi"]), \
        "基线不是 night68 链尾（J 未反映）: %s" % spot["id"]

    seg_3908 = rows[4000:7908]
    seg_257 = rows[7908:]
    seg_shibu02 = [r for r in rows if section_of(r.get("source_url", "")) == "shibu02"]
    gmap = {g["id"]: g for g in golden}

    def charcount(rs):
        e, g = collections.Counter(), collections.Counter()
        for r in rs:
            e.update(norm(r["expected_kakikudashi"]))
            g.update(norm(r["udkundoku_kakikudashi"]))
        return e, g

    lines = []

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
            tag2 = "【已覆盖】" if r["char"] in ALREADY else ("【已拒绝】" if r["char"] in REJECTED else "")
            lines.append("  %-2s exp %4d got %4d Δ %5d %s" % (
                r["char"], r["exp"], r["got"], r["delta"], tag2))
        lines.append("")
        return cand[:40]

    cd_shibu02 = char_delta(seg_shibu02, "shibu02 长句段", THRESH_DELTA)
    cd_3908 = char_delta(seg_3908, "[4000:7908)", THRESH_DELTA)
    cd_257 = char_delta(seg_257, "paren 新增 257", THRESH_DELTA)
    cd_all = char_delta(rows, "全 8165", 8)

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
            if n < 4:
                break
            m = ec.get(w, 0)
            if m <= n // 4:
                cand.append({"kana": w, "got": n, "exp": m,
                             "example": [{"id": i, "got": g[:60], "exp": e[:60]}
                                         for i, g, e in examples[w]]})
        lines.append("=== B. %s 假名串 delta（got>=4 且 exp<=got/4，top 30）===" % tag)
        for r in cand[:30]:
            tag2 = "【已覆盖/已拒绝】" if r["kana"] in _HANDLED_KANA else ""
            lines.append("  %-14s got %4d exp %3d %s" % (r["kana"], r["got"], r["exp"], tag2))
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

    # ---- C. Xぞ族专切：なんぞ got 行逐行取证 ----
    lines.append("=== C. Xぞ族专切：got 含「なんぞ」的行（逐行 exp 目标 + 白文守り字）===")
    xzo_rows = []
    for r in rows:
        got = norm(r["udkundoku_kakikudashi"])
        if "なんぞ" not in got:
            continue
        exp = norm(r["expected_kakikudashi"])
        hb = norm(gmap[r["id"]]["hakubun"])
        guards = [x for x in ("奚", "曷", "盍", "何") if x in hb]
        targets = [t for t in ("奚んぞ", "奚ぞ", "曷んぞ", "曷ぞ", "盍ぞ", "何んぞ", "何ぞ") if t in exp]
        xzo_rows.append({"id": r["id"], "guards": guards, "targets": targets,
                         "got": got[:100], "exp": exp[:100]})
        lines.append("  %s 守り=%s 目標=%s" % (r["id"], "/".join(guards) or "-", "/".join(targets) or "-"))
        lines.append("      got: %s" % got[:100])
        lines.append("      exp: %s" % exp[:100])
    tcnt = collections.Counter(tuple(sorted(r["targets"])) for r in xzo_rows)
    lines.append("  目標字形組合せ計数: %s" % dict(tcnt))
    gcnt = collections.Counter(r["guards"][0] if r["guards"] else "-" for r in xzo_rows)
    lines.append("  先頭守り字計数: %s" % dict(gcnt))
    lines.append("")

    # ---- D. SHINJITAI 1:1 残量验证（275 表外）----
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
    lines.append("=== D. SHINJITAI 1:1 残量（count>=2、表中无、exp 旧形 0 次 & got>=2）===")
    for (g, e), n in pair_cnt.most_common():
        if n < 2 or g in SHINJITAI_MAP:
            continue
        exp_old = exp_all.get(g, 0)
        if exp_old > 0:
            continue
        exp_new = exp_all.get(e, 0)
        if exp_new < 1:
            continue
        shin_cand.append({"old": g, "new": e, "got": n, "exp_new": exp_new})
        lines.append("  %s→%s got %d exp新形 %d" % (g, e, n, exp_new))
    lines.append("")

    print("\n".join(lines))
    out = os.path.join(EV, "night69_mine.json")
    json.dump({"baseline": "night68_results_8165.json", "rows": len(rows),
               "char_delta_all": cd_all, "kana_delta_all": kd_all,
               "xzo_rows": xzo_rows, "xzo_target_counts": {"".join(k): v for k, v in tcnt.items()},
               "shinjitai_left": shin_cand},
              open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    txt = os.path.join(EV, "night69_mine.txt")
    open(txt, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("written:", out, txt)


if __name__ == "__main__":
    main()
