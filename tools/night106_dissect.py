# -*- coding: utf-8 -*-
"""night106_dissect.py — Night 106 (a)：項 4 两行全文解剖＋候補判別式全域実測（报告-only）。

任务书（N105 §5 移交・N98 §3 项 4/5・機構設計夜 4/5）：只設計＋离线実測、不改產品代碼、
不收規則、不動 golden expected。基線＝night104_results_8165/4000.json（N105 登記口径）。

(a) 項 4 两行（rerun 行）全文解剖：
  rikutou37-2  got 残量 がため（Rule L がため→為 guard 爲 未発火）
  shiki050-4   got 残量 何のごとく（Rule M 何のごとく→奈何ぞ guard 奈 未発火）
候補判別式 × 全域発火集（発火行数・改善／変差・是否只命中目標行）：
  C1  がため→為    guard (爲,為)   变体字扩充（新字体並查＝Rule M (即,卽) 成文慣例）
  C2  がため→為    guard (爲,無,罔) guard 字扩充（無/罔）
  C3  がため→為    guard (爲)      現行（残量確認＝0 発火）
  C4  何のごとく→奈何ぞ guard (奈,柰) 变体字扩充（柰＝奈異体・语料内查证）
  C5  何のごとく→奈何ぞ guard (奈)   現行（残量確認＝0 発火）
  C6  何のごとく→奈何ぞ guard (奈,無,罔) guard 字扩充（shiki050-4 tail 无無罔＝不命中予想）
  C7  何のごとし→奈何 guard (奈,柰)  兄弟键（残量 0 確認）
  C8  tail→全文 guard 上下文機構（rerun 218 行 blast radius・全 pipeline 実測）
  C9  tail 句型判別（「為之奈何」phrase 級 vs 為 containment 級＝同発火集確認）
硬断言（对不上 exit 2＝停下报数）：
  S1 行分类 engine 7916 / echo 30 / rerun 218 / no_tail 1
  S2 基线 avgDist 4000=13.460 / 8165=13.467＋exact 24/30＋词库 1531
  S3 柰 全域白文出現＝1 行（shiki050-4 のみ＝柰→奈 guard 拡張の全域波及 1 行）
出力 eval/night106_dissect.json ＋ eval/night106_dissect.txt。
用法: python -I tools/night106_dissect.py
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
sys.path.insert(0, os.path.join(ROOT, ".night72_deps"))
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


def _apply_count(text, kana, repl, longer=()):
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
        sim["verdict"] = "FAIL"
        write_out()
        sys.exit(2)


def close(x, y, tol=0.0005):
    return abs(x - y) <= tol


def write_out():
    try:
        open(os.path.join(EV, "night106_dissect.txt"), "w", encoding="utf-8",
             newline="\n").write("\n".join(lines) + "\n")
    except Exception:
        pass


EXPECTED_CLASS = {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}


def run_candidate(rows, kana, repl, guard_forms_list, d0_cache, hb_of, cls):
    """guard 付き単規則走查（製品コード同一语义・echo/no_tail は規則不可達）。"""
    out = []
    for r in rows:
        rid = r["id"]
        if cls[rid] not in ("engine", "rerun"):
            continue
        hb = hb_of[rid]
        if guard_forms_list and hb and not any(g in hb for g in guard_forms_list):
            continue
        got0, exp, d0 = d0_cache[rid]
        new, n = _apply_count(got0, kana, repl)
        if n:
            out.append({"id": rid, "cls": cls[rid], "n_sites": n, "got": got0,
                        "new": new, "exp": exp, "d0": d0, "d1": lev(new, exp)})
    return out


def report_run(tag, chg, d0_cache, hb_of, cls, rows4):
    better = [c for c in chg if c["d1"] < c["d0"]]
    worse = [c for c in chg if c["d1"] > c["d0"]]
    same = [c for c in chg if c["d1"] == c["d0"]]
    pr("  %s: 発火 %d 行 | better %d / worse %d / same %d" % (
        tag, len(chg), len(better), len(worse), len(same)))
    for c in chg:
        pr("    %-16s [%s・sites %d] %d→%d %s" % (
            c["id"], c["cls"], c["n_sites"], c["d0"], c["d1"],
            "BETTER" if c["d1"] < c["d0"] else ("WORSE" if c["d1"] > c["d0"] else "SAME")))
        if c["d1"] != c["d0"]:
            pr("      got→new: %r" % c["new"][:100])
            pr("      exp     : %r" % c["exp"][:100])
    return {"fired": len(chg), "better": [c["id"] for c in better],
            "worse": [c["id"] for c in worse], "same": [c["id"] for c in same],
            "per_row": {c["id"]: [c["d0"], c["d1"]] for c in chg}}


def main():
    global sim
    t_start = time.time()
    sim = {"script": "tools/night106_dissect.py", "night": 106,
           "mode": "項 4 两行解剖＋候補判別式全域実測（報告-only・不収録・製品コード零改动）",
           "verdict": None}

    pr("== S2 词库 import 实证（不動確認）==")
    import backend.glossary_lexicon as gl
    import backend.glossary_lexicon_extra as gle
    import backend.glossary_lexicon_extra2 as gle2
    lex = {"core": len(gl.GLOSSARY_LEXICON), "core_old_size": getattr(gl, "_OLD_SIZE", None),
           "extra": len(gle.as_dicts()), "extra2": len(gle2.LEXICON_EXTRA2),
           "ordered_all": len(gle2._ORDERED_ALL)}
    pr("  %s" % lex)
    sim["lexicon"] = lex
    gate(lex["core_old_size"] == 209 and lex["core"] == 500 and lex["extra"] == 291
         and lex["extra2"] == 1031 and lex["ordered_all"] == 1531,
         "词库実測 %s != 209+291+1031=1531" % lex)

    # ---------- 基准（基線＝night104 归档） ----------
    doc8 = json.load(open(os.path.join(EV, "night104_results_8165.json"), encoding="utf-8"))
    rows8 = [r for r in doc8["results"] if r.get("udkundoku_kakikudashi") is not None]
    gate(len(rows8) == 8165, "night104_results_8165 行数 %d != 8165" % len(rows8))
    doc4 = json.load(open(os.path.join(EV, "night104_results_4000.json"), encoding="utf-8"))
    rows4 = doc4["results"]
    gate([r["id"] for r in rows4] == [r["id"] for r in rows8[:4000]],
         "night104_results_4000 与 8165 前 4000 行序不一致")

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

    # 行分类＋guard 上下文（night98_audit/night103_sim 同款）
    from backend.main import detect_text_type, _ruby_tail_kanbun
    cls, hb_of, hb_full_of, tail_raw_of = {}, {}, {}, {}
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
            hb_full_of[r["id"]] = norm(raw)
            tail_raw_of[r["id"]] = tail
        else:
            cls[r["id"]] = "engine"
            hb_of[r["id"]] = norm(raw)
            hb_full_of[r["id"]] = norm(raw)
            tail_raw_of[r["id"]] = ""
    cc = collections.Counter(cls.values())
    pr("== S1 行分类 %s（期待 %s）==" % (dict(cc), EXPECTED_CLASS))
    sim["class"] = dict(cc)
    gate(dict(cc) == EXPECTED_CLASS, "行分类実数 %s != 期待 %s" % (dict(cc), EXPECTED_CLASS))
    reachable = [r for r in rows8 if cls[r["id"]] in ("engine", "rerun")]
    pr("  reachable %d 行" % len(reachable))

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
                       "exact4000": exact_base4, "exact8165": exact_base8,
                       "archive": "night104_results_8165.json / night104_results_4000.json"}
    gate(close(base_avg4, 13.460), "基线 avgDist 4000 %.3f != 13.460" % base_avg4)
    gate(close(base_avg8, 13.467), "基线 avgDist 8165 %.3f != 13.467" % base_avg8)
    gate(exact_base4 == 24 and exact_base8 == 30,
         "基线 exact %d/%d != 24/30" % (exact_base4, exact_base8))

    # ---------- (a) 两行全文解剖 ----------
    pr("")
    pr("== (a) 項 4 两行全文解剖（rikutou37-2・shiki050-4＝rerun 行）==")
    dis = {}
    for rid in ("rikutou37-2", "shiki050-4"):
        r = next(r for r in rows8 if r["id"] == rid)
        raw = r["hakubun"] or ""
        tail = tail_raw_of[rid]
        got = r["udkundoku_kakikudashi"] or ""
        exp = r["expected_kakikudashi"] or ""
        keepers_tail = [g for g in ("莫", "勿", "毋", "罔", "無", "爲", "為", "奈", "柰")
                        if g in norm(tail)]
        keepers_full = [g for g in ("莫", "勿", "毋", "罔", "無", "爲", "為", "奈", "柰")
                        if g in norm(raw)]
        entry = {"cls": cls[rid], "tail_raw": tail, "tail_norm": norm(tail),
                 "keepers_in_tail": keepers_tail, "keepers_in_full": keepers_full,
                 "got": got, "expected": exp,
                 "hb_first_paren_pos": raw.find("（")}
        pr("  --- %s [%s] ---" % (rid, cls[rid]))
        pr("  tail（rerun guard 上下文）: %s" % tail)
        pr("  tail 守り字 census: %s" % keepers_tail)
        pr("  全文守り字 census: %s（全文 vs tail 差分＝%s）"
           % (keepers_full, [g for g in keepers_full if g not in keepers_tail]))
        for key in ("がため", "何のごとく"):
            if key in norm(got):
                i = norm(got).find(key)
                pr("  got 含 %r @%d ctx=%r" % (key, i, norm(got)[max(0, i - 14):i + 20]))
        for key in ("為", "奈何", "柰何"):
            if key in norm(exp):
                i = norm(exp).find(key)
                pr("  exp 含 %r @%d ctx=%r" % (key, i, norm(exp)[max(0, i - 14):i + 20]))
        dis[rid] = entry
    gate("がため" in norm(dis["rikutou37-2"]["got"]), "rikutou37-2 got 无 がため＝残量消失?")
    gate("何のごとく" in norm(dis["shiki050-4"]["got"]), "shiki050-4 got 无 何のごとく＝残量消失?")
    gate("為" in dis["rikutou37-2"]["tail_norm"] and "爲" not in dis["rikutou37-2"]["tail_norm"],
         "rikutou37-2 tail 无 為（新字）或含 爲（旧字）＝C1 前提崩れ")
    gate("柰" in dis["shiki050-4"]["tail_norm"] and "奈" not in dis["shiki050-4"]["tail_norm"],
         "shiki050-4 tail 无 柰 或含 奈＝C4 前提崩れ")
    sim["dissect"] = dis

    # ---------- 柰/奈 语料内查证 ----------
    pr("")
    pr("== 柰＝奈 異体 查证（语料内対照・ネット不使用）==")
    nai_rows = [r["id"] for r in rows8 if "柰" in hb_full_of[r["id"]]]
    pr("  白文含 柰 の行（全文）: %s（total %d）" % (nai_rows, len(nai_rows)))
    for rid in nai_rows:
        exp = d0_cache[rid][1]
        pr("  %s: exp 奈何=%s got 何のごとく=%s | exp=%r"
           % (rid, "奈何" in exp, "何のごとく" in norm(d0_cache[rid][0]), exp[:60]))
    gate(nai_rows == ["shiki050-4"],
         "S3 柰 全域白文出現 %s != ['shiki050-4']（＝C4 全域波及 1 行前提）" % nai_rows)
    pr("  → shiki050-4 白文 柰何 ↔ exp 奈何ぞ＝语料内 1:1 対応（柰＝奈 異体の実証）")
    sim["nai_evidence"] = {"rows": nai_rows,
                           "note": "柰＝奈異体・语料内唯一出現＝guard (奈,柰) 全域波及 1 行"}

    # ---------- 候補判別式 × 全域発火集 ----------
    pr("")
    pr("== 候補判別式 × 全域発火集（reachable 8134 行走查）==")
    gf_oe = guard_forms(("爲",))          # ['爲','爲'?] → 爲 old-form expansion
    pr("  guard_forms(爲)=%s" % gf_oe)
    cands = {}
    chg = run_candidate(reachable, "がため", "為", ("爲",), d0_cache, hb_of, cls)
    cands["C3_gatame_guard_ue_current"] = report_run("C3 がため→為 guard(爲)現行",
                                                     chg, d0_cache, hb_of, cls, rows4)
    gate(len(chg) == 0, "C3 現行 guard(爲) 発火 %d != 0（残量前提崩れ）" % len(chg))

    chg = run_candidate(reachable, "がため", "為", ("爲", "為"), d0_cache, hb_of, cls)
    cands["C1_gatame_guard_ue_shin"] = report_run("C1 がため→為 guard(爲,為)变体字",
                                                  chg, d0_cache, hb_of, cls, rows4)
    gate([c["id"] for c in chg] == ["rikutou37-2"],
         "C1 発火集 %s != ['rikutou37-2']（只命中目標行前提）" % [c["id"] for c in chg])

    chg = run_candidate(reachable, "がため", "為", ("爲", "無", "罔"), d0_cache, hb_of, cls)
    cands["C2_gatame_guard_muo"] = report_run("C2 がため→為 guard(爲,無,罔)字扩充",
                                              chg, d0_cache, hb_of, cls, rows4)
    gate([c["id"] for c in chg] == ["rikutou37-2"],
         "C2 発火集 %s != ['rikutou37-2']" % [c["id"] for c in chg])
    pr("  → C2 与 C1 同発火集（ rikutou37-2 tail 恰含 無 の単なる偶然・语义的根拠なし＝不採）")

    chg = run_candidate(reachable, "何のごとく", "奈何ぞ", ("奈",), d0_cache, hb_of, cls)
    cands["C5_nanogotoku_guard_nai_current"] = report_run("C5 何のごとく→奈何ぞ guard(奈)現行",
                                                          chg, d0_cache, hb_of, cls, rows4)
    gate(len(chg) == 0, "C5 現行 guard(奈) 発火 %d != 0（残量前提崩れ）" % len(chg))

    chg = run_candidate(reachable, "何のごとく", "奈何ぞ", ("奈", "柰"), d0_cache, hb_of, cls)
    cands["C4_nanogotoku_guard_nai_dai"] = report_run("C4 何のごとく→奈何ぞ guard(奈,柰)变体字",
                                                      chg, d0_cache, hb_of, cls, rows4)
    gate([c["id"] for c in chg] == ["shiki050-4"],
         "C4 発火集 %s != ['shiki050-4']" % [c["id"] for c in chg])

    chg = run_candidate(reachable, "何のごとく", "奈何ぞ", ("奈", "無", "罔"), d0_cache, hb_of, cls)
    cands["C6_nanogotoku_guard_nai_muo"] = report_run("C6 何のごとく→奈何ぞ guard(奈,無,罔)字扩充",
                                                      chg, d0_cache, hb_of, cls, rows4)
    gate(len(chg) == 0, "C6 発火 %d != 0（shiki050-4 tail 无無罔＝字扩充不命中の実証）" % len(chg))
    pr("  → C6＝0 発火（実測）＝無/罔 扩充は shiki050-4 に効かない")

    chg = run_candidate(reachable, "何のごとし", "奈何", ("奈", "柰"), d0_cache, hb_of, cls)
    cands["C7_nangotoshi_guard_nai_dai"] = report_run("C7 何のごとし→奈何 guard(奈,柰)兄弟键",
                                                      chg, d0_cache, hb_of, cls, rows4)
    gate(len(chg) == 0, "C7 兄弟键発火 %d != 0（残量 0 前提）" % len(chg))

    # C9 tail 句型判別（phrase 級）＝rerun 行 tail に「為之奈何」が入る行 ∩ got がため
    phrase_rows = [r["id"] for r in reachable
                   if cls[r["id"]] == "rerun" and "為之奈何" in hb_of[r["id"]]
                   and "がため" in d0_cache[r["id"]][0]]
    pr("  C9 tail 句型「為之奈何」∩ got がため: %s（phrase 級と containment 級(為) 同発火集＝%s）"
       % (phrase_rows, phrase_rows == ["rikutou37-2"]))
    cands["C9_tail_phrase"] = {"rows": phrase_rows,
                               "note": "rerun 行では guard(变体字) ≡ tail 句型判別（同一述語）・"
                                       "phrase 級（為之奈何）と containment 級（為）同発火集"}
    gate(phrase_rows == ["rikutou37-2"], "C9 phrase 発火 %s != ['rikutou37-2']" % phrase_rows)

    # ---------- C8 tail→全文 guard 上下文機構（blast radius 全 pipeline 実測） ----------
    pr("")
    pr("== C8 tail→全文 guard 上下文機構（rerun 218 行・全 pipeline blast radius）==")
    from backend.kundoku_rules import style_fix_with_hakubun
    # 8-1 per-rule guard flip census（製品 guard タプルのまま・E〜U 全 rule 表）
    import backend.kundoku_rules as kr
    rule_tables = {}
    for name in dir(kr):
        if name.endswith("_KANA_TO_KANJI"):
            tbl = getattr(kr, name)
            rule_tables[name] = [(k, r, g) for (k, r, g) in tbl]
    flip_rows = set()
    per_rule_flip = {}
    rerun_ids = [rid for rid in cls if cls[rid] == "rerun"]
    for tname, tbl in sorted(rule_tables.items()):
        n_flip = 0
        for rid in rerun_ids:
            tail_hb = hb_of[rid]
            full_hb = hb_full_of[rid]
            for (kana, repl, guard) in tbl:
                if not guard:
                    continue
                if any(g in tail_hb for g in guard) != any(g in full_hb for g in guard):
                    n_flip += 1
                    flip_rows.add(rid)
                    break
        per_rule_flip[tname] = n_flip
    pr("  per-rule guard flip 行数（rerun %d 行・rule 表 %s）: %s"
       % (len(rerun_ids), ",".join(sorted(rule_tables)), per_rule_flip))
    pr("  flip 行 total %d 行: %s" % (len(flip_rows), sorted(flip_rows)[:40]))
    # 8-2 全 pipeline 実測：archived got に全文で style_fix_with_hakubun 再適用
    blast = []
    for rid in sorted(rerun_ids):
        got0, exp, d0 = d0_cache[rid]
        new = style_fix_with_hakubun(got0, hb_full_of[rid])
        if new != got0:
            d1 = lev(new, exp)
            blast.append({"id": rid, "d0": d0, "d1": d1, "new": new})
    b = [x for x in blast if x["d1"] < x["d0"]]
    w = [x for x in blast if x["d1"] > x["d0"]]
    s = [x for x in blast if x["d1"] == x["d0"]]
    pr("  全 pipeline 再適用で変化 %d 行 | better %d / worse %d / same %d"
       % (len(blast), len(b), len(w), len(s)))
    for x in blast[:30]:
        pr("    %-16s %d→%d %s" % (x["id"], x["d0"], x["d1"],
                                   "BETTER" if x["d1"] < x["d0"] else
                                   ("WORSE" if x["d1"] > x["d0"] else "SAME")))
    gate(not ({"rikutou37-2", "shiki050-4"} & {x["id"] for x in blast}),
         "C8 が目標 2 行に効いた＝解析と矛盾（tail 見直し）")
    pr("  → 目標 2 行（rikutou37-2/shiki050-4）は tail→全文で救われない（実測）:"
       " rikutou37-2 は tail に既に 為 あり（ guard 爲 の字形問題）・"
       "shiki050-4 は全文に 奈 無し（柰 のみ）")
    cands["C8_tail_to_full"] = {
        "flip_rows": sorted(flip_rows), "flip_total": len(flip_rows),
        "per_rule_flip": per_rule_flip,
        "pipeline_changed": len(blast), "better": [x["id"] for x in b],
        "worse": [x["id"] for x in w], "same": [x["id"] for x in s],
        "per_row": {x["id"]: [x["d0"], x["d1"]] for x in blast},
        "note": "全 pipeline 再適用＝近似シミュレーション（archived got は既に tail 语境適用済み・"
                "idempotent 前提）"}
    sim["candidates"] = cands

    # ---------- 組合 preview（C1+C4 同時＝guard 变体字扩充の収益寄与） ----------
    pr("")
    pr("== 組合 preview（C1+C4 同時適用＝報告書 §3 実施提案の収益寄与）==")
    comb = []
    rules = [("がため", "為", ("爲", "為")), ("何のごとく", "奈何ぞ", ("奈", "柰"))]
    for rid in ("rikutou37-2", "shiki050-4"):
        got0, exp, d0 = d0_cache[rid]
        new = got0
        nchg = 0
        for kana, repl, guard in rules:
            hb = hb_of[rid]
            if guard and hb and not any(g in hb for g in guard):
                continue
            new, n = _apply_count(new, kana, repl)
            nchg += n
        d1 = lev(new, exp)
        comb.append({"id": rid, "d0": d0, "d1": d1, "new": new, "nchg": nchg})
        pr("  %-16s %d→%d（%s）new=%r" % (rid, d0, d1,
                                          "BETTER" if d1 < d0 else ("WORSE" if d1 > d0 else "SAME"),
                                          new[-60:]))
    dsum8 = sum(x["d1"] - x["d0"] for x in comb)
    ids4 = {r["id"] for r in rows4}
    dsum4 = sum(x["d1"] - x["d0"] for x in comb if x["id"] in ids4)
    pr("  Δ8165 %.3f（%d 字）Δ4000 %.3f（%d 字）"
       % (dsum8 / 8165, dsum8, dsum4 / 4000, dsum4))
    # 幂等
    for rid in ("rikutou37-2", "shiki050-4"):
        got0, _e, _d = d0_cache[rid]
        new = got0
        for kana, repl, guard in rules:
            hb = hb_of[rid]
            if guard and hb and not any(g in hb for g in guard):
                continue
            new, _ = _apply_count(new, kana, repl)
            new2, _ = _apply_count(new, kana, repl)
            gate(new2 == new, "幂等 bad: %s" % rid)
    sim["combo_preview"] = {x["id"]: [x["d0"], x["d1"]] for x in comb}
    sim["combo_delta"] = {"8165": round(dsum8 / 8165, 4), "4000": round(dsum4 / 4000, 4),
                          "chars8165": dsum8, "chars4000": dsum4}

    sim["verdict"] = "REPORT_ONLY_MEASURED"
    sim["lev_impl"] = _LEV_IMPL
    sim["elapsed_sec"] = round(time.time() - t_start)
    json.dump(sim, open(os.path.join(EV, "night106_dissect.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night106_dissect.txt"), "w", encoding="utf-8",
         newline="\n").write("\n".join(lines) + "\n")
    pr("")
    pr("written: eval/night106_dissect.json / night106_dissect.txt")
    pr("SUMMARY C1 rikutou37-2 better/worse=%d/%d | C4 shiki050-4 better/worse=%d/%d | "
       "C8 blast changed=%d (better %d worse %d)"
       % (len(cands["C1_gatame_guard_ue_shin"]["better"]),
          len(cands["C1_gatame_guard_ue_shin"]["worse"]),
          len(cands["C4_nanogotoku_guard_nai_dai"]["better"]),
          len(cands["C4_nanogotoku_guard_nai_dai"]["worse"]),
          cands["C8_tail_to_full"]["pipeline_changed"],
          len(cands["C8_tail_to_full"]["better"]),
          len(cands["C8_tail_to_full"]["worse"])))
    pr("elapsed %.0fs" % sim["elapsed_sec"])


if __name__ == "__main__":
    main()
