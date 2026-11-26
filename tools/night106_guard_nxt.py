# -*- coding: utf-8 -*-
"""night106_guard_nxt.py — Night 106 (c)：守り字后继字 guard 拡張機構 設計＋原型実測（报告-only）。

任务书（N103 §4 機構建议・N105 §5 移交・機構設計夜 4/5）：守り字（guard 字）の「后继字」
（白文中 guard 字の直後 1 字）で活用语境を判別する guard 拡張機構を設計し、N103 の
18 个 ことなき site で原型実測——后继字が 莫く/莫し/莫き 三活用语境を分離できるか
（每 site 判对／判错列出）。rikutou26-5 型语顺结构差行（N103）が機構管轄内かも明記。
不改產品代碼、不收規則、不動 golden expected。基線＝night104_results_8165/4000.json。

機構設計（报告書 §1 详述・本 script は原型実測）：
  データ構造  : RULE 表 entry を (kana, guard, follow_map, default_repl) に拡張
                follow_map = { 后继字: repl_var }（guard 字直後 1 字 → repl 変体）
  接入点      : style_kana_to_kanji_* の rule loop 内（guard containment 通過後・
                site ごとに白文対位 guard 字の后继字で repl を選ぶ；E〜U 既存 rule は
                follow_map 省略時現行動作＝共存方式）
  対位        : got の 莫-token（こと莫かれ|こと莫く|こと莫き|こと莫し|ことなき）と
                exp 莫-token（N103 同款 1:1 順序対位）× 白文 plain 段の 莫（順序対位）
原型実測（3 種 sim・全部 got 側のみ・exp/golden 一字不改）：
  (i)  上限（perfect per-site form）: site ごとに exp 実字形の repl を当てる
  (ii) 実現値（follow_map 多数決表）: 后继字表の予測形 repl を当てる
  (iii) 現行対照 (a)  : 単一 repl こと莫き（N103 (a) 再現）
硬断言（对不上 exit 2＝停下报数）：
  S1 行分类 7916/30/218/1・S2 基线 13.460/13.467・24/30・词库 1531
  A1 (a) 発火恰好 15 行（N103 記録 ID 集）・roushi46-2 34→35・rikutou26-5 53→54・
     utsuryo03-7 63→63（night104 基线でも d0 不変＝Rule U は 15 行に触れない）
  A2 全 15 行で got 莫-token 数＝exp 莫-token 数＝白文 莫 数（順序対位の前提）
出力 eval/night106_guard_nxt.json ＋ eval/night106_guard_nxt.txt。
用法: python -I tools/night106_guard_nxt.py
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

# got 側 莫-token（ことなき sites＋Rule N/Q/U 出力 莫形）／exp 側 莫-token（N103 同款）
GOT_TOKEN_RE = re.compile("こと莫かれ|こと莫く|こと莫き|こと莫し|ことなき")
EXP_TOKEN_RE = re.compile("莫からん|莫くんば|莫かる|莫かれ|莫き|莫く|莫し")
# N103 記録（(a) 15 行・d0→d1・基线 night101＝night104 と d0 同値のはず）
N103_A = {
    "mujun-2": (11, 10), "onoreshiru-1": (18, 17), "kagakujota-1": (27, 26),
    "kanchuna-1": (82, 81), "rongo0615-1": (12, 11), "rongo0732-1": (23, 22),
    "rongo1315-1": (113, 110), "rongo1442-1": (55, 54), "p-danjoshitsu-1": (36, 35),
    "tarekako-1": (12, 11), "tonan-1": (29, 28), "warekimi-1": (35, 34),
    "roushi46-2": (34, 35), "utsuryo03-7": (63, 63), "rikutou26-5": (53, 54),
}
# 后继字→活用形 多数決表の tie-break 順（语料多数形 莫き 優先・N103 census 10/18）
FORM_ORDER = ["莫き", "莫し", "莫く", "莫からん", "莫くんば", "莫かる"]


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
        open(os.path.join(EV, "night106_guard_nxt.txt"), "w", encoding="utf-8",
             newline="\n").write("\n".join(lines) + "\n")
    except Exception:
        pass


EXPECTED_CLASS = {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}


def splice(text, spans):
    """spans = [(start, end, repl)] を後方から置換。"""
    out = text
    for s0, s1, repl in sorted(spans, key=lambda x: -x[0]):
        out = out[:s0] + repl + out[s1:]
    return out


def main():
    global sim
    t_start = time.time()
    sim = {"script": "tools/night106_guard_nxt.py", "night": 106,
           "mode": "守り字后继字 guard 拡張機構 設計＋原型実測（報告-only・不収録）",
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
    gate(close(base_avg4, 13.460) and close(base_avg8, 13.467), "基线 avgDist != 13.460/13.467")
    gate(exact_base4 == 24 and exact_base8 == 30, "基线 exact != 24/30")

    # ---------- (i-a) 現行対照 (a)：ことなき→こと莫き（guard 莫・N103 再現） ----------
    pr("")
    pr("== (iii) 現行対照 (a)：ことなき→こと莫き（guard 莫・N103 記録再現）==")
    gf_m = guard_forms(("莫",))
    gate(gf_m == ["莫"], "guard_forms(莫) %s != ['莫']" % gf_m)
    chg_a = []
    for r in reachable:
        rid = r["id"]
        hb = hb_of[rid]
        if hb and not any(g in hb for g in gf_m):
            continue
        got0, exp, d0 = d0_cache[rid]
        new, n = (got0.replace("ことなき", "こと莫き"), got0.count("ことなき"))
        if n:
            chg_a.append({"id": rid, "cls": cls[rid], "n_sites": n, "got": got0,
                          "new": new, "exp": exp, "d0": d0, "d1": lev(new, exp)})
    by_id = {c["id"]: c for c in chg_a}
    gate(len(chg_a) == 15, "A1 発火 %d != 15" % len(chg_a))
    gate(set(by_id) == set(N103_A), "A1 発火行集合 != N103 記録 15 行")
    for rid, (dd0, dd1) in N103_A.items():
        gate(rid in by_id and by_id[rid]["d0"] == dd0 and by_id[rid]["d1"] == dd1,
             "A1 %s 実測 %s != 記録 %d→%d（night104 基线 d0 不変前提）"
             % (rid, (by_id[rid]["d0"], by_id[rid]["d1"]) if rid in by_id else None, dd0, dd1))
    b_a = [c for c in chg_a if c["d1"] < c["d0"]]
    w_a = [c for c in chg_a if c["d1"] > c["d0"]]
    s_a = [c for c in chg_a if c["d1"] == c["d0"]]
    pr("  発火 %d 行 | better %d / worse %d / same %d（N103 記録 12/2/1 と一致）"
       % (len(chg_a), len(b_a), len(w_a), len(s_a)))
    sim["a_primary"] = {"fired": 15, "better": [c["id"] for c in b_a],
                        "worse": [c["id"] for c in w_a], "same": [c["id"] for c in s_a],
                        "per_row": {c["id"]: [c["d0"], c["d1"]] for c in chg_a}}

    # ---------- 対位＋白文 后继字 census ----------
    pr("")
    pr("== 対位（got 莫-token × exp 莫-token × 白文 plain 莫・順序 1:1）＋后继字 census ==")
    site_rows = []
    for c in chg_a:
        rid = c["id"]
        hb_full = hb_of[rid]
        gt = list(GOT_TOKEN_RE.finditer(c["got"]))
        et = list(EXP_TOKEN_RE.finditer(d0_cache[rid][1]))
        gate(len(gt) == len(et), "A2 %s token 数不一致 got %d vs exp %d"
             % (rid, len(gt), len(et)))
        n_mo_hb = hb_full.count("莫")
        gate(n_mo_hb == len(gt), "A2 %s 白文 莫 %d != got token %d（対位不能）"
             % (rid, n_mo_hb, len(gt)))
        # 白文 plain 段（（…）annotation を除いた外側）の 莫 も数える（参照情報）
        outside = re.sub(r"（[^）]*）", "", hb_full)
        # 後继字＝白文中 k 番目の 莫 の直後 1 字（annotation  interference 無し実測確認）
        mo_iter = list(re.finditer("莫", hb_full))
        sites = []
        for gi, gm in enumerate(gt):
            if gm.group() != "ことなき":
                continue  # Rule N/Q/U 対位 token（site 外）
            em = et[gi]
            mo = mo_iter[gi]
            nxt = hb_full[mo.end():mo.end() + 1] or "⏎"
            nxt2 = hb_full[mo.end():mo.end() + 2] or "⏎"
            sites.append({"site_index": gi, "got_pos": gm.start(),
                          "exp_tok": em.group(), "follow": nxt, "follow2": nxt2,
                          "hb_pos": mo.start()})
        gate(sites, "%s ことなき site 0 件（矛盾）" % rid)
        site_rows.append({"id": rid, "cls": c["cls"], "got": c["got"], "exp": d0_cache[rid][1],
                          "hb": hb_full, "n_tokens": len(gt), "sites": sites})
        forms = "・".join("%s@%d(后继=%s)" % (s["exp_tok"], s["site_index"], s["follow"])
                          for s in sites)
        pr("  %-16s [%s] token %d（白文 莫 %d）｜ ことなき site %d：%s"
           % (rid, c["cls"], len(gt), n_mo_hb, len(sites), forms))

    # site 表＋census（同一オブジェクトを流用：pred/ok を site_rows 側にも伝播させる）
    all_sites = []
    for sr in site_rows:
        for s in sr["sites"]:
            s["row_id"] = sr["id"]
            all_sites.append(s)
    gate(len(all_sites) == 18, "site 总数 %d != 18（N103 census）" % len(all_sites))
    form_c = collections.Counter(s["exp_tok"] for s in all_sites)
    follow_c = collections.Counter(s["follow"] for s in all_sites)
    pr("")
    pr("  site 字形分布：%s（N103 記録 莫き10/莫し4/莫からん2/莫くんば1/莫かる1）" % dict(form_c))
    pr("  后继字分布（1 字）：%s" % dict(follow_c))
    # 後继字 → 字形 表（多数決＋tie-break）
    table = collections.defaultdict(collections.Counter)
    for s in all_sites:
        table[s["follow"]][s["exp_tok"]] += 1
    follow_map = {}
    conflicted = {}
    for fc, cc2 in table.items():
        best_n = max(cc2.values())
        winners = [f for f, n in cc2.items() if n == best_n]
        if len(winners) == 1:
            follow_map[fc] = winners[0]
        else:
            # tie-break：FORM_ORDER（语料多数形 莫き 優先）
            pick = min(winners, key=lambda f: FORM_ORDER.index(f) if f in FORM_ORDER else 99)
            follow_map[fc] = pick
            conflicted[fc] = dict(cc2)
    pr("  follow_map（多数決・tie は语料多数形順）: %s" % follow_map)
    pr("  conflicted 後继字（同字複数形＝分離失敗 site の所在）: %s" % conflicted)

    # 每 site 判对/判错
    pr("")
    pr("== 每 site 判对／判错（follow_map 予測 vs exp 実字形）==")
    n_ok = n_ng = 0
    for s in all_sites:
        pred = follow_map[s["follow"]]
        s["pred"] = pred
        s["ok"] = (pred == s["exp_tok"])
        n_ok += s["ok"]
        n_ng += (not s["ok"])
        pr("  %-16s site#%d 后继=%s 予測=%s 実=%s %s（follow2=%s）"
           % (s["row_id"], s["site_index"], s["follow"], pred, s["exp_tok"],
              "○判对" if s["ok"] else "×判错", s["follow2"]))
    pr("  → 判对 %d / 判错 %d（%d/18）｜三向（莫く/莫し/莫き）14 site 内の判对 %d"
       % (n_ok, n_ng, n_ok, sum(1 for s in all_sites if s["ok"] and s["exp_tok"] in ("莫き", "莫し", "莫く"))))
    # follow2（2 字）でも同じか
    table2 = collections.defaultdict(collections.Counter)
    for s in all_sites:
        table2[s["follow2"]][s["exp_tok"]] += 1
    conf2 = {fc: dict(cc2) for fc, cc2 in table2.items() if len(cc2) > 1}
    pr("  2 字後继（follow2）でも衝突する字:%s（前例 莫己知 型）" % conf2)
    sim["sites"] = all_sites
    sim["follow_map"] = follow_map
    sim["conflicted"] = conflicted
    sim["conflicted2"] = conf2
    sim["judge"] = {"ok": n_ok, "ng": n_ng,
                    "three_way_ok": sum(1 for s in all_sites if s["ok"] and s["exp_tok"] in ("莫き", "莫し", "莫く"))}

    # ---------- 原型 sim（got 側のみ・exp 一字不改） ----------
    pr("")
    pr("== 原型 sim（got 側のみ・exp/golden 一字不改）==")
    rows4_ids = {r["id"] for r in rows4}

    def run_mode(mode):
        """mode: a=単一 repl こと莫き / ceiling=site 実字形 / follow=後继字予測形"""
        rows_res = {}
        for sr in site_rows:
            rid = sr["id"]
            got0, exp, d0 = d0_cache[rid]
            spans = []
            for s in sr["sites"]:
                if mode == "a":
                    repl = "こと莫き"
                elif mode == "ceiling":
                    repl = "こと" + s["exp_tok"]
                else:
                    repl = "こと" + s["pred"]
                # got ことなき の実 span（site_index 番目の token が ことなき）
                gt = list(GOT_TOKEN_RE.finditer(got0))
                gm = gt[s["site_index"]]
                gate(gm.group() == "ことなき", "%s site#%d token != ことなき" % (rid, s["site_index"]))
                spans.append((gm.start(), gm.end(), repl))
            new = splice(got0, spans)
            d1 = lev(new, exp)
            rows_res[rid] = {"d0": d0, "d1": d1, "new": new}
        b = sorted(rid for rid, v in rows_res.items() if v["d1"] < v["d0"])
        w = sorted(rid for rid, v in rows_res.items() if v["d1"] > v["d0"])
        s_ = sorted(rid for rid, v in rows_res.items() if v["d1"] == v["d0"])
        dsum8 = sum(v["d1"] - v["d0"] for v in rows_res.values())
        dsum4 = sum(rows_res[rid]["d1"] - rows_res[rid]["d0"]
                    for rid in rows_res if rid in rows4_ids)
        in4 = sum(1 for rid in rows_res if rid in rows4_ids)
        pr("  [%s] better %d / worse %d / same %d | Δ8165 %.3f（%d 字）Δ4000 %.3f（4000 内 %d 行）"
           % (mode, len(b), len(w), len(s_), dsum8 / 8165, dsum8, dsum4 / 4000, in4))
        for rid in sorted(rows_res):
            v = rows_res[rid]
            tag = "BETTER" if v["d1"] < v["d0"] else ("WORSE" if v["d1"] > v["d0"] else "SAME")
            pr("    %-16s %d→%d %s" % (rid, v["d0"], v["d1"], tag))
        return {"better": b, "worse": w, "same": s_,
                "delta8165": round(dsum8 / 8165, 4), "delta_chars8165": dsum8,
                "delta4000": round(dsum4 / 4000, 4), "in4000": in4,
                "per_row": {rid: [v["d0"], v["d1"]] for rid, v in rows_res.items()}}

    res_a = run_mode("a")
    res_ceiling = run_mode("ceiling")
    res_follow = run_mode("follow")
    sim["sim"] = {"a": res_a, "ceiling": res_ceiling, "follow": res_follow}

    # rikutou26-5 管轄判定
    pr("")
    pr("== rikutou26-5（N103 語順構造差行）の機構管轄判定 ==")
    rid = "rikutou26-5"
    s_ok = [s for s in all_sites if s["row_id"] == rid]
    pr("  対位可能性: 白文 莫 %d = got token %d（A2 gate 通過）＝機構は site に届く" % (
        hb_of[rid].count("莫"), len(GOT_TOKEN_RE.findall(d0_cache[rid][0]))))
    pr("  后继字予測: %s（実 %s）＝%s" % (
        s_ok[0]["pred"], s_ok[0]["exp_tok"], "判对" if s_ok[0]["ok"] else "判错"))
    pr("  それでも d1=%d（d0=%d）＝語順構造差の d 変差は機構でも救えない"
       "（got「識らざることなきを謀る」×exp「謀は…莫し」＝挿入 莫 が exp 莫 に届かない）"
       % (res_follow["per_row"][rid][1], res_follow["per_row"][rid][0]))
    gate(res_follow["per_row"][rid][1] == 54, "rikutou26-5 follow 値 %d != 54（N103 一致前提）"
         % res_follow["per_row"][rid][1])
    sim["rikutou26_5_scope"] = {
        "reachable": True,
        "pred_ok": bool(s_ok[0]["ok"]),
        "d_follow": res_follow["per_row"][rid],
        "verdict": "機構管轄内（対位・字形選択とも可能）だが d 変差は語順構造差で残存＝"
                   "項 4/5 の別機構（語順構造差）管轄という N103 結論を機構側から再確認"}

    sim["verdict"] = "REPORT_ONLY_MEASURED"
    sim["lev_impl"] = _LEV_IMPL
    sim["elapsed_sec"] = round(time.time() - t_start)
    json.dump(sim, open(os.path.join(EV, "night106_guard_nxt.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night106_guard_nxt.txt"), "w", encoding="utf-8",
         newline="\n").write("\n".join(lines) + "\n")
    pr("")
    pr("written: eval/night106_guard_nxt.json / night106_guard_nxt.txt")
    for mode, res in (("a", res_a), ("ceiling", res_ceiling), ("follow", res_follow)):
        pr("SUMMARY %s: better %d worse %d same %d | Δ8165 %.4f"
           % (mode, len(res["better"]), len(res["worse"]), len(res["same"]), res["delta8165"]))
    pr("judge: 判对 %d / 判错 %d" % (n_ok, n_ng))
    pr("elapsed %.0fs" % sim["elapsed_sec"])


if __name__ == "__main__":
    main()
