# -*- coding: utf-8 -*-
"""night96_probe.py — N96 Rule S 试替表（micro 区带 rows<=2 有语汇对应相块・実数判定）。

候补＝night96_mine A2 micro 区带 658 块から語汇对应相の块＋B2 micro rows<=3 快查の
新長键形態（なきなり→勿かれ/毋かれ）＋B3 (べ,可) 族对照：
  T1  か→哉       guard 哉  — (か,哉) 2 pair（詩経反復 哉・悠なるか→悠なる哉）；
                              blanket か×哉 guard 予測 106 発火≫2 pair＝scramble リスク実測
  T2  なるか→なる哉 guard 哉  — 集約パス (a) 試み（(か,哉) の 2 字长键化・pair=0 制式）
  T3  ず→毋く     guard 毋  — (ず,毋) 2 pair（必ず→必毋く・論語子絶四）；
                              blanket ず×毋 guard 予測 8 発火
  T4  なきなり→勿かれ guard 勿 — B2 micro 新長键（3 pair・azamukuko/sonshi 系）
  T5  なきなり→毋かれ guard 毋 — B2 micro 新長键（2 pair・ichijicho/rongo1125）
  T6  な→勿       guard 勿  — blanket 測定（な×勿 guard 予測 36 発火≫1 pair）
  T7  べきか→可し   guard 可  — B3 (べ,可) 族对照再測（N92/N94: 31 発火 25/2・20 pair uniform）
  T8  るか→可し   guard 可  — B3 micro（1 pair）
  T9  ことなき→こと莫き guard 莫 — 禁区对照（N92 2 変差維持確認）

発火数＝guard 命中行（新旧両形并查・N72 移交①成文执行）中 got 含 key 行数；
発火 ≫ pair 行数 ⇒ 語彙対応でない（N88 T3 判定基準）。2 字长键の pair=0 は N94
已確認の制式問題（SequenceMatcher 拆块）——判定は変差実数で実施、pair 比は参考のみ。

基线 = eval/night95_results_8165.json（N95 合并夜链尾 13.498/30/0＝Rule R 生效後）。
链尾断言：night95 vs night94 got 差异 = 0 行（N95 合并夜逐位一致）。
行分类 N84 fallback 复现（engine 7916/echo 30/rerun 218/no_tail 1 断言锁定；
rerun 行 guard 上下文＝尾段）。
输出 eval/night96_probe.{json,txt}。只读。
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
EXPECTED_N94_DIFF = 0

TRIALS = [
    {"id": "T1", "kana": "か", "repl": "哉", "guard": ("哉",),
     "note": "(か,哉) micro 2 pair（詩経反復・悠なるか→悠なる哉）・guard 予測 106 発火≫2 pair",
     "pair": ("one", "か", "哉")},
    {"id": "T2", "kana": "なるか", "repl": "なる哉", "guard": ("哉",),
     "note": "T1 の 2 字长键化（集約パス (a)・pair=0 制式＝変差実数判定）",
     "pair": ("blk", "なるか", "なる哉")},
    {"id": "T3", "kana": "ず", "repl": "毋く", "guard": ("毋",),
     "note": "(ず,毋) micro 2 pair（必ず→必毋く・論語子絶四）・guard 予測 8 発火",
     "pair": ("one", "ず", "毋")},
    {"id": "T4", "kana": "なきなり", "repl": "勿かれ", "guard": ("勿",),
     "note": "B2 micro 新長键 3 pair（azamukuko-1/sonshi09-19/sonshi10-12・勿/毋 字形別は guard 分離）",
     "pair": ("blk", "なきなり", "勿かれ")},
    {"id": "T5", "kana": "なきなり", "repl": "毋かれ", "guard": ("毋",),
     "note": "B2 micro 新長键 2 pair（ichijicho-1/rongo1125-1）",
     "pair": ("blk", "なきなり", "毋かれ")},
    {"id": "T6", "kana": "な", "repl": "勿", "guard": ("勿",),
     "note": "blanket 測定（な×勿 guard 予測 36 発火≫1 pair＝(な,勿) micro・実数判定）",
     "pair": ("one", "な", "勿")},
    {"id": "T7", "kana": "べきか", "repl": "可し", "guard": ("可",),
     "note": "B3 (べ,可) 族对照再測（N92/N94: 31 発火 25 改善/2 変差・20 pair uniform 可し）",
     "pair": ("blk", "べきか", "可し")},
    {"id": "T8", "kana": "るか", "repl": "可し", "guard": ("可",),
     "note": "B3 micro 1 pair（るか→可し）",
     "pair": ("blk", "るか", "可し")},
    {"id": "T9", "kana": "ことなき", "repl": "こと莫き", "guard": ("莫",),
     "note": "禁区对照（N92 T4 2 変差維持確認・got 已含莫かれ・exp 字形混在）",
     "pair": ("blk", "ことなき", "こと莫き")},
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
    doc = json.load(open(os.path.join(EV, "night95_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    n94 = json.load(open(os.path.join(EV, "night94_results_8165.json"), encoding="utf-8"))["results"]
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序" % i
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    assert len(rows) == 8165
    m94 = {b["id"]: b for b in n94}
    diff94 = [r["id"] for r in rows
              if norm(r["udkundoku_kakikudashi"]) != norm(m94[r["id"]]["udkundoku_kakikudashi"])]
    assert len(diff94) == EXPECTED_N94_DIFF, \
        "night95 vs night94 got 差异 %d != 0（N95 合并夜逐位一致）" % len(diff94)

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
        delta_sum = sum(d["d1"] - d["d0"] for d in fired_det)
        delta = round(delta_sum / 8165, 6)
        ratio = round(len(fired) / max(1, n_pair), 1)
        verdict = "——発火/pair=%.1f" % ratio + ("（≫1＝scramble リスク）" if ratio > 3 else "")
        out_trials.append({"id": t["id"], "kana": t["kana"], "repl": t["repl"],
                           "guard": list(gf), "note": t["note"],
                           "pair_anchor": [kind, gk, ek], "pair_rows": n_pair,
                           "fired": len(fired), "better": better, "worse": worse,
                           "same": same, "delta": delta, "fired_detail": fired_det})
        lines.append("%s %s→%s（guard %s・%s）: pair %d 行 発火 %d 行 改善 %d 変差 %d same %d Δ%.6f %s" % (
            t["id"], t["kana"], t["repl"], "/".join(gf), t["note"],
            n_pair, len(fired), better, worse, same, delta, verdict))
        for d in fired_det:
            if d["mark"] == "変差":
                r = next(x for x in reachable if x["id"] == d["id"])
                lines.append("    変差 %s [%s] %d→%d | got %s" % (
                    d["id"], d["cls"], d["d0"], d["d1"], norm(r["udkundoku_kakikudashi"])[:70]))
                lines.append("        exp %s" % norm(r["expected_kakikudashi"])[:70])
        lines.append("    (%.0fs)" % (time.time() - t0))
        lines.append("")

    print("\n".join(lines))
    json.dump({"baseline": "night95_results_8165.json", "trials": out_trials},
              open(os.path.join(EV, "night96_probe.json"), "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night96_probe.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("written: eval/night96_probe.json / night96_probe.txt")


if __name__ == "__main__":
    main()
