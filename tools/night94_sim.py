# -*- coding: utf-8 -*-
"""night94_sim.py — N94 Rule R 候选离线模拟＋收录判定＋组合双口径
（机制照抄 night92_sim.py：lev / apply_one / run / idempotent，
基线 = night92 真机 8165（N93 链尾・Rule Q 生效後 13.500/30/0）。

N84 fallback 行分类を反映（night94_mine/probe 同款）：規則適用対象は engine+rerun の
8134 行のみ。rerun 行の guard 上下文は尾段（main.py 現行分岐どおり）。

収録硬门（任务书②）：変差>0 一律不収。＋N69 収録線 Δ<=-0.001（無益拒）。
长尾扫描（B2 uniform exp_seg pair、len>=3、発火<=120）＝N92 枯竭の复核のみ。

输出 eval/night94_sim.json / night94_sim.txt / night94_combo_changed_rows.json。
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
    _LEV_IMPL = "纯 Python 回退（night92_eval lev と同一算法・归档と逐位一致）"


def lev(a, b):
    if _lev_c is not None:
        return _lev_c(a, b)
    return _lev_pure(a, b)


def norm(s):
    return re.sub(r"\s+", "", s or "")


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


# 候补設計（night94_mine A 表 1 字块＋night94_probe T1〜T31 実数に基づく）
CANDIDATES = {
    "yuku_shiku":   {"kana": "ゆく", "repl": "之く", "guard": ("之",), "longer": (),
                     "tag": "収候補：probe T15 12 発火 10 改善/0 変差 same 2 Δ−0.001225＝収録線達成"
                            "（(ゆ,之) 1 字块锚定 2 字长键・guard 之・新旧両形无）"},
    "saya_kyo":     {"kana": "嗟や", "repl": "嗟乎", "guard": ("乎",), "longer": (),
                     "tag": "【对照測定】probe T13 3 発火 3 改善/0 変差 Δ−0.000367＝収録線未達"
                            "（無益拒の記録・3 行しかない歎詞）"},
    # ---- 对照測定（N92/N86 拒案の現基线再測・Rule Q 生效後 37 行改写の自然変動あり）----
    "kotonaki_moki": {"kana": "ことなき", "repl": "こと莫き", "guard": ("莫",), "longer": (),
                      "tag": "【对照測定】N92 T4 禁区 2 変差（got 已含莫かれ・exp 字形混在）の再確認"},
    "rube_kan":     {"kana": "るべ", "repl": "可", "guard": ("可",), "longer": (),
                     "tag": "【对照測定】N86 T1 拒案の現基线再測"},
    "bekika":       {"kana": "べきか", "repl": "可きか", "guard": ("可",), "longer": (),
                     "tag": "【对照測定】N86 T5 拒案の現基线再測"},
    "bekarazu":     {"kana": "べからず", "repl": "可からず", "guard": ("可",), "longer": (),
                     "tag": "【对照測定】N72 拒案の現基线再測（Rule Q すべからず 16 行収録済で発火減予測）"},
    "bekarazaru":   {"kana": "べからざる", "repl": "可からざる", "guard": ("可",), "longer": (),
                     "tag": "【对照測定】N86 拒案の現基线再測"},
    "nakare_mokaku": {"kana": "なかれ", "repl": "莫かれ", "guard": ("莫",), "longer": (),
                      "tag": "【对照測定】N78 备选⑥（kokyo09-5 1 変差＝拍板不通）"},
    "wa_mashini":   {"kana": "は", "repl": "将に", "guard": ("将",), "longer": (),
                     "tag": "【对照測定】N92 T1 blanket scramble（265 発火 207 変差）の再確認"},
    "wa_imada":     {"kana": "は", "repl": "未だ", "guard": ("未",), "longer": (),
                     "tag": "【对照測定】N92 T2 blanket scramble（172 発火 131 変差）の再確認"},
}
COMBO_ORDER = ["yuku_shiku"]  # 对照測定は combo に入れない

EXPECTED_CLASS = {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}
EXPECTED_Q_DIFF = 37
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
    # N86 Rule O 既收
    "はざる者", "たりせ", "なきか",
    # N92 Rule Q 既收
    "ことなく", "すべからず",
}
STRUCTURAL = {"して", "なりて", "するを", "みて", "すを", "なるを", "するは", "すは",
              "なるなり", "なるか", "すか", "すや", "すは", "するなり", "るか", "ぎて",
              "ぶを", "せずして", "しての", "するの", "らを", "するか", "にたり", "つを",
              "ぶは"}
SCAN_EXCLUDE = {"はざる者", "たりせ", "なきか"}  # Rule O 収録済・scan 二重計上回避


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
    doc = json.load(open(os.path.join(EV, "night92_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    n91 = json.load(open(os.path.join(EV, "night91_results_8165.json"), encoding="utf-8"))["results"]
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序" % i
    rows8 = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    assert len(rows8) == 8165
    m91 = {b["id"]: b for b in n91}
    diff91 = [r["id"] for r in rows8
              if norm(r["udkundoku_kakikudashi"]) != norm(m91[r["id"]]["udkundoku_kakikudashi"])]
    assert len(diff91) == EXPECTED_Q_DIFF, \
        "night92 vs night91 got 差异 %d != Rule Q 改写 %d" % (len(diff91), EXPECTED_Q_DIFF)
    doc4 = json.load(open(os.path.join(EV, "night92_results_4000.json"), encoding="utf-8"))
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
        res = run(reachable, [(c["kana"], c["repl"], tuple(guard_forms(c["guard"])), c["longer"])], d0_cache, hb_of)
        gate[k] = {"tag": c["tag"], "kana": c["kana"], "repl": c["repl"], "guard": list(c["guard"]),
                   "changed": res["changed_entries"], "better": res["better"],
                   "worse": res["worse"], "same": res["same"], "delta": res["delta"],
                   "worse_detail": res["worse_detail"][:8]}
        verdict = "収" if (res["worse"] == 0 and res["delta"] <= -0.001) else (
            "拒（変差 %d）" % res["worse"] if res["worse"] else "拒（無益 Δ%.3f）" % res["delta"])
        gate[k]["verdict"] = verdict
        pr("  %-16s 改写 %4d 行 better %4d worse %d delta %8.3f → %s (%.0fs)" % (
            k, res["changed_entries"], res["better"], res["worse"], res["delta"],
            verdict, time.time() - t1))
        for wd in res["worse_detail"][:6]:
            pr("      変差行 %s %d→%d | got %s" % (wd["id"], wd["old"], wd["new"], wd["got"][:50]))
    pr("")

    # ---- 长尾扫描：B2 uniform exp_seg pair（len>=3・既收/结构 key 除く）＝N92 枯竭复核 ----
    pr("== 长尾扫描（uniform exp_seg・got 块 len>=3・発火<=120）＝N92 枯竭の复核 ==")
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
    pr("  scan 集計: 0 変差＆線達成 %d 件 / 0 変差＆線未達（無益） %d 件 / 発火過大 skip %d" % (
        len(scan_hits), scan_muchi, skipped_long))
    pr("")

    # ---- 収録 ----
    accepted = [k for k in COMBO_ORDER if gate[k]["verdict"] == "収"]
    pr("収録候補（COMBO 順）: %s" % (",".join(accepted) if accepted else "（なし＝零规则夜候補）"))
    pr("")
    combo = [(CANDIDATES[k]["kana"], CANDIDATES[k]["repl"], tuple(guard_forms(CANDIDATES[k]["guard"])),
              CANDIDATES[k]["longer"]) for k in accepted]

    pr("== 组合（%d 条）幂等验证 ==" % len(combo))
    bad = idempotent(reachable, combo, d0_cache, hb_of)
    pr("  idempotent bad = %d（0 で冪等）" % bad)
    if not combo:
        pr("")
        pr("零规则夜候補＝combo なし。单条门の実数を归档して終了。")
        out = {"lev_impl": _LEV_IMPL, "baseline": "night92_results_8165.json",
               "class": dict(cc), "gate": gate, "accepted": accepted,
               "scan": {"hits": scan_hits, "much_count": scan_muchi, "skipped_long": skipped_long,
                        "entries": {k: v for k, v in scan.items()}},
               "idempotent_bad": bad}
        json.dump(out, open(os.path.join(EV, "night94_sim.json"), "w", encoding="utf-8", newline="\n"),
                  ensure_ascii=False, indent=1)
        open(os.path.join(EV, "night94_sim.txt"), "w", encoding="utf-8", newline="\n").write(
            "\n".join(lines) + "\n")
        print("")
        print("written: eval/night94_sim.json / night94_sim.txt")
        return

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
    pr("== golden_8165 全量预测（echo 30＋no_tail 1 行含む・改写 %d 行）==" % len(changed_map))
    pr("  avgDist %.3f → %.3f | exact %d → %d | 改写 %d 行（echo/no_tail 触らず）" % (
        round(total_old / 8165, 3), round(total_new / 8165, 3), ex8[0], ex_after_all,
        len(changed_map)))

    out = {"lev_impl": _LEV_IMPL, "baseline": "night92_results_8165.json",
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
    json.dump(out, open(os.path.join(EV, "night94_sim.json"), "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    json.dump(res8["changed_rows"], open(os.path.join(EV, "night94_combo_changed_rows.json"),
              "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night94_sim.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("")
    print("written: eval/night94_sim.json / night94_sim.txt / night94_combo_changed_rows.json")


if __name__ == "__main__":
    main()
