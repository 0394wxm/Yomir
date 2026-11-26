# -*- coding: utf-8 -*-
"""night102_sim.py — Night 102：第 8 项 ことなく guard 外 5 行・sim 先验 guard 扩展（night99_sim 型）。

任务书（N98 §3 决策表项 8・N101 §4 原样带入・用户拍板线）：把 Rule Q ことなく→こと莫く
的 guard 从 莫 扩为 莫/勿/毋 併用（収録＝路径 A，仅在 sim 全干净时实施）。
基线＝night101_results_8165.json / night101_results_4000.json（N101 归档・Rule T 已上 master）。

目标 5 行（N98 実測・须先对当前 master 复测）：
  p-haigun-1（白文 毋）・toushisen080-8・koshi19_01-8・rikutou04-2・rikutou21-2（白文 勿）
  ＝毋 1・勿 4・無 0・罔 0。rikutou21-2 は rerun 行且つ Rule S 发火行（なきなり→勿かれ
  既収）——本 sim はその ことなく 部分が guard 外残量のままであること（S 部分は一字も
  動かないこと）を S4/S6 で确认する。

三态 verdict（exit code で区分）：
  PATH_A_GREEN      (a)〜(d) 全部成立（5 行全改善・全域変差 0・干渉 0・発火＝恰好 5 行）
                    → 路径 A 収録绿灯
  NO_GATHER_NO_GAIN (b)(c)(d) 成立（変差 0・干渉 0・発火＝恰好 5 行）だが (a) 不成立
                    ＝5 行 0 改善（拡張は Δ0.000 で無益・収録線 Δ<=−0.001 未達）→ exit 0・不収録
  FAIL              変差が N99 6 行集合外／S/M 干渉／発火集合が 5 行以外／べき等性破れ
                    → exit 2・停下报数（路径 B）

硬断言（对不上 exit 2＝「停下报数」）：
  S1 行分类 engine 7916 / echo 30 / rerun 218 / no_tail 1（reachable 8134）
  S2 night101 vs night100 归档 got diff 0 行（合并夜门＝0）
  S3 基线 avgDist 4000=13.462 / 8165=13.469（归档値再計算一致）＋exact 24/30＋词库 1531
  S4 目标 5 行：全部発火（発火しなければ FAIL）；全域発火行集合＝恰好 5 行
     （N98 実測 5 行以外の新発火が 1 行でも出たら FAIL）；改善の有無は verdict 分岐のみ
  S5 全域変差：d1>d0 行が N99 変差 6 行集合外に 1 行でも出たら FAIL
     （N99 6 行＝shushu-4/shukateki-1/ryojo-3/shiseinishite-1/toushisen216-7/p-gekirin-1）
  S6 Rule S/M 干渉ゼロの证明（FAIL 条件）：
     (a) style_fix_with_hakubun 链序 M < Q < S（M は Q 前段＝拡張と無関係・S は Q 後段）
     (b) key ことなく は なきなり/なかれ とどの配置でも overlap 不可能（純文字列性の全判定）
     (c) 全 8165 行：拡張適用後も got の 勿かれ 出現数が不変（S/M の発火結果は一字も動かない）
     (d) S 発火 4 行（azamukuko-1/sonshi09-19/sonshi10-12/rikutou21-2＝test_night96 ID 锁）
         は拡張後も 勿かれ を保持する
  S7 幂等 bad 0・repl こと莫く は终字形（normalize_shinjitai 不変）・guard 莫/勿/毋
     は新旧変異なし（guard_forms 展開＝同形確認）
  S8 発火分布：guard 莫/勿/毋/罔 の白文含行数（blanket）と ことなく 残量行の guard 字別
     内訳を列挙（N88 T3 教训：発火 ≫ pair 即非語汇対応——本夜は ことなく 这一条のみ・
     他の 勿 行には拡大しない）

探索測定（非本夜収録対象・次夜拍板材料の実数）：per-guard repl 変体
  （ことなく→こと勿く guard 勿）＋（ことなく→こと毋く guard 毋）——guard 字と exp 実書形
  の対応を測るだけの离线 sim（製品コードには入れない）。

输出 eval/night102_sim.json ＋ eval/night102_ext_changed_rows.json（主候补拡張改写行予測＝
収録時 night102_eval_* の逐位对照源）＋ eval/night102_sim.txt。
用法: python -I tools/night102_sim.py
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
        sim["verdict"] = "FAIL"
        write_out()
        sys.exit(2)


def run(rows, kana_rules, d0_cache, hb_of, cls):
    """全行走查。echo/no_tail 行は規則不可達（N84 分流仕様）＝スキップ。

    guard 判定は製品コード（style_kana_to_kanji_q）と同一语义：
    「guard あり＆hb 非空＆守り字無し」のとき不発火、hb 空なら発火（空白文で発火）。
    """
    better = worse = same = 0
    changed_entries = 0
    total_old = total_new = 0
    worse_detail = []
    changed_rows = []
    for r in rows:
        rid = r["id"]
        hb = hb_of[rid]
        got0, exp, d0 = d0_cache[rid]
        new = got0
        nchg = 0
        if cls[rid] in ("engine", "rerun"):
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
                                 "old_text": got0, "new_text": new, "expected": exp,
                                 "cls": cls[rid]})
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


def idempotent(rows, kana_rules, d0_cache, hb_of, cls):
    bad = 0
    for r in rows:
        rid = r["id"]
        if cls[rid] not in ("engine", "rerun"):
            continue
        hb = hb_of[rid]
        got = d0_cache[rid][0]
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

# 目标 5 行（N98 §3 项 8 実測）／N99 変差 6 行集合／Rule S 発火 4 行（test_night96 ID 锁）
TARGET5 = ["p-haigun-1", "toushisen080-8", "koshi19_01-8", "rikutou04-2", "rikutou21-2"]
N99_WORSE6 = {"shushu-4", "shukateki-1", "ryojo-3", "shiseinishite-1",
              "toushisen216-7", "p-gekirin-1"}
S_FIRED4 = ["azamukuko-1", "sonshi09-19", "sonshi10-12", "rikutou21-2"]

# 主候补（任务书指定）：拡張 guard・repl はこと莫く のまま
PRIMARY = {"kana": "ことなく", "repl": "こと莫く", "guard": ("莫", "勿", "毋"),
           "longer": (), "tag": "项 8 ことなく guard 扩展（莫→莫/勿/毋 併用・Rule Q 原位改）"}
# 探索測定（非収録対象・次夜拍板材料）：guard 字と exp 実書形の対応を測る per-guard repl
EXPLORATORY = [
    {"kana": "ことなく", "repl": "こと勿く", "guard": ("勿",), "longer": (),
     "tag": "探索：guard 勿 行の exp 書形対位（こと勿く）"},
    {"kana": "ことなく", "repl": "こと毋く", "guard": ("毋",), "longer": (),
     "tag": "探索：guard 毋 行の exp 書形対位（こと毋く）"},
]


def overlap_free(a, b):
    """key a と b が文字列上で overlap（片方の suffix＝他方の prefix）し得ないこと。"""
    for i in range(1, len(a)):
        if a[-i:] == b[:i]:
            return False
    for i in range(1, len(b)):
        if b[-i:] == a[:i]:
            return False
    return True


def close(x, y, tol=0.0005):
    return abs(x - y) <= tol


def exp_context(got0, exp, key="ことなく", pad_l=8, pad_r=16):
    """got の key 出現位置ごとに、exp 側の対応箇所（前文 anchor 検索）を抜き出す。"""
    out = []
    idx = 0
    while True:
        j = got0.find(key, idx)
        if j < 0:
            break
        prefix = got0[max(0, j - pad_l):j]
        k = exp.find(prefix, max(0, j - pad_l - 40)) if prefix else -1
        if k >= 0:
            ctx = exp[max(0, k):k + len(prefix) + pad_r]
        else:
            ctx = exp[:pad_r + 8]
        out.append(ctx)
        idx = j + len(key)
    return out


def main():
    global sim
    t_start = time.time()
    sim = {"script": "tools/night102_sim.py", "night": 102,
           "mode": "项 8 ことなく guard 扩展（莫→莫/勿/毋 併用）の sim 先验（全域発火）",
           "verdict": None}

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
    doc8 = json.load(open(os.path.join(EV, "night101_results_8165.json"), encoding="utf-8"))
    rows8 = [r for r in doc8["results"] if r.get("udkundoku_kakikudashi") is not None]
    gate(len(rows8) == 8165, "night101_results_8165 行数 %d != 8165" % len(rows8))
    doc4 = json.load(open(os.path.join(EV, "night101_results_4000.json"), encoding="utf-8"))
    rows4 = doc4["results"]
    gate([r["id"] for r in rows4] == [r["id"] for r in rows8[:4000]],
         "night101_results_4000 与 8165 前 4000 行序不一致")

    doc8_n100 = json.load(open(os.path.join(EV, "night100_results_8165.json"),
                               encoding="utf-8"))["results"]
    m100 = {b["id"]: b for b in doc8_n100}
    diff100 = [r["id"] for r in rows8
               if norm(r["udkundoku_kakikudashi"]) != norm(m100[r["id"]]["udkundoku_kakikudashi"])]
    pr("== S2 基线：night101 vs night100 归档 got diff %d 行（合并夜门＝0）==" % len(diff100))
    gate(len(diff100) == 0, "night101/night100 归档差异 %d 行 != 0" % len(diff100))
    sim["n101_vs_n100_diff"] = 0

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

    # 行分类＋guard 上下文（night98_audit/night99_sim 同款）
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

    d0_cache = {}
    for r in rows8:
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        d0_cache[r["id"]] = (got, exp, lev(got, exp))
    base_avg8 = round(sum(v[2] for v in d0_cache.values()) / 8165, 3)
    base_avg4 = round(sum(d0_cache[r["id"]][2] for r in rows4) / 4000, 3)
    exact_base8 = sum(1 for v in d0_cache.values() if v[2] == 0)
    exact_base4 = sum(1 for r in rows4 if d0_cache[r["id"]][2] == 0)
    pr("  基线 avgDist 4000=%.3f 8165=%.3f（归档 13.462/13.469）exact %d/%d（归档 24/30）"
       % (base_avg4, base_avg8, exact_base4, exact_base8))
    sim["baseline"] = {"avg4000": base_avg4, "avg8165": base_avg8,
                       "exact4000": exact_base4, "exact8165": exact_base8,
                       "archive": "night101_results_8165.json / night101_results_4000.json"}
    gate(close(base_avg4, 13.462), "基线 avgDist 4000 %.3f != 13.462" % base_avg4)
    gate(close(base_avg8, 13.469), "基线 avgDist 8165 %.3f != 13.469" % base_avg8)
    gate(exact_base4 == 24 and exact_base8 == 30,
         "基线 exact %d/%d != 24/30" % (exact_base4, exact_base8))

    # ---------- 候补（1 条＝既收 Rule Q ことなく 的 guard 扩展・非新规则） ----------
    gate(normalize_shinjitai(PRIMARY["repl"]) == PRIMARY["repl"], "repl 非终字形: こと莫く")
    gf = guard_forms(PRIMARY["guard"])
    pr("== 主候补 guard_forms(莫/勿/毋)=%s（莫・勿・毋 は新旧変異なし）==" % gf)
    gate(gf == ["莫", "勿", "毋"], "guard_forms(莫/勿/毋) != ['莫','勿','毋']（字形変異あり＝要再検）")
    for e in EXPLORATORY:
        gate(normalize_shinjitai(e["repl"]) == e["repl"], "探索 repl 非终字形: %s" % e["repl"])
    kana_rules = [(PRIMARY["kana"], PRIMARY["repl"], tuple(gf), PRIMARY["longer"])]

    # ---------- S6 Rule S/M 干渉ゼロの構造証明 ----------
    pr("")
    pr("== S6 Rule S/M 干渉構造証明 ==")
    src = open(os.path.join(ROOT, "backend", "kundoku_rules.py"), encoding="utf-8").read()
    body = src.split("def style_fix_with_hakubun", 1)[1].split("return t", 1)[0]
    i_m = body.find("style_kana_to_kanji_m(")
    i_q = body.find("style_kana_to_kanji_q(")
    i_s = body.find("style_kana_to_kanji_s(")
    pr("  (a) 链序 M(%d) < Q(%d) < S(%d)：%s" % (i_m, i_q, i_s,
       "OK" if 0 < i_m < i_q < i_s else "NG"))
    gate(0 < i_m < i_q < i_s, "S6(a) 链序 M<Q<S 不成立（M は Q 後段＝拡張が M に触れ得る）")
    of1 = overlap_free("ことなく", "なきなり")
    of2 = overlap_free("ことなく", "なかれ")
    pr("  (b) overlap 判定：ことなく×なきなり %s／ことなく×なかれ %s"
       % ("FREE" if of1 else "OVERLAP", "FREE" if of2 else "OVERLAP"))
    gate(of1 and of2, "S6(b) key overlap 可能＝拡張置換が なきなり/なかれ を壊し得る")
    sim["s6_chain_order"] = "M<Q<S"
    sim["s6_overlap_free"] = True

    # ---------- 測定（主候补＝拡張 guard・repl こと莫く） ----------
    pr("")
    pr("== S4/S5/S8 測定（guard 莫→莫/勿/毋 併用・全量 sim）==")
    t1 = time.time()
    m8 = run(rows8, kana_rules, d0_cache, hb_of, cls)
    m4 = run(rows4, kana_rules, d0_cache, hb_of, cls)
    bad = idempotent(rows8, kana_rules, d0_cache, hb_of, cls)
    pr("  (%.0fs)" % (time.time() - t1))
    chg8 = {cr["id"]: cr for cr in m8["changed_rows"]}
    chg4 = {cr["id"]: cr for cr in m4["changed_rows"]}

    pr("  拡張発火 %d 行（4000 内 %d）| better %d/%d worse %d/%d same %d | "
       "avg 8165 %.3f→%.3f 4000 %.3f→%.3f | Δ8165 %.3f Δ4000 %.3f | 幂等 bad %d"
       % (m8["changed_entries"], m4["changed_entries"], m8["better"], m4["better"],
          m8["worse"], m4["worse"], m8["same"],
          m8["avg_old"], m8["avg_new"], m4["avg_old"], m4["avg_new"],
          m8["delta"], m4["delta"], bad))
    pr("  変差行 %s" % sorted(wd["id"] for wd in m8["worse_detail"]))
    for cr in m8["changed_rows"]:
        pr("    発火 %s [%s・guard %s] %d→%d%s | got …%s"
           % (cr["id"], cr["cls"],
              "".join(g for g in ("莫", "勿", "毋") if g in hb_of[cr["id"]]) or "(空)",
              cr["old_dist"], cr["new_dist"],
              "" if cr["new_dist"] < cr["old_dist"]
              else ("（改善なし＝same）" if cr["new_dist"] == cr["old_dist"]
                    else "（変差！）"),
              cr["old_text"][:36]))
        pr("        → %s" % cr["new_text"][:72])
        for ctx in exp_context(cr["old_text"], cr["expected"]):
            pr("        exp側対位 …%s" % ctx)

    # S8 発火分布（guard 字別 blanket ＋ ことなく 残量内訳）
    dist = {}
    for g in ("莫", "勿", "毋", "罔"):
        blanket = sum(1 for r in reachable if g in hb_of[r["id"]])
        dist["blanket_" + g] = blanket
    resid = [r["id"] for r in reachable if "ことなく" in d0_cache[r["id"]][0]]
    resid_g = collections.Counter()
    for rid in resid:
        hb = hb_of[rid]
        hit = "".join(g for g in ("莫", "勿", "毋") if g in hb)
        resid_g[hit or "(守り字無し)"] += 1
    sim["s8_distribution"] = {"blanket": dist, "kotonaku_residual": dict(resid_g),
                              "kotonaku_residual_ids": resid}
    pr("== S8 発火分布 ==")
    pr("  guard 字 blanket（reachable %d 行の白文/tail 含字行数）：莫 %d・勿 %d・毋 %d・罔 %d"
       % (len(reachable), dist["blanket_莫"], dist["blanket_勿"],
          dist["blanket_毋"], dist["blanket_罔"]))
    pr("  ことなく 残量行（reachable・got に ことなく 残存）%d 行：guard 字別 %s"
       % (len(resid), dict(resid_g)))
    pr("  → 発火は ことなく 残量行に限定（key 必須）＝N88 T3 型 blanket scramble 構造を持たない")

    # ---------- 硬断言 ----------
    pr("")
    pr("== 硬断言（N98 実測・N99 変差集合との对照）==")
    # S4 目标 5 行の発火（改善の有無は verdict 分岐）
    for rid in TARGET5:
        gate(rid in chg8, "S4 目标行 %s が発火しない（残量状態が変化？）" % rid)
        gate(cls.get(rid) in ("engine", "rerun"),
             "S4 目标行 %s が規則不可達クラス %s" % (rid, cls.get(rid)))
    hb_t = {rid: hb_of[rid] for rid in TARGET5}
    gate(all(("勿" in hb_t[rid] or "毋" in hb_t[rid]) for rid in TARGET5),
         "S4 目标行の白文/tail に 勿/毋 が無い：%s" % hb_t)
    gate(all("莫" not in hb_t[rid] for rid in TARGET5),
         "S4 目标行の白文/tail に 莫 がある（既発火のはず＝矛盾）：%s" % hb_t)
    gate(set(chg8.keys()) == set(TARGET5),
         "S4 全域発火行 %s != 恰好 N98 実測 5 行（新発火＝停下报数）"
         % sorted(set(chg8.keys()) - set(TARGET5)))
    pr("  S4 全域発火＝恰好 N98 実測 5 行 ✓（勿 4・毋 1・rikutou21-2 の ことなく 部分は"
       " guard 外残量のまま確認）")
    # S5 全域変差
    worse_ids = set(wd["id"] for wd in m8["worse_detail"])
    gate(worse_ids.issubset(N99_WORSE6),
         "S5 変差行が N99 6 行集合外: %s" % sorted(worse_ids - N99_WORSE6))
    worse4 = set(wd["id"] for wd in m4["worse_detail"])
    gate(worse4.issubset(N99_WORSE6),
         "S5(4000) 変差行が N99 6 行集合外: %s" % sorted(worse4 - N99_WORSE6))
    pr("  S5 変差 %s（8165）／%s（4000）・N99 6 行集合内 ✓"
       % (sorted(worse_ids) or "0 行", sorted(worse4) or "0 行"))
    # S6(c)(d) 勿かれ 保全
    lost = [r["id"] for r in rows8
            if d0_cache[r["id"]][0].count("勿かれ") !=
            (chg8[r["id"]]["new_text"].count("勿かれ") if r["id"] in chg8
             else d0_cache[r["id"]][0].count("勿かれ"))]
    gate(not lost, "S6(c) 拡張適用で 勿かれ 出現数が変わった行: %s" % lost[:8])
    lost_s = [rid for rid in S_FIRED4
              if "勿かれ" not in (chg8[rid]["new_text"] if rid in chg8
                                  else d0_cache[rid][0])]
    gate(not lost_s, "S6(d) S 発火 4 行の拡張後 got に 勿かれ が無い: %s" % lost_s)
    pr("  S6(c) 全 8165 行 勿かれ 出現数不変 ✓／S6(d) S 発火 4 行 %s 勿かれ 保持 ✓" % S_FIRED4)
    # S7 幂等・终字形
    gate(bad == 0, "S7 幂等 bad %d != 0" % bad)
    pr("  S7 幂等 bad 0 ✓・repl こと莫く 终字形 ✓・guard 新旧変異なし ✓")

    # ---------- verdict 分岐（S4 改善の有無） ----------
    all5_better = all(chg8[rid]["new_dist"] < chg8[rid]["old_dist"] for rid in TARGET5)
    pe8 = (sum(1 for r in rows8 if r["id"] not in chg8 and d0_cache[r["id"]][2] == 0)
           + sum(1 for cr in m8["changed_rows"] if cr["new_dist"] == 0))
    pe4 = (sum(1 for r in rows4 if r["id"] not in chg4 and d0_cache[r["id"]][2] == 0)
           + sum(1 for cr in m4["changed_rows"] if cr["new_dist"] == 0))
    pr("")
    if all5_better:
        sim["verdict"] = "PATH_A_GREEN"
        pr("== verdict: PATH_A_GREEN（5 行全改善・変差 0・干渉 0・発火＝恰好 5 行）→ 路径 A 収録绿灯 ==")
    else:
        sim["verdict"] = "NO_GATHER_NO_GAIN"
        pr("== verdict: NO_GATHER_NO_GAIN（変差 0・干渉 0・発火＝恰好 5 行だが 0 改善＝"
           "拡張は Δ%.3f で無益・収録線 Δ<=−0.001 未達）→ 不収録（N94 嗟や 無益拒の同系）=="
           % m8["delta"])
    pr("  予測：Δ8165 %.3f Δ4000 %.3f｜avg 8165 %.3f 4000 %.3f｜exact %d/%d（変更なし）"
       % (m8["delta"], m4["delta"], m8["avg_new"], m4["avg_new"], pe4, pe8))

    # ---------- 探索測定（非収録対象・次夜拍板材料） ----------
    pr("")
    pr("== 探索測定：per-guard repl 変体（こと勿く guard 勿／こと毋く guard 毋・"
       "非本夜収録対象＝製品コードに入れない）==")
    expl_res = {}
    for e in EXPLORATORY:
        kr = [(e["kana"], e["repl"], tuple(guard_forms(e["guard"])), e["longer"])]
        x8 = run(rows8, kr, d0_cache, hb_of, cls)
        x4 = run(rows4, kr, d0_cache, hb_of, cls)
        xbad = idempotent(rows8, kr, d0_cache, hb_of, cls)
        expl_res[e["repl"]] = {
            "changed": x8["changed_entries"], "changed4000": x4["changed_entries"],
            "better": x8["better"], "worse": x8["worse"], "same": x8["same"],
            "delta8165": x8["delta"], "delta4000": x4["delta"],
            "idempotent_bad": xbad,
            "worse_ids": sorted(w["id"] for w in x8["worse_detail"]),
            "changed_rows": x8["changed_rows"],
        }
        pr("  %s（guard %s）：発火 %d 行（4000 内 %d）改善 %d 変差 %d same %d｜"
           "Δ8165 %.3f Δ4000 %.3f｜幂等 bad %d"
           % (e["repl"], e["guard"][0], x8["changed_entries"], x4["changed_entries"],
              x8["better"], x8["worse"], x8["same"], x8["delta"], x4["delta"], xbad))
        pr("      変差行 %s" % (sorted(w["id"] for w in x8["worse_detail"]) or "なし"))
    krx = [(e["kana"], e["repl"], tuple(guard_forms(e["guard"])), e["longer"])
           for e in EXPLORATORY]
    y8 = run(rows8, krx, d0_cache, hb_of, cls)
    y4 = run(rows4, krx, d0_cache, hb_of, cls)
    ybad = idempotent(rows8, krx, d0_cache, hb_of, cls)
    pr("  combo（勿+毋 2 条）：発火 %d 行（4000 内 %d）改善 %d 変差 %d same %d｜"
       "Δ8165 %.3f Δ4000 %.3f｜幂等 bad %d"
       % (y8["changed_entries"], y4["changed_entries"], y8["better"], y8["worse"],
          y8["same"], y8["delta"], y4["delta"], ybad))
    pr("      combo 変差行 %s" % (sorted(w["id"] for w in y8["worse_detail"]) or "なし"))
    sim["exploratory"] = {k: {kk: vv for kk, vv in v.items() if kk != "changed_rows"}
                          for k, v in expl_res.items()}
    sim["exploratory_combo"] = {"changed": y8["changed_entries"],
                                "changed4000": y4["changed_entries"],
                                "better": y8["better"], "worse": y8["worse"],
                                "delta8165": y8["delta"], "delta4000": y4["delta"],
                                "idempotent_bad": ybad,
                                "worse_ids": sorted(w["id"] for w in y8["worse_detail"]),
                                "note": "非本夜収録対象・次夜拍板材料の実数（sim 离线値）"}

    # ---------- S/M 发火行の観測値（報告用・発火集合は構造証明+eval 逐位で確定） ----------
    m_fired_obs = [r["id"] for r in rows8
                   if cls[r["id"]] in ("engine", "rerun")
                   and "勿かれ" in d0_cache[r["id"]][0]
                   and r["id"] not in S_FIRED4]
    pr("")
    pr("  観測：got に 勿かれ を含む行 %d 行（＝S 4 行＋M なかれ→勿かれ 由来 %d 行）"
       % (len(m_fired_obs) + len(S_FIRED4), len(m_fired_obs)))
    pr("  → 拡張は Q 段の ことなく 置換のみ（S6 構造証明）・M/S の発火集合は不変")
    sim["sm_observation"] = {"s_fired4": S_FIRED4,
                             "motsukare_rows_excl_S": sorted(m_fired_obs),
                             "note": "M/S 発火集合は構造証明 S6(a)(b)＋勿かれ保全 S6(c)(d)＋"
                                     "（収録時は eval 全行逐位一致）で不変確認"}

    # ---------- 输出 ----------
    gates_slim = {
        "ext8165": {k: v for k, v in m8.items() if k != "changed_rows"},
        "ext4000": {k: v for k, v in m4.items() if k != "changed_rows"},
        "pred_exact4000": pe4, "pred_exact8165": pe8,
        "target5_detail": {rid: {"old": chg8[rid]["old_dist"], "new": chg8[rid]["new_dist"],
                                 "guard": [g for g in ("莫", "勿", "毋")
                                           if g in hb_of[rid]],
                                 "cls": chg8[rid]["cls"],
                                 "exp_ctx": exp_context(chg8[rid]["old_text"],
                                                        chg8[rid]["expected"])}
                           for rid in TARGET5},
    }
    sim["gates"] = gates_slim
    sim["lev_impl"] = _LEV_IMPL
    sim["elapsed_sec"] = round(time.time() - t_start)

    out_changed = os.path.join(EV, "night102_ext_changed_rows.json")
    json.dump(m8["changed_rows"], open(out_changed, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    out_json = os.path.join(EV, "night102_sim.json")
    json.dump(sim, open(out_json, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night102_sim.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    pr("")
    pr("written: eval/night102_sim.json / night102_ext_changed_rows.json / night102_sim.txt")
    pr("PRED_4000=%d PRED_8165=%d | PRED_EXACT_4000=%d PRED_EXACT_8165=%d | verdict=%s"
       % (m4["changed_entries"], m8["changed_entries"], pe4, pe8, sim["verdict"]))
    pr("elapsed %.0fs" % sim["elapsed_sec"])


def write_out():
    try:
        open(os.path.join(EV, "night102_sim.txt"), "w", encoding="utf-8", newline="\n").write(
            "\n".join(lines) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
