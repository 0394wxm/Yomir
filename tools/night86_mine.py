# -*- coding: utf-8 -*-
"""night86_mine.py — N86 Rule O 候选挖掘（Night 68/73/78 方法论第七遍）。

基线 = eval/night85_results_8165.json（N85 合并夜链尾真机归档；与 night84_results_8165.json
全行 got 逐位一致——Rule N 在链、N84 ruby fallback 生效后的 got 即 Rule O 将看到的链尾文本）。
基线断言：results/golden 同序；night85 vs night84 全行 got 逐位一致；
night85_results_4000.json 前 4000 行与 8165 归档一致。

行分类（规则可达性＝N84 fallback 分支复现，直接 import backend.main 現行分岐）：
  engine  = detect_text_type 非 kana：style_fix_with_hakubun(got, 白文全文)
            ——guard 上下文＝白文全文；
  rerun   = kana 分流・尾段>8：_kundoku_result_for(tail)
            ——guard 上下文＝尾段（main.py 現行分岐）；
  echo    = kana 分流・尾段≤8：白文直出、规则不可达（挖词/适用対象から除外）；
  no_tail = kana 分流・尾段なし：空串のまま（除外）。

切面：
  B2. opcode 词级挖（主切面・N73 移交①）：SequenceMatcher replace 块、got 侧纯假名
      (>=2) × exp 侧汉字头 → (kana, 汉字头) 对计数——守り字候补は新旧字体两形并查
      （N72 移交①成文执行）；
  C1. N78 备选⑥ 复核：なかれ→莫かれ/莫し/莫（guard 莫・guard 上下文按行类）post-N
      残量を per-row 実距で再計数（N84 後の 218 rerun 行も現行分岐で再判定）；
  C2. はざる 残量（N72 から拍板待ち・はざる者 2 行含む）got/exp/白文 再録；
  C3. 既收族残量（がため/ゆゑん/なんぞ 等＝0 であるべき一族の健全性確認）；
  D.  SHINJITAI 1:1 残量（N69/N72/N73/N78 结论の再確認）。
只读；输出 eval/night86_mine.json / night86_mine.txt。
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
    # E〜M 既收（night78_mine.py 清单の継承）
    "これ", "また", "それ", "ゆゑん", "いはゆる", "たがいに",
    "みな", "すでに", "なお", "あに", "ただ", "いかん",
    "べし", "べく", "べからず", "ことなかれ", "なかれ", "ごとし", "ごとく", "ごとき",
    "ゆえ", "ために", "べき", "べから", "のみ", "もの", "とき", "ところ",
    "けだし", "いずくんぞ", "もし", "まさに",
    "ひて", "へて", "はず", "へず", "いやしくも", "なんぞ",
    "つひに", "がため", "はざるなり", "はざるを",
    "そく", "はあるいは", "ゆき", "はそれ", "何のごとし", "何のごとく",
    # N78 Rule N 既收
    "することなかれ", "ざることなかれ", "なることなかれ", "うことなかれ",
    "ることなかれ", "はいよいよ", "いよいよ", "しばしば", "ほとんど",
    "はやや", "やや", "たま",
}
STRUCTURAL = {"して", "なりて", "するを", "みて", "すを", "なるを", "するは", "すは",
              "なるは", "するなり", "るか", "ぎて", "なるか", "ぶを", "せずして",
              "しての", "するの", "らを", "するか", "にたり", "つを", "ぶは",
              "なるなり", "すか", "すや", "すは"}

EXPECTED_CLASS = {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}


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
    doc = json.load(open(os.path.join(EV, "night85_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    n84 = json.load(open(os.path.join(EV, "night84_results_8165.json"), encoding="utf-8"))["results"]
    doc4 = json.load(open(os.path.join(EV, "night85_results_4000.json"), encoding="utf-8"))
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序" % i
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    assert len(rows) == 8165, "基线行数 %d != 8165" % len(rows)
    # ---- 基线必须是 N85 链尾（与 night84 归档逐位一致＝N85 合并夜回归结论の再验证）----
    m84 = {b["id"]: b for b in n84}
    for r in rows:
        assert norm(r["udkundoku_kakikudashi"]) == norm(m84[r["id"]]["udkundoku_kakikudashi"]), \
            "night85 归档与 night84 链尾不一致: %s" % r["id"]
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
    lines.append("基线 = night85_results_8165.json（N85 链尾・与 night84 逐位一致）| "
                 "行分类 %s | 規則可達 %d 行" % (dict(cc), len(reachable)))

    # ---- B2. opcode 词级挖（主切面）----
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
    lines.append("")
    lines.append("=== B2. opcode 词级挖：got 纯假名 replace 块 × exp 汉字头（行数>=4，top 50）===")
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

    # ---- C1. N78 备选⑥ 复核：なかれ 残量（guard 莫・実距再計数）----
    lines.append("=== C1. なかれ 残量（N78 备选⑥ 复核・基线 night85）===")
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
        for d in detail:
            lines.append("    %s %-14s %d→%d %s" % (d["id"], d["run"], d["d0"], d["d1"], d["mark"]))
    lines.append("  （N78 mokaku 結論の再確認：排除 guard／kanji→kanji 机制なしでは "
                 "kokyo09-5 1 変差を避けられない＝普通规则＋guard の形では不通）")
    lines.append("")

    # ---- C2. はざる 残量（N72 から拍板待ち）----
    lines.append("=== C2. はざる 残量（N72 移交・拍板待ち）===")
    haz = []
    for r in reachable:
        got = norm(r["udkundoku_kakikudashi"])
        if "はざる" in got:
            haz.append(r)
    lines.append("  残量 %d 行" % len(haz))
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
        lines.append("      白文: %s" % hb[:70])
    lines.append("")

    # ---- C3. 既收族残量（健全性確認・0 であるべき）----
    lines.append("=== C3. 既收族残量（engine+rerun 行・規則適用後 got に残るべきでない）===")
    handled_residual = {}
    for w in ("がため", "ゆゑん", "つひに", "いずくんぞ", "しばしば", "ほとんど",
              "いよいよ", "はやや", "することなかれ", "ざることなかれ",
              "なることなかれ", "うことなかれ", "ることなかれ", "そく",
              "はあるいは", "ゆき", "はそれ", "何のごとし", "何のごとく"):
        n_ = sum(1 for r in reachable if w in norm(r["udkundoku_kakikudashi"]))
        handled_residual[w] = n_
        lines.append("  %-12s 残量 %d 行" % (w, n_))
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
        lines.append("  （0 対——N69/N72/N73/N78 结论維持）")
    lines.append("")

    print("\n".join(lines))
    out = os.path.join(EV, "night86_mine.json")
    json.dump({"baseline": "night85_results_8165.json", "rows": len(rows),
               "class": dict(cc), "reachable": len(reachable),
               "opcode_pairs": b2_cand, "nakare_mokaku": mokaku,
               "hazaru": haz_out, "handled_residual": handled_residual,
               "shinjitai_left": shin_cand},
              open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    txt = os.path.join(EV, "night86_mine.txt")
    open(txt, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("written:", out, txt)


if __name__ == "__main__":
    main()
