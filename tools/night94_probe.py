# -*- coding: utf-8 -*-
"""night94_probe.py — N94 Rule R 试替表（1 字块 3〜5 行区 + N92 未试替块・长键手測）。

候补＝night94_mine A 表（1 字块枚举 rows>=3・56 块）＋ B2 (とも,与) から锚定した长键：
  (a) N92 未试替 11 块（任务书清单）：の→之に／は→有／も→与に／とも→与に（B2 长键）／
      は→少／は→白／は→行／は→来／は→尽／は→樹／は→闕／な→莫（Rule Q 後残量 5）
  (b) 新 3〜5 行区 uniform/近 uniform 长键：嗟や→嗟乎・ゆく→之く・は→請う・は→不・
      は→見ずや・は→無・は→復た・は→自ずから・は→服・は→猶お・は→舎・は→聞く、・
      な→悠た・ら→回か・に→郷・を→者に・は→為に・に→来（＋や→乎 blanket 对照）

発火数＝guard 命中行（新旧両形并查・N72 移交①成文执行）中 got 含 key 行数；
発火 ≫ pair 行数 ⇒ 語彙対応でない（N88 T3 して→問す 5 pair vs 162 発火 scramble
実証例の判定基準）。(は,*) 块は N92 §7 预判 scramble＝本夜も実測数字で判定
（预判で拒らない＝任务书明示）。

基线 = eval/night92_results_8165.json（N93 链尾・Rule Q 生效後 13.500/30/0）。
链尾断言：night92 vs night91 got 差异 = 37 行（Rule Q 改写行数）。
行分类 N84 fallback 复现（engine 7916/echo 30/rerun 218/no_tail 1 断言锁定；
rerun 行 guard 上下文＝尾段）。
输出 eval/night94_probe.{json,txt}。只读。
"""
import collections
import json
import os
import re
import sys
import time
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")

EXPECTED_CLASS = {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}
EXPECTED_Q_DIFF = 37

TRIALS = [
    # ---- (a) N92 未试替 11 块（任务书清单・(な,莫) は Rule Q 生效後 9→5 残量）----
    {"id": "T1", "kana": "の", "repl": "之に", "guard": ("之",),
     "note": "(の,之) 9 行・之に 5 uniform（之/之は/之を経るに/之を 混在）",
     "pair": ("one", "の", "之")},
    {"id": "T2", "kana": "は", "repl": "有", "guard": ("有",),
     "note": "(は,有) 7 行・有 4（烏は→烏有・冉は→冉有 专名型含む）",
     "pair": ("one", "は", "有")},
    {"id": "T3", "kana": "も", "repl": "与に", "guard": ("与",),
     "note": "(も,与) 7 行・与に 4（与にか 3・与わるに 1 混在）",
     "pair": ("one", "も", "与")},
    {"id": "T4", "kana": "とも", "repl": "与に", "guard": ("与",),
     "note": "B2 (とも,与) 5 uniform 与に・4 字长键",
     "pair": ("blk", "とも", "与に")},
    {"id": "T5", "kana": "は", "repl": "少", "guard": ("少",),
     "note": "(は,少) 6 行（少き/少にして/少/少なく 混在）",
     "pair": ("one", "は", "少")},
    {"id": "T6", "kana": "は", "repl": "白", "guard": ("白",),
     "note": "(は,白) 6 行（白 4・白蓮/白波に 混在）",
     "pair": ("one", "は", "白")},
    {"id": "T7", "kana": "は", "repl": "行", "guard": ("行",),
     "note": "(は,行) 6 行（行〻/行人/行くこと 混在）",
     "pair": ("one", "は", "行")},
    {"id": "T8", "kana": "は", "repl": "来", "guard": ("来",),
     "note": "(は,来) 6 行（来って/来/来る/来の 混在）",
     "pair": ("one", "は", "来")},
    {"id": "T9", "kana": "は", "repl": "尽", "guard": ("尽",),
     "note": "(は,尽) 6 行（尽きて 3・尽く 3）",
     "pair": ("one", "は", "尽")},
    {"id": "T10", "kana": "は", "repl": "樹", "guard": ("樹",),
     "note": "(は,樹) 6 行（樹 4・樹の 2）",
     "pair": ("one", "は", "樹")},
    {"id": "T11", "kana": "は", "repl": "闕", "guard": ("闕",),
     "note": "(は,闕) 6 行（闕 5・闕の 1）",
     "pair": ("one", "は", "闕")},
    {"id": "T12", "kana": "な", "repl": "莫", "guard": ("莫",),
     "note": "(な,莫) 5 残量（Rule Q guard 外 ことなく＋ことなき/なかれ 禁区行・実測のみ）",
     "pair": ("one", "な", "莫")},
    # ---- (b) 新 3〜5 行区带（uniform/近 uniform 长键手測）----
    {"id": "T13", "kana": "嗟や", "repl": "嗟乎", "guard": ("乎",),
     "note": "(や,乎) 3 uniform 嗟や→嗟乎・2 字长键（歎詞・新候补）",
     "pair": ("blk", "嗟や", "嗟乎")},
    {"id": "T14", "kana": "や", "repl": "乎", "guard": ("乎",),
     "note": "(や,乎) 对照・1 字 blanket（T13 死时の単形確認）",
     "pair": ("one", "や", "乎")},
    {"id": "T15", "kana": "ゆく", "repl": "之く", "guard": ("之",),
     "note": "(ゆ,之) 3 uniform ゆく→之く・2 字长键",
     "pair": ("blk", "ゆく", "之く")},
    {"id": "T16", "kana": "は", "repl": "請う", "guard": ("請",),
     "note": "(は,請) 4（臣は→臣請う 重排 artifact 型）",
     "pair": ("one", "は", "請")},
    {"id": "T17", "kana": "は", "repl": "不", "guard": ("不",),
     "note": "(は,不) 4 uniform（Xは敏ならず→X不敏 型・活用語混在）",
     "pair": ("one", "は", "不")},
    {"id": "T18", "kana": "は", "repl": "見ずや", "guard": ("見",),
     "note": "(は,見) 4 uniform 見ずや（君は…見ず→君見ずや 倒置型）",
     "pair": ("one", "は", "見")},
    {"id": "T19", "kana": "は", "repl": "無", "guard": ("無",),
     "note": "(は,無) 5 uniform（こと無き→無限 重排 artifact 型）",
     "pair": ("one", "は", "無")},
    {"id": "T20", "kana": "は", "repl": "復た", "guard": ("復",),
     "note": "(は,復) 4（復た 3 uniform・復た旧き池台 1）",
     "pair": ("one", "は", "復")},
    {"id": "T21", "kana": "は", "repl": "自ずから", "guard": ("自",),
     "note": "(は,自) 4（自ずから 5 次・自ら 1）",
     "pair": ("one", "は", "自")},
    {"id": "T22", "kana": "は", "repl": "服", "guard": ("服",),
     "note": "(は,服) 3 uniform",
     "pair": ("one", "は", "服")},
    {"id": "T23", "kana": "は", "repl": "猶お", "guard": ("猶",),
     "note": "(は,猶) 3 uniform 猶お",
     "pair": ("one", "は", "猶")},
    {"id": "T24", "kana": "は", "repl": "舎", "guard": ("舎",),
     "note": "(は,舎) 5（舎 4・舎を 1）",
     "pair": ("one", "は", "舎")},
    {"id": "T25", "kana": "は", "repl": "聞く、", "guard": ("聞",),
     "note": "(は,聞) 5（聞く、2・聞かずや 2・聞くに 1 混在）",
     "pair": ("one", "は", "聞")},
    {"id": "T26", "kana": "な", "repl": "悠た", "guard": ("悠",),
     "note": "(な,悠) 3 uniform 悠た",
     "pair": ("one", "な", "悠")},
    {"id": "T27", "kana": "ら", "repl": "回か", "guard": ("回",),
     "note": "(ら,回) 3 uniform 回か",
     "pair": ("one", "ら", "回")},
    {"id": "T28", "kana": "に", "repl": "郷", "guard": ("郷",),
     "note": "(に,郷) 3 uniform（故に…郷して→故郷 重排 artifact 型）",
     "pair": ("one", "に", "郷")},
    {"id": "T29", "kana": "を", "repl": "者に", "guard": ("者",),
     "note": "(を,者) 3 uniform 者に",
     "pair": ("one", "を", "者")},
    {"id": "T30", "kana": "は", "repl": "為に", "guard": ("為",),
     "note": "(は,為) 5（為に 4 uniform・為れぞ 1）",
     "pair": ("one", "は", "為")},
    {"id": "T31", "kana": "に", "repl": "来", "guard": ("来",),
     "note": "(に,来) 3 uniform",
     "pair": ("one", "に", "来")},
]


def norm(s):
    return re.sub(r"\s+", "", s or "")


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
    doc = json.load(open(os.path.join(EV, "night92_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    n91 = json.load(open(os.path.join(EV, "night91_results_8165.json"), encoding="utf-8"))["results"]
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序" % i
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    assert len(rows) == 8165
    m91 = {b["id"]: b for b in n91}
    diff91 = [r["id"] for r in rows
              if norm(r["udkundoku_kakikudashi"]) != norm(m91[r["id"]]["udkundoku_kakikudashi"])]
    assert len(diff91) == EXPECTED_Q_DIFF, \
        "night92 vs night91 got 差异 %d != %d" % (len(diff91), EXPECTED_Q_DIFF)

    from backend.kundoku_rules import SHINJITAI_MAP
    old_to_new = dict(SHINJITAI_MAP)
    new_to_old = {}
    for o, n in old_to_new.items():
        new_to_old.setdefault(n, o)

    def guard_forms(chars):
        out = []
        for c in chars:
            for f in (c, new_to_old.get(c), old_to_new.get(c)):
                if f and f not in out:
                    out.append(f)
        return out

    from backend.main import detect_text_type, _ruby_tail_kanbun
    cls, hb_of = {}, {}
    for r in rows:
        raw = r["hakubun"] or ""
        if detect_text_type(raw) == "kana":
            tail = _ruby_tail_kanbun(raw)
            if not tail:
                cls[r["id"]] = "no_tail"
                hb_of[r["id"]] = ""
            elif len(tail) <= 8:
                cls[r["id"]] = "echo"
                hb_of[r["id"]] = norm(tail)
            else:
                cls[r["id"]] = "rerun"
                hb_of[r["id"]] = norm(tail)
        else:
            cls[r["id"]] = "engine"
            hb_of[r["id"]] = norm(raw)
    cc = collections.Counter(cls.values())
    assert dict(cc) == EXPECTED_CLASS, "行分类実数 %s != 期待 %s" % (dict(cc), EXPECTED_CLASS)
    reachable = [r for r in rows if cls[r["id"]] in ("engine", "rerun")]

    # 1 字块 pair 行集合（発火数比対用・N92 制式）＋ 全 replace 块 map（2 字长键锚定用）
    _KANA_ONLY_RE = re.compile(r"^[ぁ-ゖー]+$")

    def is_kanji(c):
        return bool(c) and ("\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf")

    one_rows = collections.defaultdict(set)
    block_map = collections.defaultdict(set)
    for r in reachable:
        got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        sm = SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op != "replace":
                continue
            g_, e = got[a1:a2], exp[b1:b2]
            if not g_ or not e:
                continue
            if len(g_) == 1 and _KANA_ONLY_RE.match(g_) and e and is_kanji(e[0]):
                one_rows[(g_, e[0])].add(r["id"])
            block_map[(g_, e)].add(r["id"])

    lines = []
    out_trials = []
    for t in TRIALS:
        t0 = time.time()
        gf = guard_forms(t["guard"])
        kind, gk, ek = t["pair"]
        if kind == "one":
            n_pair = len(one_rows.get((gk, ek), ()))
        else:
            n_pair = len(block_map.get((gk, ek), ()))
        fired = []
        for r in reachable:
            hb = hb_of[r["id"]]
            if not any(g in hb for g in gf):
                continue
            if t["kana"] in norm(r["udkundoku_kakikudashi"]):
                fired.append(r)
        better = worse = same = 0
        fired_det = []
        for r in fired:
            got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
            d0 = _lev(got, exp)
            new = got.replace(t["kana"], t["repl"])
            d1 = _lev(new, exp)
            mark = "変差" if d1 > d0 else ("改善" if d1 < d0 else "same")
            fired_det.append({"id": r["id"], "cls": cls[r["id"]], "d0": d0, "d1": d1, "mark": mark})
            if d1 > d0:
                worse += 1
            elif d1 < d0:
                better += 1
            else:
                same += 1
        ratio = round(len(fired) / max(1, n_pair), 1)
        verdict = "——発火/pair=%.1f" % ratio + ("（≫1＝scramble リスク）" if ratio > 3 else "")
        out_trials.append({"id": t["id"], "kana": t["kana"], "repl": t["repl"],
                           "guard": list(gf), "note": t["note"],
                           "pair_anchor": [kind, gk, ek], "pair_rows": n_pair,
                           "fired": len(fired), "better": better, "worse": worse,
                           "same": same, "fired_detail": fired_det})
        lines.append("%s %s→%s（guard %s・%s）: pair %d 行 発火 %d 行 改善 %d 変差 %d same %d %s" % (
            t["id"], t["kana"], t["repl"], "/".join(gf), t["note"],
            n_pair, len(fired), better, worse, same, verdict))
        for d in fired_det:
            if d["mark"] == "変差":
                r = next(x for x in reachable if x["id"] == d["id"])
                lines.append("    変差 %s [%s] %d→%d | got %s" % (
                    d["id"], d["cls"], d["d0"], d["d1"], norm(r["udkundoku_kakikudashi"])[:70]))
                lines.append("        exp %s" % norm(r["expected_kakikudashi"])[:70])
        lines.append("    (%.0fs)" % (time.time() - t0))
        lines.append("")

    print("\n".join(lines))
    json.dump({"baseline": "night92_results_8165.json", "trials": out_trials},
              open(os.path.join(EV, "night94_probe.json"), "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night94_probe.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("written: eval/night94_probe.json / night94_probe.txt")


if __name__ == "__main__":
    main()
