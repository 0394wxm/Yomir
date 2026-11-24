# -*- coding: utf-8 -*-
"""night96_mine.py — N96 Rule S 候选挖掘（micro 区带 rows 1〜2 主力・(すべ,可) prefix 分離副切面）。

本夜主切面＝**1 字块 micro 区带（rows<=2）全枚举**（N94 §7 移交⑤：rows>=3 56 块完掘）：
  A1. 1 字块 rows>=3（N94 済区带の現基线残景・对照のみ・Rule R 12 行改写で自然変動あり）；
  A2. 1 字块 rows 1〜2 micro 区带＝全枚举（块数必定上百）——variants／guard 命中／
      样本 got・exp 全出し（手測素材）。有语汇对应相のみ probe に進める
      （は系 blanket・纯重排 artifact は记拒・probe 不进＝任务书②）。
  B2. opcode 词级挖复跑（rows>=4）＝N86/N88/N92/N94 复核（Rule R 生效後の自然変動は注记）。
  B3. (べ,可) 族全扫（副切面）：1 字块 (べ,可) variants＋B2 exp 頭 可 の全 pair
      ＝(すべ,可) 型未試 prefix 分離の素材（N92 すべからず 収録済・同じ族の未试長键を探す）。
  C1. なかれ 残量复核（拍板事项＝只复核不收录）；
  C2. はざる 残量复核（blanket 拒案維持確認）；
  C3. 既收族残量（Rule O 三键＋Rule Q 二键＋Rule R 一键＝健全性確認）；
  D.  SHINJITAI 1:1 残量（再確認・N88/N92/N94 0 対の复核）。

基线 = eval/night95_results_8165.json（N95 合并夜链尾真机归档 13.498/30/0＝Rule R
1 条生效後）。链尾断言：与 night94_results_8165.json の got 差异＝**0 行**（N95 合并夜
night95 归档＝night94 归档逐位一致の実証）。night95_results_4000.json 前 4000 行 got
逐位一致も断言。
行分类（规则可达性＝N84 fallback 分支复现，直接 import backend.main 現行分岐）：
  engine  = detect_text_type 非 kana：style_fix_with_hakubun(got, 白文全文)
            ——guard 上下文＝白文全文；
  rerun   = kana 分流・尾段>8：_kundoku_result_for(tail)
            ——guard 上下文＝尾段（main.py 現行分岐）；
  echo    = kana 分流・尾段<=8：白文直出、规则不可达（除外）；
  no_tail = kana 分流・尾段なし：空串のまま（除外）。
只读；输出 eval/night96_mine.json / night96_mine.txt。
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

HANDLED = {
    # E〜N 既收（night88_mine.py 清单の継承）
    "これ", "また", "それ", "ゆゑん", "いはゆる", "たがいに",
    "みな", "すでに", "なお", "あに", "ただ", "いかん",
    "べし", "べく", "べからず", "ことなかれ", "なかれ", "ごとし", "ごとく", "ごとき",
    "ゆえ", "ために", "べき", "べから", "のみ", "もの", "とき", "ところ",
    "けだし", "いずくんぞ", "もし", "まさに",
    "ひて", "へて", "はず", "へず", "いやしくも", "なんぞ",
    "つひに", "がため", "はざるなり", "はざるを",
    "そく", "はあるいは", "ゆき", "はそれ", "何のごとし", "何のごとく",
    "することなかれ", "ざることなかれ", "なることなかれ", "うことなかれ",
    "ることなかれ", "はいよいよ", "いよいよ", "しばしば", "ほとんど",
    "はやや", "やや", "たま",
    # N86 Rule O 既收
    "はざる者", "たりせ", "なきか",
    # N92 Rule Q 既收
    "ことなく", "すべからず",
}
STRUCTURAL = {"して", "なりて", "するを", "みて", "すを", "なるを", "するは", "すは",
              "なるは", "するなり", "るか", "ぎて", "なるか", "ぶを", "せずして",
              "しての", "するの", "らを", "するか", "にたり", "つを", "ぶは",
              "なるなり", "すか", "すや", "すは"}

# N92/N94 probe 済块（rows>=3 区带＝N94 済・micro は新规）
TESTED_N92 = {("は", "将"), ("は", "未"), ("た", "為"), ("て", "為"), ("べ", "可")}

EXPECTED_CLASS = {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}
EXPECTED_N94_DIFF = 0  # night95 vs night94 got 差异＝N95 合并夜逐位一致（Rule R 済み基线）


def norm(s):
    return re.sub(r"\s+", "", s or "")


def is_kanji(c):
    return bool(c) and ("\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf")


_KANA_RE = re.compile(r"[ぁ-ゖー]+")
_KANA_ONLY_RE = re.compile(r"^[ぁ-ゖー]+$")


def _lev(a, b):
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
    doc = json.load(open(os.path.join(EV, "night95_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    n94 = json.load(open(os.path.join(EV, "night94_results_8165.json"), encoding="utf-8"))["results"]
    doc4 = json.load(open(os.path.join(EV, "night95_results_4000.json"), encoding="utf-8"))
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序" % i
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    assert len(rows) == 8165, "基线行数 %d != 8165" % len(rows)
    # ---- 链尾断言：night95 归档 got 与 night94 差异 = 0 行（N95 合并夜逐位一致）----
    m94 = {b["id"]: b for b in n94}
    diff94 = [r["id"] for r in rows
              if norm(r["udkundoku_kakikudashi"]) != norm(m94[r["id"]]["udkundoku_kakikudashi"])]
    assert len(diff94) == EXPECTED_N94_DIFF, \
        "night95 vs night94 got 差异 %d 行 != %d（N95 合并夜逐位一致）" % (len(diff94), EXPECTED_N94_DIFF)
    rows4 = doc4["results"]
    assert [r["id"] for r in rows4] == [r["id"] for r in rows[:4000]], "4000/8165 前 4000 行不同序"
    for a, b in zip(rows4, rows[:4000]):
        assert norm(a["udkundoku_kakikudashi"]) == norm(b["udkundoku_kakikudashi"]), \
            "4000/8165 got 不一致: %s" % a["id"]

    from backend.kundoku_rules import SHINJITAI_MAP
    old_to_new = dict(SHINJITAI_MAP)
    new_to_old = {}
    for o, n in old_to_new.items():
        new_to_old.setdefault(n, o)

    def guard_forms(g):
        """守り字 g 的新旧两形（＋本身）：N72 移交①——新旧字体两形并查成文执行。"""
        forms = [g]
        for f in (new_to_old.get(g), old_to_new.get(g)):
            if f and f not in forms:
                forms.append(f)
        return tuple(forms)

    # ---- 行分类（backend.main 現行分岐の輸入）＋ guard 上下文 ----
    from backend.main import detect_text_type, _ruby_tail_kanbun
    cls = {}
    hb_of = {}
    for r in rows:
        raw = r["hakubun"] or ""
        if detect_text_type(raw) == "kana":
            tail = _ruby_tail_kanbun(raw)
            if not tail:
                cls[r["id"]] = "no_tail"
                hb_of[r["id"]] = ""
            elif len(tail) <= 8:
                cls[r["id"]] = "echo"
                hb_of[r["id"]] = norm(tail)  # 白文直出＝規則不可達（hb は参考記録のみ）
            else:
                cls[r["id"]] = "rerun"
                hb_of[r["id"]] = norm(tail)  # 尾段重跑＝guard 上下文は尾段
        else:
            cls[r["id"]] = "engine"
            hb_of[r["id"]] = norm(raw)      # 全文訓読＝guard 上下文は全文
    cc = collections.Counter(cls.values())
    assert dict(cc) == EXPECTED_CLASS, "行分类実数 %s != 期待 %s" % (dict(cc), EXPECTED_CLASS)
    reachable = [r for r in rows if cls[r["id"]] in ("engine", "rerun")]

    lines = []
    lines.append("基线 = night95_results_8165.json（N95 链尾・Rule R 生效後 13.498/30/0）| "
                 "night95 vs night94 got 差异 %d 行（=0・N95 合并夜逐位一致）| "
                 "行分类 %s | 規則可達 %d 行" % (len(diff94), dict(cc), len(reachable)))

    # ---- A1+A2. 1 字块枚举（主力：micro 区带 rows<=2 全列）----
    one_rows = collections.defaultdict(list)   # (kana, head) -> set(ids)
    one_variants = collections.defaultdict(list)  # (kana, head) -> [(exp_seg, ids)]
    for r in reachable:
        got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        sm = SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op != "replace":
                continue
            g_, e = got[a1:a2], exp[b1:b2]
            if len(g_) != 1 or not _KANA_ONLY_RE.match(g_):
                continue
            if not e or not is_kanji(e[0]):
                continue
            key = (g_, e[0])
            if r["id"] not in one_rows[key]:
                one_rows[key].append(r["id"])
            one_variants[key].append((e, r["id"]))

    id2row = {r["id"]: r for r in rows}
    band3 = []   # rows>=3（N94 済区带の現基线残景・对照のみ）
    micro = []   # rows 1〜2（本夜主力・全枚举）
    for (g_, head), ids in sorted(one_rows.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        gf = guard_forms(head)
        tgt_hits = sum(1 for rid in ids if any(f in hb_of[rid] for f in gf))
        vcnt = collections.Counter(v for v, _rid in one_variants[(g_, head)])
        entry = {"kana": g_, "head": head, "rows": len(ids),
                 "guard_forms": gf, "guard_hit_rows": tgt_hits,
                 "tested_n92": (g_, head) in TESTED_N92,
                 "variants": [{"exp_seg": v, "n": n} for v, n in vcnt.most_common(8)],
                 "example_id": sorted(ids)[0],
                 "sample_ids": sorted(ids)[:2] if len(ids) <= 2 else sorted(ids)[:1]}
        if len(ids) >= 3:
            band3.append(entry)
        else:
            micro.append(entry)

    lines.append("")
    lines.append("=== A1. 1 字块 rows>=3（N94 済区带の現基线残景・Rule R 生效後の自然変動のみ・对照）=== %d 块"
                 % len(band3))
    for c in band3:
        gf = "/".join(c["guard_forms"])
        vstr = " / ".join("%s(%d)" % (v["exp_seg"], v["n"]) for v in c["variants"][:5])
        tag = "【N92试替済】" if c["tested_n92"] else ""
        lines.append("  (%s,%s) 行数 %4d 守り %s 命中 %4d/%4d %s| exp側: %s" % (
            c["kana"], c["head"], c["rows"], gf, c["guard_hit_rows"], c["rows"], tag, vstr))
    lines.append("")
    lines.append("=== A2. 1 字块 micro 区带 rows 1〜2（本夜主力・全枚举）=== %d 块（行数内計 %d 行）"
                 % (len(micro), sum(c["rows"] for c in micro)))
    for c in micro:
        gf = "/".join(c["guard_forms"])
        vstr = " / ".join("%s(%d)" % (v["exp_seg"], v["n"]) for v in c["variants"])
        lines.append("  (%s,%s) 行数 %d 守り %s 命中 %d/%d | exp側: %s" % (
            c["kana"], c["head"], c["rows"], gf, c["guard_hit_rows"], c["rows"], vstr))
        for rid in c["sample_ids"]:
            r = id2row[rid]
            got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
            pos = got.find(c["kana"])
            lo, hi = max(0, pos - 25), min(len(got), pos + 25)
            lines.append("      %s [%s] got ...%s..." % (rid, cls[rid], got[lo:hi]))
            lines.append("          exp %s" % exp[:80])
    lines.append("")

    # ---- B2. opcode 词级挖复跑（副切面：预期多为 N86/N88 拒案の再確認）----
    pair_rows = collections.defaultdict(list)
    for r in reachable:
        got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        sm = SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op != "replace":
                continue
            g_, e = got[a1:a2], exp[b1:b2]
            if len(g_) < 2 or not _KANA_ONLY_RE.match(g_):
                continue
            if not e or not is_kanji(e[0]):
                continue
            pair_rows[(g_, e)].append(r["id"])

    pair_head = collections.defaultdict(list)
    for (g_, e), ids in pair_rows.items():
        pair_head[(g_, e[0])].append((e, ids))

    b2_cand = []
    lines.append("=== B2. opcode 词级挖复跑（副切面）：rows>=4（top 50）＝N86/N88/N92/N94 复核"
                 "（本夜基线 Rule R 生效後・12 行改写による変動は自然）===")
    for (g_, head), variants in sorted(pair_head.items(), key=lambda kv: -sum(len(v[1]) for v in kv[1])):
        total = sum(len(v[1]) for v in variants)
        if total < 4:
            break
        gf = guard_forms(head)
        tot_rows = set()
        for _e, ids in variants:
            tot_rows.update(ids)
        tgt_hits = sum(1 for rid in tot_rows if any(f in hb_of[rid] for f in gf))
        vstr = " / ".join("%s(%d)" % (v, len(ids)) for v, _ids in sorted(variants, key=lambda x: -len(x[1]))[:4])
        handled_tag = "【既覆盖】" if g_ in HANDLED else ""
        b2_cand.append({"kana": g_, "head": head, "rows": total,
                        "guard_forms": gf, "guard_hit_rows": tgt_hits,
                        "handled": g_ in HANDLED,
                        "variants": [{"exp_seg": v, "n": len(ids)} for v, ids in
                                     sorted(variants, key=lambda x: -len(x[1]))[:6]],
                        "example_id": sorted(tot_rows)[0]})
        lines.append("  %-12s → %-2s 行数 %4d 守り %s 命中 %4d/%4d %s| exp側: %s" % (
            g_, head, total, "/".join(gf), tgt_hits, len(tot_rows), handled_tag, vstr))
    lines.append("")

    # ---- B3. (べ,可) 族全扫（副切面：(すべ,可) 型未試 prefix 分離素材）----
    lines.append("=== B3. (べ,可) 族全扫（副切面）：1 字块 (べ,可) variants＋B2 exp 頭 可 の全 pair"
                 "（N92 すべからず 収録済・同じ族の未试長键・prefix 分離候補を探す）===")
    bek_block = one_rows.get(("べ", "可"), [])
    bek_variants = collections.Counter(v for v, _rid in one_variants.get(("べ", "可"), []))
    bek_rows = []
    for v, n in bek_variants.most_common():
        ids = sorted(rid for vv, rid in one_variants[("べ", "可")] if vv == v)
        bek_rows.append({"exp_seg": v, "n": n, "ids": ids})
        lines.append("  1字块 (べ,可) exp「%s」%d 行: %s" % (v, n, ",".join(ids[:12]) + ("..." if len(ids) > 12 else "")))
    bek_fired = []
    gf_ke = guard_forms("可")
    for r in reachable:
        got = norm(r["udkundoku_kakikudashi"])
        if "べ" in got and any(f in hb_of[r["id"]] for f in gf_ke):
            bek_fired.append(r["id"])
    lines.append("  1字块 (べ,可) 合計 %d 行 | guard 可 命中かつ got 含 べ の行 %d 行" % (
        len(bek_block), len(bek_fired)))
    bek2 = [(g_, e, ids) for (g_, e), ids in pair_rows.items() if e[0] == "可"]
    bek2.sort(key=lambda x: -len(x[2]))
    lines.append("  B2 exp 頭 可 の pair %d 件:" % len(bek2))
    bek2_out = []
    for g_, e, ids in bek2:
        gf = "/".join(guard_forms(e[0]))
        tot = set()
        for rid in ids:
            tot.add(rid)
        hits = sum(1 for rid in tot if any(f in hb_of[rid] for f in guard_forms(e[0])))
        bek2_out.append({"kana": g_, "exp_seg": e, "rows": len(ids),
                         "guard_forms": gf, "guard_hit_rows": hits,
                         "ids": sorted(tot)[:12]})
        lines.append("    %-16s → %-10s 行数 %4d 守り %s 命中 %4d/%4d %s" % (
            g_, e, len(ids), gf, hits, len(tot), "【既覆盖】" if g_ in HANDLED else ""))
    lines.append("")

    # ---- C1. なかれ 残量复核（N78 备选⑥・拍板事项＝本夜只复核不收录）----
    lines.append("=== C1. なかれ 残量复核（N78 备选⑥・基线 night95＝Rule R 生效後）===")
    rem = []
    for r in reachable:
        got = norm(r["udkundoku_kakikudashi"])
        if "なかれ" in got:
            m = re.search(r"[ぁ-ゖー]*なかれ", got)
            rem.append({"id": r["id"], "run": m.group(0), "cls": cls[r["id"]], "row": r})
    lines.append("  残量 %d 行（内訳 run: %s）" % (
        len(rem), dict(collections.Counter(x["run"] for x in rem))))
    mokaku = {}
    for repl in ("莫かれ", "莫し", "莫"):
        better = worse = same = 0
        detail = []
        for x in rem:
            r = x["row"]
            got = norm(r["udkundoku_kakikudashi"])
            exp = norm(r["expected_kakikudashi"])
            hb = hb_of[r["id"]]
            d0 = _lev(got, exp)
            if "莫" not in hb:
                detail.append({"id": x["id"], "run": x["run"], "d0": d0, "d1": d0,
                               "mark": "守り外"})
                continue
            new = got.replace("なかれ", repl)
            d1 = _lev(new, exp)
            detail.append({"id": x["id"], "run": x["run"], "d0": d0, "d1": d1,
                           "mark": "変差" if d1 > d0 else ("改善" if d1 < d0 else "same")})
            if d1 < d0:
                better += 1
            elif d1 > d0:
                worse += 1
            else:
                same += 1
        mokaku[repl] = {"better": better, "worse": worse, "same": same,
                        "detail": detail}
        lines.append("  なかれ→%s（guard 莫・row-class 别 guard 上下文）: 改善 %d／変差 %d／same %d" % (
            repl, better, worse, same))
    lines.append("  （N78 mokaku 結論の再確認：拍板事項のまま・本夜収録せず）")
    lines.append("")

    # ---- C2. はざる 残量复核（Rule O 收 はざる者 后・blanket 拒案維持確認）----
    lines.append("=== C2. はざる 残量复核（Rule O 収録後・blanket 拒案維持確認）===")
    haz = []
    for r in reachable:
        got = norm(r["udkundoku_kakikudashi"])
        if "はざる" in got:
            haz.append(r)
    lines.append("  残量 %d 行（はざる者 収録分を除く残量）" % len(haz))
    haz_out = []
    for r in haz:
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        hb = hb_of[r["id"]]
        d0 = _lev(got, exp)
        new = got.replace("はざる", "わざる")
        d1 = _lev(new, exp)
        haz_out.append({"id": r["id"], "d0": d0, "d1": d1})
        lines.append("    %s %d→%d | got: %s" % (r["id"], d0, d1, got[:70]))
        lines.append("      exp: %s" % exp[:70])
    lines.append("")

    # ---- C3. 既收族残量（健全性確認・Rule O/Q/R 含む）----
    lines.append("=== C3. 既收族残量（engine+rerun 行・規則適用後 got に残るべきでない）===")
    handled_residual = {}
    for w in ("がため", "ゆゑん", "つひに", "いずくんぞ", "しばしば", "ほとんど",
              "いよいよ", "はやや", "することなかれ", "ざることなかれ",
              "なることなかれ", "うことなかれ", "ることなかれ", "そく",
              "はあるいは", "ゆき", "はそれ", "何のごとし", "何のごとく",
              "はざる者", "たりせ", "なきか",
              "ことなく", "すべからず", "ゆく"):
        n_ = sum(1 for r in reachable if w in norm(r["udkundoku_kakikudashi"]))
        handled_residual[w] = n_
        lines.append("  %-12s 残量 %d 行" % (w, n_))
    lines.append("  （ゆく 残量は guard 之 外の行＝Rule R 不発火の健全状態・参考記録のみ）")
    lines.append("")

    # ---- D. SHINJITAI 1:1 残量（再確認）----
    pair_cnt = collections.Counter()
    for r in reachable:
        got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        sm = SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op == "equal":
                continue
            g_, e = got[a1:a2], exp[b1:b2]
            if len(g_) == 1 and len(e) == 1 and is_kanji(g_) and is_kanji(e) \
                    and old_to_new.get(g_) != e:
                pair_cnt[(g_, e)] += 1
    exp_all, got_all = collections.Counter(), collections.Counter()
    for r in reachable:
        exp_all.update(norm(r["expected_kakikudashi"]))
        got_all.update(norm(r["udkundoku_kakikudashi"]))
    shin_cand = []
    lines.append("=== D. SHINJITAI 1:1 残量（count>=2、表中无、exp 旧形 0 次 & exp 新形>=1）===")
    for (g_, e), n in pair_cnt.most_common():
        if n < 2 or g_ in old_to_new:
            continue
        if exp_all.get(g_, 0) > 0:
            continue
        if exp_all.get(e, 0) < 1:
            continue
        shin_cand.append({"old": g_, "new": e, "got": n, "exp_new": exp_all.get(e, 0)})
        lines.append("  %s→%s got %d exp新形 %d" % (g_, e, n, exp_all.get(e, 0)))
    if not shin_cand:
        lines.append("  （0 対——N69/N72/N73/N78/N86/N88/N92/N94 结论維持）")
    lines.append("")

    print("\n".join(lines))
    out = os.path.join(EV, "night96_mine.json")
    json.dump({"baseline": "night95_results_8165.json", "rows": len(rows),
               "n94_diff_rows": len(diff94), "class": dict(cc), "reachable": len(reachable),
               "band3_blocks": band3, "micro_blocks": micro,
               "opcode_pairs": b2_cand,
               "bek_ke_block": bek_rows, "bek_ke_fired": len(bek_fired),
               "bek_ke_pairs": bek2_out,
               "nakare_mokaku": mokaku,
               "hazaru": haz_out, "handled_residual": handled_residual,
               "shinjitai_left": shin_cand},
              open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    txt = os.path.join(EV, "night96_mine.txt")
    open(txt, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("written:", out, txt)


if __name__ == "__main__":
    main()
