# -*- coding: utf-8 -*-
"""night73_mine.py — N73 Rule M 候选挖掘（Night 68/69/72 方法论第五遍）。

基线 = eval/night72_results_8165.json（Rule L 上线后全链真机归档，8165 条 0 error——
got 字段即 M 将看到的链尾文本，E〜L 已全部跑完）。
基线断言：results/golden 同序；L combo 行 got == night72_combo_changed_rows.new_text；
非 combo 行 got == night70 归档（L 只改 combo 行，N72 双向 0 差的再验证）。

切面：
  A. 字符 delta（SHINJITAI 275 对后的残量验证）；
  B. 假名串 delta（L 后仍剩的高频かな→漢字错失；已知活用/句法结构差标【结构】）；
  B2. opcode 词级挖（新切面）：SequenceMatcher replace 块、got 侧纯假名（>=2）×
      exp 侧汉字头 → (kana, 汉字头) 对计数——直接挖「词边界假名→漢字」型，
      守り字候补新旧字体两形并查（N72 移交①成文执行）；
  C. N72 拒案＋移交复查（とも／べからず／がため落选字形／はざる者 2 行——
      はざる者 本夜不收、只核实计数）；
  D. SHINJITAI 1:1 残量（N69/N72 结论＝0 对，再验证）。
只读；输出 eval/night73_mine.json / night73_mine.txt。
"""
import collections
import json
import os
import re
import sys
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")

ALREADY = set("皆既旣猶豈唯亦何可之又所以謂相復只須蓋焉如夫惟毋方若如苟盍奚曷")
_HANDLED_KANA = {
    "これ", "また", "それ", "ゆゑん", "いはゆる", "たがいに",
    "みな", "すでに", "なお", "あに", "ただ", "いかん",
    "べし", "べく", "べからず", "ことなかれ", "なかれ", "ごとし", "ごとく", "ごとき",
    "ゆえ", "ために", "べき", "べから", "のみ", "もの", "とき", "ところ",
    "けだし", "いずくんぞ", "もし", "まさに",
    "ひて", "へて", "はず", "へず", "いやしくも", "なんぞ",
    # N72 Rule L 已收
    "つひに", "がため", "はざるなり", "はざるを",
}
# N24/25 定性＝活用・句法结构差（規則層不可達，B 面只标注不算候选）
STRUCTURAL = {"して", "なりて", "するを", "みて", "すを", "なるを", "するは", "すは",
              "なるは", "するなり", "るか", "ぎて", "なるか", "ぶを", "せずして",
              "しての", "するの", "らを", "するか", "にたり", "つを", "ぶは",
              "なるなり", "すか", "すや", "すは"}

THRESH_DELTA = 4


def norm(s):
    return re.sub(r"\s+", "", s or "")


def is_kanji(c):
    return bool(c) and ("\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf")


_KANA_RE = re.compile(r"[ぁ-ゖー]+")
_KANA_ONLY_RE = re.compile(r"^[ぁ-ゖー]+$")


def kana_runs(s):
    return _KANA_RE.findall(s)


def section_of(url):
    m = re.search(r"kanbun\.info/([a-z0-9_]+)/", (url or "").lower())
    return m.group(1) if m else "?"


def main():
    doc = json.load(open(os.path.join(EV, "night72_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    n70 = json.load(open(os.path.join(EV, "night70_results_8165.json"), encoding="utf-8"))
    combo = json.load(open(os.path.join(EV, "night72_combo_changed_rows.json"), encoding="utf-8"))
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序" % i
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    assert len(rows) == 8165, "基线行数 %d != 8165" % len(rows)
    # ---- 基线必须是 L 后链尾（night72 归档）----
    n70_map = {r["id"]: r for r in n70["results"]}
    combo_map = {c["id"]: c for c in combo}
    for r in rows:
        nid = r["id"]
        g72 = norm(r["udkundoku_kakikudashi"])
        if nid in combo_map:
            assert g72 == norm(combo_map[nid]["new_text"]), \
                "L 链尾不一致（combo 行）: %s" % nid
        else:
            assert g72 == norm(n70_map[nid]["udkundoku_kakikudashi"]), \
                "L 链尾不一致（非 combo 行）: %s" % nid

    from backend.kundoku_rules import SHINJITAI_MAP
    old_to_new = dict(SHINJITAI_MAP)
    new_to_old = {}
    for o, n in old_to_new.items():
        new_to_old.setdefault(n, o)

    def guard_forms(g):
        """守り字 g 的新旧两形（＋本身）：N72 移交①——mine/probe 守り字候补必须
        新旧字体两形并查（白文保 旧字体/異体字）。"""
        forms = [g]
        for f in (new_to_old.get(g), old_to_new.get(g)):
            if f and f not in forms:
                forms.append(f)
        return tuple(forms)

    gmap = {g["id"]: g for g in golden}
    seg_3908 = rows[4000:7908]
    seg_257 = rows[7908:]
    seg_shibu02 = [r for r in rows if section_of(r.get("source_url", "")) == "shibu02"]

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
            tag2 = "【已覆盖】" if r["char"] in ALREADY else ""
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
                             "structural": w in STRUCTURAL,
                             "handled": w in _HANDLED_KANA,
                             "example": [{"id": i, "got": g[:60], "exp": e[:60]}
                                         for i, g, e in examples[w]]})
        lines.append("=== B. %s 假名串 delta（got>=4 且 exp<=got/4，top 30）===" % tag)
        for r in cand[:30]:
            tag2 = "【结构】" if r["structural"] else (
                "【已覆盖】" if r["handled"] else "")
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

    # ---- B2. opcode 词级挖（新切面）----
    # replace 块、got 侧纯假名（>=2 字）×exp 侧汉字头 → (kana, head) 对。
    # 对每对记录：行数、exp 头字＋尾きぬがさ（okurigana 分布）、白文守り字命中
    # （头字新旧两形并查）、非目标行守り字命中（guard 可达性粗判）。
    pair_rows = collections.defaultdict(list)
    for r in rows:
        got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        sm = SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op != "replace":
                continue
            g, e = got[a1:a2], exp[b1:b2]
            if len(g) < 2 or not _KANA_ONLY_RE.match(g):
                continue
            if not e or not is_kanji(e[0]):
                continue
            pair_rows[(g, e)].append(r["id"])

    # (kana, 汉字头) 聚合
    pair_head = collections.defaultdict(list)
    for (g, e), ids in pair_rows.items():
        pair_head[(g, e[0])].append((e, ids))

    b2_cand = []
    lines.append("=== B2. opcode 词级挖：got 纯假名 replace 块 × exp 汉字头（行数>=5，top 40）===")
    for (g, head), variants in sorted(pair_head.items(), key=lambda kv: -sum(len(v[1]) for v in kv[1])):
        total = sum(len(v[1]) for v in variants)
        if total < 5:
            break
        # 守り字头字新旧两形命中（目标行白文）
        gf = guard_forms(head)
        tgt_hits = 0
        tot_rows = set()
        for _e, ids in variants:
            tot_rows.update(ids)
        for rid in tot_rows:
            hb = norm(gmap[rid]["hakubun"])
            if any(f in hb for f in gf):
                tgt_hits += 1
        vstr = " / ".join("%s(%d)" % (v, len(ids)) for v, _ids in sorted(variants, key=lambda x: -len(x[1]))[:4])
        b2_cand.append({"kana": g, "head": head, "rows": total,
                        "guard_forms": gf, "guard_hit_rows": tgt_hits,
                        "variants": [{"exp_seg": v, "n": len(ids)} for v, ids in
                                     sorted(variants, key=lambda x: -len(x[1]))[:6]],
                        "example_id": sorted(tot_rows)[0]})
        lines.append("  %-10s → %-2s 行数 %4d 守り %s 命中 %4d/%4d | exp側: %s" % (
            g, head, total, "/".join(gf), tgt_hits, len(tot_rows), vstr))
    lines.append("")

    # ---- C. N72 拒案＋移交复查 ----
    lines.append("=== C. N72 拒案・移交复查 ===")
    review = {}
    # C1. とも：拒案维持（N69 1 変差＋N72 与に 121 変差）——只数残量
    c_tomo = [r["id"] for r in rows if "とも" in norm(r["udkundoku_kakikudashi"])]
    lines.append("  とも 残量 %d 行（N69/N72 拒案維持：yoryoezu-1 1 変差；repl 与に 121 変差）" % len(c_tomo))
    review["tomo_remaining"] = len(c_tomo)
    # C2. がため：L 收录後残量（应 ≈0）
    c_gatame = [r["id"] for r in rows if "がため" in norm(r["udkundoku_kakikudashi"])]
    lines.append("  がため 残量 %d 行（L 収録 repl 為 guard 爲 92/92 後の残量検証）" % len(c_gatame))
    review["gatame_remaining"] = c_gatame
    for rid in c_gatame:
        r = next(x for x in rows if x["id"] == rid)
        lines.append("      %s got: %s" % (rid, norm(r["udkundoku_kakikudashi"])[:80]))
    # C3. べからず：N68 §8-3 结构性 gap 实证收口——只数残量
    c_bekarazu = [r["id"] for r in rows if "べからず" in norm(r["udkundoku_kakikudashi"])]
    lines.append("  べからず 残量 %d 行（H 収録 guard 可＋N72 変差 5 行 exp 自写仮名——gap 收口済）" % len(c_bekarazu))
    review["bekarazu_remaining"] = len(c_bekarazu)
    # C4. はざる残量 singleton（N72 移交②）——はざる者 2 行只核实计数（本夜不收）
    c_haz = [r for r in rows if "はざる" in norm(r["udkundoku_kakikudashi"])]
    haz_suffix = collections.Counter()
    haz_details = []
    for r in c_haz:
        got = norm(r["udkundoku_kakikudashi"])
        i = got.find("はざる")
        tail = got[i + 3:i + 5]
        haz_suffix[tail] += 1
        if tail.startswith("者"):
            haz_details.append({"id": r["id"], "got": got[:100],
                                "exp": norm(r["expected_kakikudashi"])[:100],
                                "hakubun": norm(gmap[r["id"]]["hakubun"])[:100]})
    lines.append("  はざる残量 %d 行、後続 1〜2 字分布: %s" % (len(c_haz), dict(haz_suffix)))
    lines.append("  はざる者（key 含漢字「者」破純 kana 惯例・本夜不収）: %d 行" % len(haz_details))
    for d in haz_details:
        lines.append("      %s" % d["id"])
        lines.append("        got: %s" % d["got"])
        lines.append("        exp: %s" % d["exp"])
    review["hazaru_remaining"] = len(c_haz)
    review["hazaru_suffix"] = dict(haz_suffix)
    review["hazaru_mono"] = haz_details
    lines.append("")

    # ---- D. SHINJITAI 1:1 残量验证 ----
    pair_cnt = collections.Counter()
    for r in rows:
        got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        sm = SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op == "equal":
                continue
            g, e = got[a1:a2], exp[b1:b2]
            if len(g) == 1 and len(e) == 1 and is_kanji(g) and is_kanji(e) \
                    and old_to_new.get(g) != e:
                pair_cnt[(g, e)] += 1
    exp_all, got_all = charcount(rows)
    shin_cand = []
    lines.append("=== D. SHINJITAI 1:1 残量（count>=2、表中无、exp 旧形 0 次 & got>=2）===")
    for (g, e), n in pair_cnt.most_common():
        if n < 2 or g in old_to_new:
            continue
        exp_old = exp_all.get(g, 0)
        if exp_old > 0:
            continue
        exp_new = exp_all.get(e, 0)
        if exp_new < 1:
            continue
        shin_cand.append({"old": g, "new": e, "got": n, "exp_new": exp_new})
        lines.append("  %s→%s got %d exp新形 %d" % (g, e, n, exp_new))
    if not shin_cand:
        lines.append("  （0 対——N69/N72 结论维持）")
    lines.append("")

    print("\n".join(lines))
    out = os.path.join(EV, "night73_mine.json")
    json.dump({"baseline": "night72_results_8165.json", "rows": len(rows),
               "char_delta_all": cd_all, "kana_delta_all": kd_all,
               "kana_delta_shibu02": kd_shibu02, "opcode_pairs": b2_cand,
               "review": review, "shinjitai_left": shin_cand},
              open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    txt = os.path.join(EV, "night73_mine.txt")
    open(txt, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("written:", out, txt)


if __name__ == "__main__":
    main()
