# -*- coding: utf-8 -*-
"""night106_wa_pos.py — Night 106 (b)：項 5 は系主语位置判別・切分実測（报告-only）。

任务书（N98 §3 项 5・機構設計夜 4/5）：把 は→将に（N92 T1）与 は→未だ（N92 T2）の発火行
按位置切分（句首／「。」后／从句首＝主语位 vs 其余），算每切分的改善／変差；
主语位切分が改善と変差を分離できない場合は負結果をありのまま記録し、
次の判別方向を書く。不改產品代碼、不收規則、不動 golden expected。
基線＝night104_results_8165/4000.json。

定義（3 段・字面→操作化）：
  PosDef-1 字面句首   : occ==0 or 直前字符＝「。」
  PosDef-2 topic slot : occ がその文（直前「。」の後の区間）内で最初の は（主語/主題槽の操作化）
  PosDef-3 clause 先頭: occ がその節（直前「。」或いは「、」の後の区間）内で最初の は
sim（機構原型）：PosDef 毎に「当該位置の は のみ」置換して better/worse/same・Δ 双口径。
硬断言（对不上 exit 2＝停下报数）：
  S1 行分类 7916/30/218/1・S2 基线 13.460/13.467・24/30・词库 1531
  S3 guard_forms(将)==["将","將"]（N94 坑位③・wa_mashini 2 発火翻车の教訓）
  S4 発火行数 mashini==265 / imada==172（N92/N98 記録・got は と 白文 将/將・未 は
     R/S/T/U 規則で不変のため安定）
出力 eval/night106_wa_pos.json ＋ eval/night106_wa_pos.txt。
用法: python -I tools/night106_wa_pos.py
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


def apply_at_positions(text, kana, positions, repl):
    """positions（occurrence 開始 index の set）にある kana のみ置換。"""
    out, last, n = [], 0, 0
    for m in re.finditer(re.escape(kana), text):
        if m.start() in positions:
            out.append(text[last:m.start()] + repl)
            last = m.end()
            n += 1
    out.append(text[last:])
    return "".join(out), n


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
        open(os.path.join(EV, "night106_wa_pos.txt"), "w", encoding="utf-8",
             newline="\n").write("\n".join(lines) + "\n")
    except Exception:
        pass


EXPECTED_CLASS = {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}


def occ_features(got):
    """各 は occurrence の位置特徴を返す: list of dict(pos, literal, topic, clause)."""
    occs = [m.start() for m in re.finditer("は", got)]
    # 文区間の先頭 index（0 と 各「。」の直後）
    sent_starts = {0}
    for i, ch in enumerate(got):
        if ch == "。" and i + 1 < len(got):
            sent_starts.add(i + 1)
    first_in_sent = {}
    for p in occs:
        s = max(s for s in sent_starts if s <= p)
        if s not in first_in_sent:
            first_in_sent[s] = p
    # 節区間の先頭（「。」または「、」の直後）
    clause_starts = set(sent_starts)
    for i, ch in enumerate(got):
        if ch == "、" and i + 1 < len(got):
            clause_starts.add(i + 1)
    first_in_clause = {}
    for p in occs:
        s = max(s for s in clause_starts if s <= p)
        if s not in first_in_clause:
            first_in_clause[s] = p
    feats = []
    for p in occs:
        feats.append({"pos": p,
                      "literal": p == 0 or got[p - 1] == "。",
                      "topic": first_in_sent.get(max(s for s in sent_starts if s <= p)) == p,
                      "clause": first_in_clause.get(max(s for s in clause_starts if s <= p)) == p})
    return feats


def main():
    global sim
    t_start = time.time()
    sim = {"script": "tools/night106_wa_pos.py", "night": 106,
           "mode": "項 5 は系主语位置判別・切分実測（報告-only・不収録・製品コード零改动）",
           "verdict": None}

    pr("== S2 词库 import 实证（不動確認）==")
    import backend.glossary_lexicon as gl
    import backend.glossary_lexicon_extra as gle
    import backend.glossary_lexicon_extra2 as gle2
    lex = {"core": len(gl.GLOSSARY_LEXICON), "core_old_size": getattr(gl, "_OLD_SIZE", None),
           "extra": len(gle.as_dicts()), "extra2": len(gle2.LEXICON_EXTRA2),
           "ordered_all": len(gle2._ORDERED_ALL)}
    pr("  %s" % lex)
    gate(lex["core_old_size"] == 209 and lex["core"] == 500 and lex["extra"] == 291
         and lex["extra2"] == 1031 and lex["ordered_all"] == 1531,
         "词库実測 != 1531")

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
    gate(dict(cc) == EXPECTED_CLASS, "行分类実数 %s != 期待 %s" % (dict(cc), EXPECTED_CLASS))
    reachable = [r for r in rows8 if cls[r["id"]] in ("engine", "rerun")]

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
    gate(close(base_avg4, 13.460) and close(base_avg8, 13.467), "基线 avgDist != 13.460/13.467")
    gate(exact_base4 == 24 and exact_base8 == 30, "基线 exact != 24/30")

    # ---------- 候補（N92 T1/T2・N98 B5 承認表） ----------
    gf_mashini = guard_forms(("将",))
    gf_imada = guard_forms(("未",))
    pr("")
    pr("== S3 guard_forms：将→%s・未→%s ==" % (gf_mashini, gf_imada))
    gate(gf_mashini == ["将", "將"], "guard_forms(将) %s != ['将','將']" % gf_mashini)
    gate(gf_imada == ["未"], "guard_forms(未) %s != ['未']" % gf_imada)

    CANDS = [("wa_mashini", "は", "将に", gf_mashini, 265),
             ("wa_imada", "は", "未だ", gf_imada, 172)]

    rows4_ids = {r["id"] for r in rows4}
    results = {}
    for key, kana, repl, gfl, expect_fired in CANDS:
        pr("")
        pr("== %s は→%s（guard %s）==" % (key, repl, gfl))
        # 全域発火（全 occurrence 置換＝N92 probe 语义）
        fired = []
        for r in reachable:
            rid = r["id"]
            hb = hb_of[rid]
            if gfl and hb and not any(g in hb for g in gfl):
                continue
            if "は" in d0_cache[rid][0]:
                fired.append(r)
        pr("  S4 発火 %d 行（N92/N98 記録 %d）" % (len(fired), expect_fired))
        gate(len(fired) == expect_fired,
             "S4 %s 発火 %d != %d（記録対照・停下报数）" % (key, len(fired), expect_fired))
        # 全 occurrence 置換（N92 语义）の better/worse
        full = []
        for r in fired:
            rid = r["id"]
            got0, exp, d0 = d0_cache[rid]
            new, n = apply_at_positions(got0, "は", {m.start() for m in re.finditer("は", got0)}, repl)
            full.append({"id": rid, "n_occ": n, "d0": d0, "d1": lev(new, exp),
                         "got": got0, "exp": exp})
        fb = [c for c in full if c["d1"] < c["d0"]]
        fw = [c for c in full if c["d1"] > c["d0"]]
        fs = [c for c in full if c["d1"] == c["d0"]]
        pr("  全 occurrence 置換（N92 语义）: better %d / worse %d / same %d（occ 計 %d）"
           % (len(fb), len(fw), len(fs), sum(c["n_occ"] for c in full)))
        # exp 側に repl を書く行の割合（付帯統計）
        n_exp_repl = sum(1 for c in full if repl in c["exp"])
        pr("  付帯: 発火行のうち exp が %r を含む行 %d/%d（%.1f%%）"
           % (repl, n_exp_repl, len(full), 100.0 * n_exp_repl / len(full)))

        # 位置切分（三つの PosDef を全部測る）
        posdef_results = {}
        for feat_key in ("literal", "topic", "clause"):
            occ_stat = collections.Counter()
            row_b = collections.Counter()
            for r in fired:
                got0 = d0_cache[r["id"]][0]
                feats = occ_features(got0)
                n_yes = sum(1 for f in feats if f[feat_key])
                occ_stat["occ_yes"] += n_yes
                occ_stat["occ_total"] += len(feats)
                row_b["rows_all_yes" if n_yes == len(feats) else
                      ("rows_mixed" if n_yes else "rows_none")] += 1
            pr("  PosDef %s: occ %d/%d | rows all-yes %d / mixed %d / none %d"
               % (feat_key, occ_stat["occ_yes"], occ_stat["occ_total"],
                  row_b["rows_all_yes"], row_b["rows_mixed"], row_b["rows_none"]))
            # split sim：yes 位置のみ置換
            chg = []
            for r in fired:
                rid = r["id"]
                got0, exp, d0 = d0_cache[rid]
                feats = occ_features(got0)
                pos = {f["pos"] for f in feats if f[feat_key]}
                if not pos:
                    continue
                new, n = apply_at_positions(got0, "は", pos, repl)
                chg.append({"id": rid, "n": n, "d0": d0, "d1": lev(new, exp),
                            "got": got0, "exp": exp, "new": new})
            cb = [c for c in chg if c["d1"] < c["d0"]]
            cw = [c for c in chg if c["d1"] > c["d0"]]
            cs = [c for c in chg if c["d1"] == c["d0"]]
            dsum8 = sum(c["d1"] - c["d0"] for c in chg)
            dsum4 = sum(c["d1"] - c["d0"] for c in chg if c["id"] in rows4_ids)
            in4 = sum(1 for c in chg if c["id"] in rows4_ids)
            pr("    → yes のみ置換: 触った行 %d | better %d / worse %d / same %d | "
               "Δ8165 %.3f（%d 字）Δ4000 %.3f（4000 内 %d 行）"
               % (len(chg), len(cb), len(cw), len(cs), dsum8 / 8165, dsum8,
                  dsum4 / 4000, in4))
            # complement（no のみ置換）＝分離の反証
            chg2 = []
            for r in fired:
                rid = r["id"]
                got0, exp, d0 = d0_cache[rid]
                feats = occ_features(got0)
                pos = {f["pos"] for f in feats if not f[feat_key]}
                if not pos:
                    continue
                new, n = apply_at_positions(got0, "は", pos, repl)
                chg2.append({"id": rid, "n": n, "d0": d0, "d1": lev(new, exp)})
            cb2 = [c for c in chg2 if c["d1"] < c["d0"]]
            cw2 = [c for c in chg2 if c["d1"] > c["d0"]]
            pr("    → no のみ置換（反証）: 触った行 %d | better %d / worse %d"
               % (len(chg2), len(cb2), len(cw2)))
            posdef_results[feat_key] = {
                "occ_yes": occ_stat["occ_yes"], "occ_total": occ_stat["occ_total"],
                "rows_all_yes": row_b["rows_all_yes"], "rows_mixed": row_b["rows_mixed"],
                "rows_none": row_b["rows_none"],
                "yes_sim": {"rows": len(chg), "better": len(cb), "worse": len(cw),
                            "same": len(cs), "delta8165": round(dsum8 / 8165, 4),
                            "delta_chars8165": dsum8, "delta4000": round(dsum4 / 4000, 4),
                            "in4000": in4,
                            "per_row": {c["id"]: [c["d0"], c["d1"]] for c in chg}},
                "no_sim": {"rows": len(chg2), "better": len(cb2), "worse": len(cw2),
                           "per_row": {c["id"]: [c["d0"], c["d1"]] for c in chg2}}}
            if feat_key == "topic" and key == "wa_mashini":
                # サンプル dump（topic 切分・better/worse 各 3 行）
                for tag, group in (("BETTER", cb), ("WORSE", cw)):
                    for c in group[:3]:
                        pr("      [%s %s] %d→%d" % (tag, c["id"], c["d0"], c["d1"]))
                        pr("        got=%r" % c["got"][:110])
                        pr("        new=%r" % c["new"][:110])
                        pr("        exp=%r" % c["exp"][:110])
        results[key] = {"fired": len(fired), "guard": gfl,
                        "full_sim": {"better": len(fb), "worse": len(fw), "same": len(fs),
                                     "occ_total": sum(c["n_occ"] for c in full),
                                     "exp_contains_repl_rows": n_exp_repl,
                                     "per_row": {c["id"]: [c["d0"], c["d1"]] for c in full}},
                        "posdefs": posdef_results}
        sim[key] = results[key]

    sim["verdict"] = "REPORT_ONLY_MEASURED"
    sim["lev_impl"] = _LEV_IMPL
    sim["elapsed_sec"] = round(time.time() - t_start)
    json.dump(sim, open(os.path.join(EV, "night106_wa_pos.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night106_wa_pos.txt"), "w", encoding="utf-8",
         newline="\n").write("\n".join(lines) + "\n")
    pr("")
    pr("written: eval/night106_wa_pos.json / night106_wa_pos.txt")
    for key, _k, _r, _g, _e in CANDS:
        res = results[key]
        for fk, pd in res["posdefs"].items():
            pr("SUMMARY %s/%s: yes 置換 rows %d better %d worse %d | no 置換 better %d worse %d"
               % (key, fk, pd["yes_sim"]["rows"], pd["yes_sim"]["better"],
                  pd["yes_sim"]["worse"], pd["no_sim"]["better"], pd["no_sim"]["worse"]))
    pr("elapsed %.0fs" % sim["elapsed_sec"])


if __name__ == "__main__":
    main()
