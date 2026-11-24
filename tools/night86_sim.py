# -*- coding: utf-8 -*-
"""night86_sim.py — N86 Rule O 候选离线模拟＋收录判定＋组合双口径
（机制照抄 night78_sim.py：lev / apply_one / run / idempotent，
基线 = night85 真机 8165（N85 链尾・与 night84 逐位一致）。

N84 fallback 行分类を反映（night86_mine/probe 同款）：規則適用対象は engine+rerun の
8134 行のみ（echo 30 行＝白文直出・no_tail 1 行＝空串、規則不可達）。rerun 行の
guard 上下文は尾段（main.py 現行分岐どおり）。

Levenshtein：.night72_deps 隔离目录が無い環境（本夜実測＝存在せず）は纯 Python 回退
——night85_eval_8165.py の lev と同一算法なので归档 edit_distance と逐位一致。

収録硬门（任务书②）：変差>0 一律不収。＋N69 収録線 Δ<=-0.001（無益拒）。
长尾扫描（B2 uniform exp_seg pair、len>=3、発火<=120、既收/结构 key 除く）を追加で
回し、0 変差＆Δ線達成 pair は追加候補として人工复核、線未達は無益集計。

输出 eval/night86_sim.json / night86_sim.txt / night86_combo_changed_rows.json。
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
sys.path.insert(0, os.path.join(ROOT, ".night72_deps"))  # 隔离目录（あれば C 库）
EV = os.path.join(ROOT, "eval")


def _lev_pure(a, b):
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


try:
    from Levenshtein import distance as _lev_c
    _LEV_IMPL = "Levenshtein C (.night72_deps 隔离目录)"
except Exception:  # pragma: no cover
    _lev_c = None
    _LEV_IMPL = "纯 Python 回退（night85_eval lev と同一算法・归档と逐位一致）"


def lev(a, b):
    if _lev_c is not None:
        return _lev_c(a, b)
    return _lev_pure(a, b)


def norm(s):
    return re.sub(r"\s+", "", s or "")


def apply_one(text, kana, repl, longer):
    longer = sorted(longer, key=len, reverse=True)
    out, i, n = [], 0, len(kana)
    while True:
        j = text.find(kana, i)
        if j < 0:
            out.append(text[i:])
            break
        tail = text[j:]
        hit = next((w for w in longer if tail.startswith(w)), None)
        if hit:
            out.append(text[i:j + len(hit)])
            i = j + len(hit)
        else:
            out.append(text[i:j] + repl)
            i = j + n
    return "".join(out)


# 候补設計（night86_mine/probe 実数に基づく）
CANDIDATES = {
    "hazaru_mono":   {"kana": "はざる者", "repl": "わざる者", "guard": (), "longer": (),
                      "tag": "収候補：N72 拍板待ち はざる者 2 行＋N84 rerun 追加 4 行＝6 行 0 変差"
                             "（kanji 含み key＝M 何のごとし 前例・L はざる接続族と同型）"},
    "bekarazaru":    {"kana": "べからざる", "repl": "可からざる", "guard": ("可",), "longer": (),
                      "tag": "べからざる→可からざる（未試行族・guard 可）"},
    "tari_se":      {"kana": "たりせ", "repl": "為ら", "guard": ("爲", "為"), "longer": (),
                      "tag": "収候補：白文 爲 のエンジン完了形 たり 出力→exp 為ら（6 行全改善 0 変差・"
                             "guard 爲/爲 新旧両形並查＝N72 移交①成文执行）"},
    "nakika":       {"kana": "なきか", "repl": "莫し", "guard": ("莫",), "longer": (),
                      "tag": "収候補：ことなきか→こと莫し（白文 莫〜構文の反語疑問形 読み替え・"
                             "3 行全改善 0 変差・guard 莫＝M 何のごとく→奈何ぞ 3 行先例）"},
    "bekarazu":      {"kana": "べからず", "repl": "可からず", "guard": ("可",), "longer": (),
                      "tag": "【对照測定】N72 拒案の現基线再測（probe T2・5 変差予想）"},
    "bekarazu_zaru": {"kana": "ざるべからず", "repl": "ざる可からず", "guard": ("可",), "longer": (),
                      "tag": "【对照測定】prefix 長 key（probe T3・1 変差予想）"},
    "nakare_mokaku": {"kana": "なかれ", "repl": "莫かれ", "guard": ("莫",), "longer": (),
                      "tag": "【对照測定】N78 备选⑥（排除 guard なしでは kokyo09-5 1 変差＝拍板不通）"},
    "kotona_ki":     {"kana": "きことなかれ", "repl": "きこと莫かれ", "guard": ("莫",), "longer": (),
                      "tag": "【对照測定】N78 無益拒案再確認（1 行）"},
    "kotona_bu":     {"kana": "ぶことなかれ", "repl": "ぶこと莫かれ", "guard": ("莫",), "longer": (),
                      "tag": "【对照測定】N78 無益拒案再確認（2 行）"},
    "kotona_ku":     {"kana": "くことなかれ", "repl": "くこと莫かれ", "guard": ("莫",), "longer": (),
                      "tag": "【对照測定】N78 無益拒案再確認（2 行）"},
    "kotona_tsu":    {"kana": "つことなかれ", "repl": "つこと莫かれ", "guard": ("莫",), "longer": (),
                      "tag": "【对照測定】N78 無益拒案再確認（1 行）"},
    "kotona_bubeki": {"kana": "ぶべきことなかれ", "repl": "ぶべきこと莫かれ", "guard": ("莫",), "longer": (),
                      "tag": "【对照測定】残量 singleton（1 行）"},
    "hazaru_blank":  {"kana": "はざる", "repl": "わざる", "guard": (), "longer": (),
                      "tag": "【对照測定】はざる blanket（N69 拒案 24shihin10-4 再確認）"},
    "hazaru_ka":     {"kana": "はざるか", "repl": "わざるか", "guard": (), "longer": (),
                      "tag": "【对照測定】はざる接続 か（N72 無益拒案再確認）"},
    "shiteshimuru":  {"kana": "してしむる", "repl": "使う", "guard": ("使",), "longer": (),
                      "tag": "【对照測定】使役族（T9・1 変差 sonshi05-3＝構造差）"},
    "shiteshimu":    {"kana": "してしむ", "repl": "使う", "guard": ("使",), "longer": (),
                      "tag": "【对照測定】使役族（T10・3 変差＝構造差）"},
    "bekika":        {"kana": "べきか", "repl": "可きか", "guard": ("可",), "longer": (),
                      "tag": "【对照測定】T5（2 変差 omoi-1/mobosansen-1＝exp 自書仮名）"},
}
COMBO_ORDER = ["hazaru_mono", "tari_se", "nakika"]

EXPECTED_CLASS = {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}
HANDLED = {
    "これ", "また", "それ", "ゆゑん", "いはゆる", "たがいに", "みな", "すでに",
    "なお", "あに", "ただ", "いかん", "べし", "べく", "べからず", "ことなかれ",
    "なかれ", "ごとし", "ごとく", "ごとき", "ゆえ", "ために", "べき", "べから",
    "のみ", "もの", "とき", "ところ", "けだし", "いずくんぞ", "もし", "まさに",
    "ひて", "へて", "はず", "へず", "いやしくも", "なんぞ",
    "つひに", "がため", "はざるなり", "はざるを",
    "そく", "はあるいは", "ゆき", "はそれ", "何のごとし", "何のごとく",
    "することなかれ", "ざることなかれ", "なることなかれ", "うことなかれ",
    "ることなかれ", "はいよいよ", "いよいよ", "しばしば", "ほとんど",
    "はやや", "やや", "たま",
}
STRUCTURAL = {"して", "なりて", "するを", "みて", "すを", "なるを", "するは", "すは",
              "なるは", "するなり", "るか", "ぎて", "なるか", "ぶを", "せずして",
              "しての", "するの", "らを", "するか", "にたり", "つを", "ぶは",
              "なるなり", "すか", "すや", "すは"}
SCAN_EXCLUDE = {"はざる者", "たりせ", "なきか"}  # gate 収録済・scan 二重計上回避


def run(rows, kana_rules, d0_cache, hb_of, keep_changed=False):
    better = worse = same = 0
    changed_entries = 0
    total_old = total_new = 0
    worse_detail = []
    changed_rows = []
    segs = {"s4000": [0, 0, 0], "s3908": [0, 0, 0], "s257": [0, 0, 0]}
    for idx, r in enumerate(rows):
        rid = r["id"]
        hb = hb_of[rid]
        got0, exp, d0 = d0_cache[rid]
        new = got0
        nchg = 0
        for kana, repl, guard, longer in kana_rules:
            if guard and not any(g in hb for g in guard):
                continue
            new, n = _apply_count(new, kana, repl, longer)
            nchg += n
        d1 = d0 if new == got0 else lev(new, exp)
        total_old += d0
        total_new += d1
        sk = "s4000" if idx < 4000 else ("s3908" if idx < 7908 else "s257")
        if new != got0:
            changed_entries += 1
            delta = d1 - d0
            segs[sk][0 if delta < 0 else (1 if delta > 0 else 2)] += 1
            if keep_changed:
                changed_rows.append({"id": rid, "cls": None, "old_dist": d0, "new_dist": d1,
                                     "old_text": got0, "new_text": new, "expected": exp})
        if d1 < d0:
            better += 1
        elif d1 > d0:
            worse += 1
            worse_detail.append({"id": rid, "old": d0, "new": d1,
                                 "got": got0[:120], "exp": exp[:120], "newtext": new[:120]})
        else:
            same += 1
    n = len(rows)
    out = {"entries": n, "changed_entries": changed_entries,
           "avg_old": round(total_old / n, 3), "avg_new": round(total_new / n, 3),
           "delta": round((total_new - total_old) / n, 3),
           "better": better, "worse": worse, "same": same,
           "segs": {k: {"better": v[0], "worse": v[1], "same": v[2]} for k, v in segs.items()},
           "worse_detail": worse_detail[:40]}
    if keep_changed:
        out["changed_rows"] = changed_rows
    return out


def _apply_count(text, kana, repl, longer):
    longer = sorted(longer, key=len, reverse=True)
    out, i, n, cnt = [], 0, len(kana), 0
    while True:
        j = text.find(kana, i)
        if j < 0:
            out.append(text[i:])
            break
        tail = text[j:]
        hit = next((w for w in longer if tail.startswith(w)), None)
        if hit:
            out.append(text[i:j + len(hit)])
            i = j + len(hit)
        else:
            out.append(text[i:j] + repl)
            i = j + n
            cnt += 1
    return "".join(out), cnt


def idempotent(rows, kana_rules, d0_cache, hb_of):
    bad = 0
    for r in rows:
        hb = hb_of[r["id"]]
        got = d0_cache[r["id"]][0]
        new = got
        for kana, repl, guard, longer in kana_rules:
            if guard and not any(g in hb for g in guard):
                continue
            new, _ = _apply_count(new, kana, repl, longer)
        twice = new
        for kana, repl, guard, longer in kana_rules:
            if guard and not any(g in hb for g in guard):
                continue
            twice, _ = _apply_count(twice, kana, repl, longer)
        if twice != new:
            bad += 1
    return bad


def exact_count(rows, kana_rules, d0_cache, hb_of):
    before = after = 0
    for r in rows:
        hb = hb_of[r["id"]]
        got, exp, _d0 = d0_cache[r["id"]]
        new = got
        for kana, repl, guard, longer in kana_rules:
            if guard and not any(g in hb for g in guard):
                continue
            new, _ = _apply_count(new, kana, repl, longer)
        before += got == exp
        after += new == exp
    return before, after


def main():
    doc = json.load(open(os.path.join(EV, "night85_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序" % i
    rows8 = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    assert len(rows8) == 8165
    doc4 = json.load(open(os.path.join(EV, "night85_results_4000.json"), encoding="utf-8"))
    rows4 = doc4["results"]
    assert [r["id"] for r in rows4] == [r["id"] for r in rows8[:4000]], "4000/8165 前 4000 行不同序"
    for a, b in zip(rows4, rows8[:4000]):
        assert norm(a["udkundoku_kakikudashi"]) == norm(b["udkundoku_kakikudashi"]), \
            "4000/8165 got 不一致: %s" % a["id"]

    from backend.kundoku_rules import normalize_shinjitai, SHINJITAI_MAP
    for k, c in CANDIDATES.items():
        assert normalize_shinjitai(c["repl"]) == c["repl"], \
            "repl 非终字形: %s %s" % (k, c["repl"])
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

    # ---- 行分类＋guard 上下文（mine/probe 同款）----
    from backend.main import detect_text_type, _ruby_tail_kanbun
    cls, hb_of = {}, {}
    for r in rows8:
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
    reachable = [r for r in rows8 if cls[r["id"]] in ("engine", "rerun")]

    # ---- d0 全局缓存 ----
    t0 = time.time()
    d0_cache = {}
    for r in rows8:
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        d0_cache[r["id"]] = (got, exp, lev(got, exp))
    base_avg = round(sum(v[2] for v in d0_cache.values()) / len(d0_cache), 3)
    lines = []

    def pr(s=""):
        lines.append(s)
        print(s, flush=True)

    pr("lev 实现: %s | d0 缓存 8165 行耗时 %.0fs" % (_LEV_IMPL, time.time() - t0))
    pr("样本 8165 条 | 行分类 %s | 規則可達 %d | 基线 avgDist %.3f" % (
        dict(cc), len(reachable), base_avg))
    pr("")

    # ---- B2 pair 收集（长尾扫描用）----
    _KANA_ONLY_RE = re.compile(r"^[ぁ-ゖー]+$")
    pair_rows = collections.defaultdict(list)
    for r in reachable:
        got, exp = d0_cache[r["id"]][0], d0_cache[r["id"]][1]
        sm = SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op != "replace":
                continue
            g_, e = got[a1:a2], exp[b1:b2]
            if len(g_) >= 2 and _KANA_ONLY_RE.match(g_) and e and not _KANA_ONLY_RE.match(e[0]):
                pair_rows[(g_, e)].append(r["id"])

    # ---- 单条 0 変差门 ----
    pr("== 单条 0 変差门 ==")
    gate = {}
    for k in CANDIDATES:
        t1 = time.time()
        c = CANDIDATES[k]
        res = run(reachable, [(c["kana"], c["repl"], c["guard"], c["longer"])], d0_cache, hb_of)
        gate[k] = {"tag": c["tag"], "kana": c["kana"], "repl": c["repl"], "guard": list(c["guard"]),
                   "changed": res["changed_entries"], "better": res["better"],
                   "worse": res["worse"], "same": res["same"], "delta": res["delta"],
                   "worse_detail": res["worse_detail"][:8]}
        verdict = "収" if (res["worse"] == 0 and res["delta"] <= -0.001) else (
            "拒（変差 %d）" % res["worse"] if res["worse"] else "拒（無益 Δ%.3f）" % res["delta"])
        gate[k]["verdict"] = verdict
        pr("  %-14s 改写 %4d 行 better %4d worse %d delta %8.3f → %s (%.0fs)" % (
            k, res["changed_entries"], res["better"], res["worse"], res["delta"],
            verdict, time.time() - t1))
        for wd in res["worse_detail"][:6]:
            pr("      変差行 %s %d→%d | got %s" % (wd["id"], wd["old"], wd["new"], wd["got"][:50]))
    pr("")

    # ---- 长尾扫描：B2 uniform exp_seg pair（len>=3・既收/结构 key 除く）----
    pr("== 长尾扫描（uniform exp_seg・got 块 len>=3・発火<=120）==")
    by_key = collections.defaultdict(list)
    for (g_, e), ids in pair_rows.items():
        by_key[g_].append((e, ids))
    scan = {}
    scan_hits, scan_muchi = [], 0
    skipped_long = 0
    for g_, variants in sorted(by_key.items(), key=lambda kv: -sum(len(v[1]) for v in kv[1])):
        if len(g_) < 3 or g_ in HANDLED or g_ in STRUCTURAL or g_ in SCAN_EXCLUDE:
            continue
        if len(variants) != 1:
            continue  # exp 側異字形は単一 repl で成り立たない（N78 落选字形教训）
        e, ids = variants[0]
        e0 = e[0]
        if not e0 or not ("\u3400" <= e0 <= "\u9fff" or "\u4e00" <= e0 <= "\u4dbf"):
            continue  # exp 頭は漢字限定（B2 定義どおり）
        tot = len(ids)
        if tot < 2:
            continue
        # 発火行（key 在 got ∧ guard 命中＝head 新旧两形）
        gf = guard_forms((e[0],))
        fired = [r for r in reachable
                 if g_ in norm(r["udkundoku_kakikudashi"]) and any(f in hb_of[r["id"]] for f in gf)]
        if len(fired) > 120:
            skipped_long += 1
            continue
        if len(fired) == 0:
            continue
        better = worse = same = 0
        delta_sum = 0
        worse_ids = []
        for r in fired:
            rid = r["id"]
            got, exp, d0 = d0_cache[rid]
            new, n = _apply_count(got, g_, e, ())
            if n == 0:
                same += 1
                continue
            d1 = lev(new, exp)
            delta_sum += d1 - d0
            if d1 < d0:
                better += 1
            elif d1 > d0:
                worse += 1
                worse_ids.append(rid)
            else:
                same += 1
        delta = round(delta_sum / 8165, 3)
        entry = {"kana": g_, "exp_seg": e, "pair_rows": tot, "fired": len(fired),
                 "better": better, "worse": worse, "same": same, "delta": delta,
                 "worse_ids": worse_ids[:8]}
        scan[g_] = entry
        if worse == 0 and delta <= -0.001:
            scan_hits.append(entry)
            pr("  【scan 収候補】%-14s → %-10s pair %d 発火 %d 改善 %d 変差 0 Δ%.3f" % (
                g_, e, tot, len(fired), better, delta))
        elif worse == 0 and delta_sum < 0:
            scan_muchi += 1
        elif worse:
            pass
    pr("  scan 集計: 0 変差＆線達成 %d 件 / 0 変差＆線未達（無益） %d 件 / 発火過大 skip %d" % (
        len(scan_hits), scan_muchi, skipped_long))
    pr("")

    # ---- 收録（gate 収＋scan 収候補は人工复核対象として报告するが、本夜の combo は gate 収のみ）----
    accepted = [k for k in COMBO_ORDER if gate[k]["verdict"] == "収"]
    pr("収録候補（COMBO 順）: %s" % ",".join(accepted))
    pr("")
    combo = [(CANDIDATES[k]["kana"], CANDIDATES[k]["repl"], CANDIDATES[k]["guard"],
              CANDIDATES[k]["longer"]) for k in accepted]

    pr("== 组合（%d 条）幂等验证 ==" % len(combo))
    bad = idempotent(reachable, combo, d0_cache, hb_of)
    pr("  idempotent bad = %d（0 で冪等）" % bad)

    pr("")
    pr("== 组合双口径离线真算（reachable 8134 行基线）==")
    res8 = run(reachable, combo, d0_cache, hb_of, keep_changed=True)
    ex8 = exact_count(reachable, combo, d0_cache, hb_of)
    res4 = run(rows4, combo, d0_cache, hb_of)
    ex4 = exact_count(rows4, combo, d0_cache, hb_of)
    for tag, res, ex in (("4000", res4, ex4), ("8165(全)", res8, ex8)):
        pr("  [%s] 改写 %d 行 | better %d worse %d | avgDist %.3f→%.3f (Δ%.3f) | exact %d→%d" % (
            tag, res["changed_entries"], res["better"], res["worse"],
            res["avg_old"], res["avg_new"], res["delta"], ex[0], ex[1]))
        for sk, v in res["segs"].items():
            if v["better"] or v["worse"] or v["same"]:
                pr("      %-8s better %4d worse %d same %d" % (sk, v["better"], v["worse"], v["same"]))
    pr("")
    pr("  变差行明细: %s" % ("無し" if res8["worse"] == 0 else "要确认"))
    for wd in res8["worse_detail"][:10]:
        pr("    %s %d→%d | got %s | exp %s | new %s" % (
            wd["id"], wd["old"], wd["new"], wd["got"][:40], wd["exp"][:40], wd["newtext"][:40]))

    # 8165 全量口径（echo/no_tail 行は改写なしで d0 のまま）——README 登记値の予測
    total_old = sum(d0_cache[r["id"]][2] for r in rows8)
    changed_map = {c["id"]: c for c in res8["changed_rows"]}
    total_new = total_old + sum(c["new_dist"] - c["old_dist"] for c in res8["changed_rows"])
    ex_after_all = ex8[1] + sum(1 for r in rows8 if cls[r["id"]] in ("echo", "no_tail")
                                and d0_cache[r["id"]][0] == d0_cache[r["id"]][1])
    pr("")
    pr("== golden_8165 全量预测（echo 30＋no_tail 1 行含む・改写 0 行）==")
    pr("  avgDist %.3f → %.3f | exact %d → %d | 改写 %d 行（echo/no_tail 触らず）" % (
        round(total_old / 8165, 3), round(total_new / 8165, 3), ex8[0], ex_after_all,
        len(changed_map)))

    out = {"lev_impl": _LEV_IMPL, "baseline": "night85_results_8165.json",
           "class": dict(cc), "gate": gate, "accepted": accepted,
           "scan": {"hits": scan_hits, "much_count": scan_muchi, "skipped_long": skipped_long,
                    "entries": {k: v for k, v in scan.items()}},
           "idempotent_bad": bad,
           "combo_reachable": {k: v for k, v in res8.items() if k != "changed_rows"},
           "combo_4000": res4,
           "exact_reachable": {"before": ex8[0], "after": ex8[1]},
           "exact_4000": {"before": ex4[0], "after": ex4[1]},
           "full8165_predict": {"avg_old": round(total_old / 8165, 3),
                                "avg_new": round(total_new / 8165, 3),
                                "exact_before": ex8[0], "exact_after": ex_after_all,
                                "changed": len(changed_map)}}
    json.dump(out, open(os.path.join(EV, "night86_sim.json"), "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    json.dump(res8["changed_rows"], open(os.path.join(EV, "night86_combo_changed_rows.json"),
              "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night86_sim.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("")
    print("written: eval/night86_sim.json / night86_sim.txt / night86_combo_changed_rows.json")


if __name__ == "__main__":
    main()
