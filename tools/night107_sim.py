# -*- coding: utf-8 -*-
"""night107_sim.py — Night 107 項 4 実施夜：guard 変体字拡張 C1+C4 収録前 sim 検証（night99_sim 型）。

N106 REPORT §2.1/§3 設計（項 4 実施建議）の実施前复现：判別式＝guard 変体字拡張のみ
（規則数不変・repl/链序/長词表不変・golden expected 不変）。C1＝Rule L がため→為
guard (爲,)→(爲,為)（爲＝旧字・為＝新字＝SHINJITAI_MAP 派生可・Rule M そく→即ち
(即,卽) と Rule O たりせ→為ら (爲,為) の成文慣例どおり）；C4＝Rule M 何のごとく→
奈何ぞ guard (奈,)→(奈,柰)（柰＝奈 の異体字・SHINJITAI_MAP 両方向に無いため
リテラル tuple＝N106 語料内実証・白文含柰は全域 shiki050-4 のみ）。
C2（無/罔 字拡張）と C8（tail→全文機構）は N106 実測否決＝禁实施（本 sim も測らない）。

机制照抄 tools/night104_sim.py（lev / _apply_count / run / 行分类 / guard_forms）。
sim 基线＝night104_results_8165.json / night104_results_4000.json（N105 合并链尾＝
Rule U 生效済み・N106 実測 golden 13.460/24/0・13.467/30/0 锁定済み）。N106 実測
C1 恰 1 行 rikutou37-2 44→43・C4 恰 1 行 shiki050-4 25→20・変差 0・組合 Δ8165 −0.001
（両行 4000 外）を本 sim が gate する。

硬断言（对不上 exit 2＝「停下报数」）：
  S1 行分类 engine 7916 / echo 30 / rerun 218 / no_tail 1（reachable 8134）
  S2 night104 vs night101 归档 got diff 恰 17 行＝night104_changed_rows.json の
     ID 集合（链完整性＝night104 基线＝night101＋Rule U 17 改写の証明）
  S3 基线 avgDist 4000=13.460 / 8165=13.467（归档値再計算一致）＋exact 24/30＋词库 1531
  S4 guard 双形并查証明：guard_forms(爲)=["爲","為"]（SHINJITAI 派生・Rule O 前例と
     同形）／guard_forms(奈)=["奈"]（柰 は SHINJITAI 両方向に無い＝リテラル (奈,柰)
     の根拠）／リテラル tuple は guard_forms 冪等（並查で落とさない）＋repl 终字形＋
     構造冪等（repl に kana 非含有）
  S5 C1/C4/combo：C1 恰 1 行 rikutou37-2 44→43・C4 恰 1 行 shiki050-4 25→20・
     combo 2 改写 2 改善 0 変差・Δ8165 ≈ −0.001・Δ4000 0.000・幂等 bad 0・
     对照 C3/C5（現行 guard (爲,)/(奈,)）＝0 発火（残量確認）・guard miss 行集合＝
     {rikutou37-2}/{shiki050-4} 恰 1 行（N106「唯一の guard miss 行」再確認）・
     echo/no_tail 規則不可達＋reachable hb 非空

输出 eval/night107_sim.json（全実績）＋ eval/night107_changed_rows.json（改写 2 行预测＝
night107_eval_* の逐位对照源・hb＝guard 语境同梱）＋ eval/night107_sim.txt。
用法: python -I tools/night107_sim.py
"""
import collections
import json
import os
import re
import sys
import time

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
    _LEV_IMPL = "Levenshtein C (.night72_deps)"
except Exception:  # pragma: no cover
    _lev_c = None
    _LEV_IMPL = "纯 Python 回退（night85_eval 同一算法・归档逐位一致実績）"


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


lines = []


def pr(s=""):
    lines.append(s)
    print(s, flush=True)


def gate(cond, msg):
    if not cond:
        pr("[FAIL] %s → 停下报数" % msg)
        write_out()
        sys.exit(2)


def run(rows, kana_rules, d0_cache, hb_of):
    better = worse = same = 0
    changed_entries = 0
    total_old = total_new = 0
    worse_detail = []
    changed_rows = []
    for idx, r in enumerate(rows):
        rid = r["id"]
        hb = hb_of[rid]
        got0, exp, d0 = d0_cache[rid]
        new = got0
        nchg = 0
        for kana, repl, guard, longer in kana_rules:
            if guard and hb and not any(g in hb for g in guard):
                continue
            new, n = _apply_count(new, kana, repl, longer)
            nchg += n
        d1 = d0 if new == got0 else lev(new, exp)
        total_old += d0
        total_new += d1
        if new != got0:
            changed_entries += 1
            changed_rows.append({"id": rid, "old_dist": d0, "new_dist": d1,
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
    return {"entries": n, "changed_entries": changed_entries,
            "avg_old": round(total_old / n, 3), "avg_new": round(total_new / n, 3),
            "delta": round((total_new - total_old) / n, 3),
            "better": better, "worse": worse, "same": same,
            "worse_detail": worse_detail, "changed_rows": changed_rows}


def idempotent(rows, kana_rules, d0_cache, hb_of):
    bad = 0
    for r in rows:
        hb = hb_of[r["id"]]
        got = d0_cache[r["id"]][0]
        new = got
        for kana, repl, guard, longer in kana_rules:
            if guard and hb and not any(g in hb for g in guard):
                continue
            new, _ = _apply_count(new, kana, repl, longer)
        twice = new
        for kana, repl, guard, longer in kana_rules:
            if guard and hb and not any(g in hb for g in guard):
                continue
            twice, _ = _apply_count(twice, kana, repl, longer)
        if twice != new:
            bad += 1
    return bad


EXPECTED_CLASS = {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}

# N106 §2.1 実測（C1/C4 各恰好 1 行・変差 0・両行 4000 外）
EXPECTED = {
    "c1": {"id": "rikutou37-2", "old": 44, "new": 43},
    "c4": {"id": "shiki050-4", "old": 25, "new": 20},
}
COMBO_IDS = ["rikutou37-2", "shiki050-4"]


def close(x, y, tol=0.0005):
    return abs(x - y) <= tol


def main():
    t_start = time.time()
    sim = {"script": "tools/night107_sim.py", "night": 107,
           "mode": "項 4 実施夜 guard 変体字拡張 C1+C4 sim 検証（N106 §2.1/§3 設計の実施前复现・規則数不変）"}

    pr("== S3 词库 import 实证（不動確認）==")
    import backend.glossary_lexicon as gl
    import backend.glossary_lexicon_extra as gle
    import backend.glossary_lexicon_extra2 as gle2
    core_n = len(gl.GLOSSARY_LEXICON)
    old_n = getattr(gl, "_OLD_SIZE", None)
    extra_n = len(gle.as_dicts())
    ex2_n = len(gle2.LEXICON_EXTRA2)
    ordered_n = len(gle2._ORDERED_ALL)
    lex = {"core": core_n, "core_old_size": old_n, "extra": extra_n,
           "extra2": ex2_n, "ordered_all": ordered_n}
    pr("  %s → 209+291+1031=%s" % (lex, ordered_n))
    sim["lexicon"] = lex
    gate(old_n == 209 and core_n == 500 and extra_n == 291 and ex2_n == 1031
         and ordered_n == 1531, "词库实测 %s != 209+291+1031=1531" % lex)

    # ---------- 基准 ----------
    doc8 = json.load(open(os.path.join(EV, "night104_results_8165.json"), encoding="utf-8"))
    rows8 = [r for r in doc8["results"] if r.get("udkundoku_kakikudashi") is not None]
    gate(len(rows8) == 8165, "night104_results_8165 行数 %d != 8165" % len(rows8))
    doc4 = json.load(open(os.path.join(EV, "night104_results_4000.json"), encoding="utf-8"))
    rows4 = doc4["results"]
    gate([r["id"] for r in rows4] == [r["id"] for r in rows8[:4000]],
         "night104_results_4000 与 8165 前 4000 行序不一致")

    # S2 链完整性：night104 归档 ＝ night101 归档 ＋ Rule U 17 改写行（ID 集合一致）
    doc8_n101 = json.load(open(os.path.join(EV, "night101_results_8165.json"),
                               encoding="utf-8"))["results"]
    m101 = {b["id"]: b for b in doc8_n101}
    diff101 = [r["id"] for r in rows8
               if norm(r["udkundoku_kakikudashi"]) != norm(m101[r["id"]]["udkundoku_kakikudashi"])]
    u_rows = json.load(open(os.path.join(EV, "night104_changed_rows.json"), encoding="utf-8"))
    u_ids = sorted(c["id"] for c in u_rows)
    pr("== S2 链完整性：night104 vs night101 归档 got diff %d 行 vs Rule U 改写 %d 行 =="
       % (len(diff101), len(u_ids)))
    gate(len(diff101) == 17 and sorted(diff101) == u_ids,
         "night104/night101 归档差异 %d 行 != Rule U 17 改写行（基线链不健全）" % len(diff101))
    sim["n104_vs_n101_diff_ids"] = sorted(diff101)

    from backend.kundoku_rules import normalize_shinjitai, SHINJITAI_MAP
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

    # 行分类＋guard 上下文（night98_audit 同款）
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
    pr("== S1 行分类 %s（期待 %s）==" % (dict(cc), EXPECTED_CLASS))
    sim["class"] = dict(cc)
    gate(dict(cc) == EXPECTED_CLASS, "行分类実数 %s != 期待 %s" % (dict(cc), EXPECTED_CLASS))
    reachable = [r for r in rows8 if cls[r["id"]] in ("engine", "rerun")]
    pr("  reachable %d 行" % len(reachable))

    # S6：echo/no_tail 規則不可達＋engine/rerun hb 非空（N102 教训の適用）
    unreach_key = [r["id"] for r in rows8 if cls[r["id"]] in ("echo", "no_tail")
                   and ("がため" in norm(r["udkundoku_kakikudashi"])
                        or "何のごとく" in norm(r["udkundoku_kakikudashi"]))]
    gate(not unreach_key, "S6 echo/no_tail 行に がため/何のごとく 出現（規則可達化で sim/実跑乖離の恐れ）: %s"
         % unreach_key[:8])
    empty_hb = [r["id"] for r in reachable if not hb_of[r["id"]]]
    gate(not empty_hb, "S6 engine/rerun に hb 空行（guard 語义乖離の恐れ）: %s" % empty_hb[:8])
    pr("== S6 echo/no_tail 規則不可達（がため/何のごとく 0 行）＋reachable 全行 hb 非空 ✓ ==")

    d0_cache = {}
    for r in rows8:
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        d0_cache[r["id"]] = (got, exp, lev(got, exp))
    base_avg8 = round(sum(v[2] for v in d0_cache.values()) / 8165, 3)
    base_avg4 = round(sum(d0_cache[r["id"]][2] for r in rows4) / 4000, 3)
    exact_base8 = sum(1 for v in d0_cache.values() if v[2] == 0)
    exact_base4 = sum(1 for r in rows4 if d0_cache[r["id"]][2] == 0)
    pr("  基线 avgDist 4000=%.3f 8165=%.3f（归档 13.460/13.467）exact %d/%d（归档 24/30）"
       % (base_avg4, base_avg8, exact_base4, exact_base8))
    sim["baseline"] = {"avg4000": base_avg4, "avg8165": base_avg8,
                       "exact4000": exact_base4, "exact8165": exact_base8}
    gate(close(base_avg4, 13.460), "基线 avgDist 4000 %.3f != 13.460" % base_avg4)
    gate(close(base_avg8, 13.467), "基线 avgDist 8165 %.3f != 13.467" % base_avg8)
    gate(exact_base4 == 24 and exact_base8 == 30,
         "基线 exact %d/%d != 24/30" % (exact_base4, exact_base8))

    # ---------- S4 guard 双形并查証明 ----------
    pr("")
    pr("== S4 guard 双形并查証明 ==")
    gf_i = guard_forms(("為",))
    gf_i_old = guard_forms(("爲",))
    pr("  guard_forms(爲)=%s（SHINJITAI 派生可・Rule O たりせ (爲,為) 前例と同形）" % gf_i_old)
    gate(gf_i_old == ["爲", "為"], "guard_forms(爲) %s != ['爲','為']" % gf_i_old)
    gf_n = guard_forms(("奈",))
    pr("  guard_forms(奈)=%s（柰 は SHINJITAI 両方向に無い＝リテラル (奈,柰) の根拠）" % gf_n)
    gate(gf_n == ["奈"], "guard_forms(奈) %s != ['奈']（柰 派生の有無が変わった）" % gf_n)
    gate("柰" not in old_to_new and "柰" not in new_to_old,
         "柰 が SHINJITAI_MAP に現れた（リテラル tuple 前提崩れ）")
    # リテラル tuple は guard_forms 冪等（並查で字形を落とさない）
    gate(guard_forms(("爲", "為")) == ["爲", "為"],
         "guard_forms((爲,為)) %s != ['爲','為']" % guard_forms(("爲", "為")))
    gate(guard_forms(("奈", "柰")) == ["奈", "柰"],
         "guard_forms((奈,柰)) %s != ['奈','柰']" % guard_forms(("奈", "柰")))
    sim["guard_forms_proof"] = {"wei": gf_i_old, "nai": gf_n,
                                "literal_idempotent": True}

    # ---------- 候补表（guard 変体字拡張のみ・repl/長词表不変） ----------
    CANDIDATES = {
        "c1": {"kana": "がため", "repl": "為", "guard": ("爲", "為"), "longer": (),
               "tag": "C1 がため→為 guard 変体字 (爲,為)（N106 §2.1 採用候補）"},
        "c4": {"kana": "何のごとく", "repl": "奈何ぞ", "guard": ("奈", "柰"), "longer": (),
               "tag": "C4 何のごとく→奈何ぞ guard 変体字 (奈,柰)（柰＝異体字リテラル）"},
        "c3_contrast": {"kana": "がため", "repl": "為", "guard": ("爲",), "longer": (),
                        "tag": "C3 对照＝現行 guard (爲,)（残量確認・0 発火期待）"},
        "c5_contrast": {"kana": "何のごとく", "repl": "奈何ぞ", "guard": ("奈",), "longer": (),
                        "tag": "C5 对照＝現行 guard (奈,)（残量確認・0 発火期待）"},
    }
    for k, c in CANDIDATES.items():
        gate(normalize_shinjitai(c["repl"]) == c["repl"], "repl 非终字形: %s" % k)
        gate(c["kana"] not in c["repl"], "構造冪等：repl %s に kana %s 含有" % (c["repl"], c["kana"]))

    def rules_of(keys):
        return [(CANDIDATES[k]["kana"], CANDIDATES[k]["repl"],
                 tuple(CANDIDATES[k]["guard"]), CANDIDATES[k]["longer"])
                for k in keys]

    def measure(keys):
        kana_rules = rules_of(keys)
        res8 = run(reachable, kana_rules, d0_cache, hb_of)
        res4 = run(rows4, kana_rules, d0_cache, hb_of)
        chg8 = {cr["id"]: cr for cr in res8["changed_rows"]}
        # 8165 全口径（reachable 外 31 行は d0 据置・night104_sim gate 同款）
        total_old8 = sum(d0_cache[r["id"]][2] for r in rows8)
        full_new8 = total_old8 + sum(cr["new_dist"] - cr["old_dist"]
                                     for cr in res8["changed_rows"])
        pe8 = (sum(1 for r in rows8 if r["id"] not in chg8 and d0_cache[r["id"]][2] == 0)
               + sum(1 for cr in res8["changed_rows"] if cr["new_dist"] == 0))
        chg4 = {cr["id"]: cr for cr in res4["changed_rows"]}
        pe4 = (sum(1 for r in rows4 if r["id"] not in chg4 and d0_cache[r["id"]][2] == 0)
               + sum(1 for cr in res4["changed_rows"] if cr["new_dist"] == 0))
        bad = idempotent(reachable, kana_rules, d0_cache, hb_of)
        enriched = []
        for cr in res8["changed_rows"]:
            e = dict(cr)
            e["hb"] = hb_of[cr["id"]]
            e["cls"] = cls[cr["id"]]
            enriched.append(e)
        return {"keys": keys, "changed": res8["changed_entries"],
                "better": res8["better"], "worse": res8["worse"], "same": res8["same"],
                "changed4000": res4["changed_entries"],
                "better4000": res4["better"], "worse4000": res4["worse"],
                "delta8165": round((full_new8 - total_old8) / 8165, 3),
                "delta4000": res4["delta"],
                "full8165": {"avg_old": round(total_old8 / 8165, 3),
                             "avg_new": round(full_new8 / 8165, 3),
                             "delta": round((full_new8 - total_old8) / 8165, 3)},
                "full4000": {"avg_old": res4["avg_old"], "avg_new": res4["avg_new"],
                             "delta": res4["delta"]},
                "pred_exact8165": pe8, "pred_exact4000": pe4,
                "idempotent_bad": bad,
                "worse_ids": sorted(wd["id"] for wd in res8["worse_detail"]),
                "worse_ids4000": sorted(wd["id"] for wd in res4["worse_detail"]),
                "changed_rows": enriched}

    pr("")
    pr("== S5 測定（C1/C4 単条＋C3/C5 現行对照＋combo）==")
    t1 = time.time()
    m_c1 = measure(["c1"])
    m_c4 = measure(["c4"])
    m_c3 = measure(["c3_contrast"])
    m_c5 = measure(["c5_contrast"])
    m_combo = measure(["c1", "c4"])
    pr("  (%.0fs)" % (time.time() - t1))
    for label, m in (("c1", m_c1), ("c4", m_c4), ("c3対", m_c3), ("c5対", m_c5), ("combo", m_combo)):
        pr("  %-6s 改写 %3d(4000内 %2d) better %d/%d worse %d/%d same %d | "
           "Δ8165 %.3f Δ4000 %.3f | avg 8165 %.3f→%.3f 4000 %.3f→%.3f | 幂等 bad %d"
           % (label, m["changed"], m["changed4000"], m["better"], m["better4000"],
              m["worse"], m["worse4000"], m["same"],
              m["delta8165"], m["delta4000"],
              m["full8165"]["avg_old"], m["full8165"]["avg_new"],
              m["full4000"]["avg_old"], m["full4000"]["avg_new"], m["idempotent_bad"]))
        for cr in m["changed_rows"][:4]:
            pr("      改写 %s %d→%d | %s → %s | got頭 %s"
               % (cr["id"], cr["old_dist"], cr["new_dist"],
                  cr["old_text"][:28], cr["new_text"][:28], cr["old_text"][:28]))

    # ---------- 硬断言（N106 §2.1 実測との逐位对照） ----------
    pr("")
    pr("== 硬断言（N106 §2.1 C1/C4 全域実測との逐位对照）==")
    g = m_c1
    e = EXPECTED["c1"]
    gate(g["changed"] == 1 and g["changed_rows"][0]["id"] == e["id"],
         "C1 発火 %s != 恰 1 行 %s" % ([c["id"] for c in g["changed_rows"]], e["id"]))
    cr1 = g["changed_rows"][0]
    gate((cr1["old_dist"], cr1["new_dist"]) == (e["old"], e["new"]),
         "C1 d0→d1 %s != %s" % ((cr1["old_dist"], cr1["new_dist"]), (e["old"], e["new"])))
    gate(g["changed4000"] == 0 and g["worse_ids4000"] == [],
         "C1 4000 内改写 %d != 0（両行 4000 外前提）" % g["changed4000"])
    g = m_c4
    e = EXPECTED["c4"]
    gate(g["changed"] == 1 and g["changed_rows"][0]["id"] == e["id"],
         "C4 発火 %s != 恰 1 行 %s" % ([c["id"] for c in g["changed_rows"]], e["id"]))
    cr4 = g["changed_rows"][0]
    gate((cr4["old_dist"], cr4["new_dist"]) == (e["old"], e["new"]),
         "C4 d0→d1 %s != %s" % ((cr4["old_dist"], cr4["new_dist"]), (e["old"], e["new"])))
    gate(g["changed4000"] == 0 and g["worse_ids4000"] == [],
         "C4 4000 内改写 %d != 0（両行 4000 外前提）" % g["changed4000"])
    gate(m_c3["changed"] == 0, "C3 对照（現行 guard 爲）発火 %d != 0（残量確認不成立）" % m_c3["changed"])
    gate(m_c5["changed"] == 0, "C5 对照（現行 guard 奈）発火 %d != 0（残量確認不成立）" % m_c5["changed"])

    # guard miss 残量集合＝N106「唯一の guard miss 行」再確認
    miss1 = sorted(r["id"] for r in reachable
                   if "がため" in d0_cache[r["id"]][0] and "爲" not in hb_of[r["id"]])
    miss2 = sorted(r["id"] for r in reachable
                   if "何のごとく" in d0_cache[r["id"]][0] and "奈" not in hb_of[r["id"]])
    pr("  guard miss 残量：C1(がため∧爲無し)=%s・C4(何のごとく∧奈無し)=%s" % (miss1, miss2))
    gate(miss1 == ["rikutou37-2"], "C1 guard miss 残量 %s != ['rikutou37-2']" % miss1)
    gate(miss2 == ["shiki050-4"], "C4 guard miss 残量 %s != ['shiki050-4']" % miss2)
    sim["guard_miss_c1"] = miss1
    sim["guard_miss_c4"] = miss2

    g = m_combo
    gate(g["changed"] == 2 and g["better"] == 2 and g["worse"] == 0,
         "combo %d 改写 %d 改善 %d 変差 != 2/2/0" % (g["changed"], g["better"], g["worse"]))
    gate(g["worse_ids"] == [], "combo 変差行 %s != []（N106 変差 0 実測）" % g["worse_ids"])
    gate(sorted(c["id"] for c in g["changed_rows"]) == COMBO_IDS,
         "combo 改写行 %s != %s" % (sorted(c["id"] for c in g["changed_rows"]), COMBO_IDS))
    gate(g["idempotent_bad"] == 0, "combo 幂等 bad %d != 0" % g["idempotent_bad"])
    gate(close(g["delta8165"], -0.001), "combo Δ8165 %.3f != -0.001（N106 実測）" % g["delta8165"])
    gate(close(g["delta4000"], 0.000), "combo Δ4000 %.3f != 0.000（両行 4000 外）" % g["delta4000"])
    gate(g["changed4000"] == 0, "combo 4000 内改写 %d != 0" % g["changed4000"])
    gate(g["pred_exact4000"] == 24 and g["pred_exact8165"] == 30,
         "combo 预测 exact %d/%d != 24/30" % (g["pred_exact4000"], g["pred_exact8165"]))
    pr("  全硬断言 PASS：C1 rikutou37-2 44→43・C4 shiki050-4 25→20・combo 変差 0・"
       "Δ8165 %.3f Δ4000 %.3f" % (g["delta8165"], g["delta4000"]))

    # ---------- 输出 ----------
    sim["gates"] = {
        "combo": {k: v for k, v in m_combo.items() if k != "changed_rows"},
        "c1": {k: v for k, v in m_c1.items() if k != "changed_rows"},
        "c4": {k: v for k, v in m_c4.items() if k != "changed_rows"},
        "c3_contrast": {k: v for k, v in m_c3.items() if k != "changed_rows"},
        "c5_contrast": {k: v for k, v in m_c5.items() if k != "changed_rows"},
    }
    sim["lev_impl"] = _LEV_IMPL
    sim["baseline"]["archive"] = ("night104_results_8165.json / night104_results_4000.json"
                                  "（N105 合并链尾＝Rule U 生效済み）")
    sim["elapsed_sec"] = round(time.time() - t_start)
    sim["verdict"] = "PASS"

    out_changed = os.path.join(EV, "night107_changed_rows.json")
    json.dump(m_combo["changed_rows"], open(out_changed, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    out_json = os.path.join(EV, "night107_sim.json")
    json.dump(sim, open(out_json, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night107_sim.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    pr("")
    pr("written: eval/night107_sim.json / night107_changed_rows.json / night107_sim.txt")
    pr("PRED_4000=%d PRED_8165=%d | PRED_EXACT_4000=%d PRED_EXACT_8165=%d"
       % (m_combo["changed4000"], m_combo["changed"],
          m_combo["pred_exact4000"], m_combo["pred_exact8165"]))
    pr("elapsed %.0fs" % sim["elapsed_sec"])


def write_out():
    try:
        open(os.path.join(EV, "night107_sim.txt"), "w", encoding="utf-8", newline="\n").write(
            "\n".join(lines) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
