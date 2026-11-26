# -*- coding: utf-8 -*-
"""night103_sim.py — Night 103：第 6 项 ことなき字形统一・sim 再测（night102_sim 型・报告-only）。

任务书（N98 §3 项 6・N102 §4/§6 顺位更新・「收益列须 sim 实测后才定」教训）：
本夜只 sim 再测、不改任何产品代码、不动 golden expected、不拍板。
基线＝night101_results_8165.json / night101_results_4000.json（N101 归档・Rule T 已上 master）。

(a) 原规则复测：ことなき→こと莫き（guard 莫）对当前 master 重测——确认 15 改写
    12 改善 2 変差；変差行＝roushi46-2（34→35）・rikutou26-5（53→54）（N101 §4 的
    「rousShi46-2」は筆誤・正 ID＝roushi46-2，N98 定）。
(b) 字形统一 sim（site 級・双向＋数据驱动第三向）：exp 側 ことなき-site の 莫-同語変体
    （莫き/莫く/莫し）を統一——莫く 一式／莫し 一式（任务书指定両向）＋莫き 一式
    （exp 侧多数形・本夜 recon 実測 9/17 site でデータ駆動追加）。 grammar 異形
    （莫からん・莫かる・莫くんば・莫かれ）は同語変体でないので**一切触らない**
    （書き下し文の文法保全・Rule N 出力 莫かれ 対位も不触碰＝⑤の確認）。
    各向で ことなき→こと莫{く,し,き}（guard 莫）を適用し package 効果を測定：
    ① 15 行中 改善/変差/持平；② 2 変差行の解消；③ 全域新增変差（N99 6 行集合外）；
    ④ Δ8165/Δ4000 実測＋N98「13 行改善」vs 12+2=14 の差額算清；⑤ got 莫かれ 72 行不変。
(c) 改动清单：各向で golden expected を書き換える行（ID＋原文→統一後テキスト）を
    出力（night103_unify_rows.json・报告 §3・ファイルは書き換えない）。

探索測定（非収録対象）：guard 外 4 行（ichijicho-1/rongo1125-1 exp 毋かれ・
shindoku-1/daigaku06-1 exp 毋き＝recon 新知見・白文 毋系）に ことなき→こと毋き
（guard 毋）を当てて収益を測るだけ（次夜拍板材料）。

硬断言（对不上 exit 2＝停下报数）：
  S1 行分类 engine 7916 / echo 30 / rerun 218 / no_tail 1（reachable 8134）
  S2 night101 vs night100 归档 got diff 0 行（合并夜门＝0）
  S3 基线 avgDist 4000=13.462 / 8165=13.469＋exact 24/30＋词库 1531
  A1 (a) 原規則：発火恰好 15 行（guard 莫 適用後）・better 12・worse 2・same 1・
     変差行＝roushi46-2 34→35・rikutou26-5 53→54・同一行 utsuryo03-7 63→63
  A2 token 対位：全 15 行で got 莫-token 数＝exp 莫-token 数（順序 1:1 対位の前提）
  A3 ⑤ got 莫かれ 72 行（統一前後不変・統一は site 級で Rule N 対位 token に触れない）
输出 eval/night103_sim.json ＋ eval/night103_unify_rows.json（改动清单）＋
eval/night103_sim.txt。
用法: python -I tools/night103_sim.py
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


def run_rule(rows, kana, repl, guard_forms_list, d0_cache, hb_of, cls):
    """guard 付き単規則走查（製品コード同一语义・echo/no_tail は規則不可達）。"""
    out = []
    for r in rows:
        rid = r["id"]
        if cls[rid] not in ("engine", "rerun"):
            continue
        hb = hb_of[rid]
        if guard_forms_list and hb and not any(g in hb for g in guard_forms_list):
            continue
        got0 = d0_cache[rid][0]
        new, n = _apply_count(got0, kana, repl)
        if n:
            out.append({"id": rid, "cls": cls[rid], "n_sites": n,
                        "got": got0, "new": new,
                        "d0": d0_cache[rid][2], "d1": lev(new, d0_cache[rid][1])})
    return out


EXPECTED_CLASS = {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}

N99_WORSE6 = {"shushu-4", "shukateki-1", "ryojo-3", "shiseinishite-1",
              "toushisen216-7", "p-gekirin-1"}
WORSE2 = {"roushi46-2": (34, 35), "rikutou26-5": (53, 54)}
SAME1 = {"utsuryo03-7": 63}

# got 側 莫-token（ことなき sites＋Rule N/Q 出力 莫形）／exp 側 莫-token
GOT_TOKEN_RE = re.compile("こと莫かれ|こと莫く|こと莫き|こと莫し|ことなき")
EXP_TOKEN_RE = re.compile("莫からん|莫くんば|莫かる|莫かれ|莫き|莫く|莫し")
# 同語変体（字形統一の対象）／文法異形（一切触らない）
VARIANT_FORMS = {"莫き", "莫く", "莫し"}
DISTINCT_FORMS = {"莫からん", "莫くんば", "莫かる", "莫かれ"}

# 統一方向：任務書指定 2 向＋データ駆動 1 向（target form, 書き換対象の旧形集合）
DIRS = [
    ("moku", "莫く", {"莫き", "莫し"}),
    ("moshi", "莫し", {"莫き", "莫く"}),
    ("moki", "莫き", {"莫く", "莫し"}),
]


def main():
    global sim
    t_start = time.time()
    sim = {"script": "tools/night103_sim.py", "night": 103,
           "mode": "项 6 ことなき字形统一・sim 再测（报告-only・不収録・製品コード零改动）",
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

    # 行分类＋guard 上下文（night98_audit/night102_sim 同款）
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

    # ---------- (a) 原規則复测：ことなき→こと莫き（guard 莫） ----------
    pr("")
    pr("== (a) 原規則复测：ことなき→こと莫き（guard 莫・guard_forms 展開）==")
    gf_m = guard_forms(("莫",))
    gate(gf_m == ["莫"], "guard_forms(莫) != ['莫']（字形変異あり＝要再検）")
    chg_a = run_rule(rows8, "ことなき", "こと莫き", gf_m, d0_cache, hb_of, cls)
    by_id = {c["id"]: c for c in chg_a}
    better_ids = sorted(c["id"] for c in chg_a if c["d1"] < c["d0"])
    worse_ids = sorted(c["id"] for c in chg_a if c["d1"] > c["d0"])
    same_ids = sorted(c["id"] for c in chg_a if c["d1"] == c["d0"])
    pr("  発火 %d 行 | better %d / worse %d / same %d" % (
        len(chg_a), len(better_ids), len(worse_ids), len(same_ids)))
    for c in chg_a:
        pr("    %-16s [%s・sites %d] %d→%d %s" % (
            c["id"], c["cls"], c["n_sites"], c["d0"], c["d1"],
            "BETTER" if c["d1"] < c["d0"] else ("WORSE" if c["d1"] > c["d0"] else "SAME")))
    # A1 硬断言（N96/N98 記録との逐位对照）
    gate(len(chg_a) == 15, "A1 発火 %d != 15" % len(chg_a))
    gate(len(better_ids) == 12 and len(worse_ids) == 2 and len(same_ids) == 1,
         "A1 better/worse/same %d/%d/%d != 12/2/1"
         % (len(better_ids), len(worse_ids), len(same_ids)))
    gate(set(by_id) == set(WORSE2) | set(SAME1) | set(better_ids),
         "A1 発火行集合が想定と不一致")
    for rid, (dd0, dd1) in WORSE2.items():
        gate(rid in by_id and by_id[rid]["d0"] == dd0 and by_id[rid]["d1"] == dd1,
             "A1 変差行 %s 実測 %s != 記録 %d→%d"
             % (rid, (by_id[rid]["d0"], by_id[rid]["d1"]) if rid in by_id else None, dd0, dd1))
    for rid, dd0 in SAME1.items():
        gate(rid in by_id and by_id[rid]["d0"] == dd0 and by_id[rid]["d1"] == dd0,
             "A1 同一行 %s 実測 != %d→%d" % (rid, dd0, dd0))
    dsum8 = sum(c["d1"] - c["d0"] for c in chg_a)
    chg_a4 = [c for c in chg_a if c["id"] in {r["id"] for r in rows4}]
    dsum4 = sum(c["d1"] - c["d0"] for c in chg_a4)
    delta_a8 = round(dsum8 / 8165, 3)
    delta_a4 = round(dsum4 / 4000, 3)
    pr("  Δ8165 %.3f（%d 字）Δ4000 %.3f（4000 内 %d 行）→ 原規則単独は 0 変差門不通"
       "（変差 2 行＝roushi46-2/rikutou26-5）＝字形統一拍板の対象" % (delta_a8, dsum8, delta_a4, len(chg_a4)))
    sim["a_primary"] = {"fired": len(chg_a), "better": len(better_ids),
                        "worse": worse_ids, "same": same_ids,
                        "worse_detail": {rid: [by_id[rid]["d0"], by_id[rid]["d1"]]
                                         for rid in worse_ids},
                        "delta8165": delta_a8, "delta4000": delta_a4,
                        "in4000": len(chg_a4),
                        "per_row": {c["id"]: [c["d0"], c["d1"]] for c in chg_a}}

    # ---------- token 対位（順序 1:1）＋site 字形 census ----------
    pr("")
    pr("== token 対位（got 莫-token × exp 莫-token・順序 1:1）==")
    site_info = {}
    for c in chg_a:
        rid = c["id"]
        raw_exp = next(r["expected_kakikudashi"] for r in rows8 if r["id"] == rid)
        gt = list(GOT_TOKEN_RE.finditer(c["got"]))
        et_n = list(EXP_TOKEN_RE.finditer(d0_cache[rid][1]))
        et_r = list(EXP_TOKEN_RE.finditer(raw_exp))
        gate(len(gt) == len(et_n),
             "A2 %s token 数不一致 got %d vs exp %d（対位不能＝停下报数）"
             % (rid, len(gt), len(et_n)))
        gate(len(et_n) == len(et_r) and
             [m.group() for m in et_n] == [m.group() for m in et_r],
             "A2 %s raw/norm token 列不一致（whitespace 問題）" % rid)
        pairs = []
        for gm, em in zip(gt, et_n):
            pairs.append({"got_tok": gm.group(), "got_pos": gm.start(),
                          "exp_tok": em.group(), "exp_pos": em.start()})
        kt = [p for p in pairs if p["got_tok"] == "ことなき"]
        site_info[rid] = {"raw_exp": raw_exp, "pairs": pairs, "kotonaki_sites": kt,
                          "n_got_tokens": len(gt), "n_exp_tokens": len(et_n)}
        forms = "・".join("%s@%d" % (p["exp_tok"], p["exp_pos"]) for p in kt)
        pr("  %-16s got-token %d＝exp-token %d｜ことなき site %d：exp %s"
           % (rid, len(gt), len(et_n), len(kt), forms))
    # site 字形分布
    form_c = collections.Counter()
    for rid, si in site_info.items():
        for p in si["kotonaki_sites"]:
            form_c[p["exp_tok"]] += 1
    pr("  ことなき site（%d 行 %d site）の exp 字形分布：%s"
       % (len(site_info), sum(form_c.values()), dict(form_c)))
    sim["site_form_census"] = dict(form_c)

    # ---------- (b) 字形统一 sim（3 向・site 級） ----------
    pr("")
    pr("== (b) 字形统一 sim（site 級・文法異形 莫からん/莫かる/莫くんば/莫かれ は不触碰）==")
    mk_before = sum(1 for r in rows8 if "莫かれ" in d0_cache[r["id"]][0])
    gate(mk_before == 72, "got 莫かれ 行数 %d != 72（N98 記録）" % mk_before)
    pr("  ⑤ got 莫かれ 行数（統一前）：%d（N98 記録 72 ✓）" % mk_before)

    unify_results = {}
    for key, target, variants in DIRS:
        rule_repl = "こと" + target
        pr("")
        pr("  ---- 向 %s：site 字形 %s → %s（rule ことなき→%s）----"
           % (key, "/".join(sorted(variants)), target, rule_repl))
        row_res = {}
        changed_exp_rows = []
        total_d0 = total_d1 = 0
        for r in rows8:
            rid = r["id"]
            got0, exp0, d00 = d0_cache[rid]
            exp_mod = exp0
            rewrite_detail = []
            if rid in site_info:
                si = site_info[rid]
                # raw 文での site 書き換え（norm と raw の token 列は A2 で一致済み）
                raw_exp = si["raw_exp"]
                et_r = list(EXP_TOKEN_RE.finditer(raw_exp))
                et_n = list(EXP_TOKEN_RE.finditer(exp0))
                gate([m.group() for m in et_r] == [m.group() for m in et_n],
                     "%s raw/norm token 列不一致" % rid)
                # 書き換え span（後方から置換して offset をずらさない）：
                # pairs は got/exp token の順序対＝exp token の index は pairs 内の位置
                all_pairs = si["pairs"]
                spans = []
                for i, p in enumerate(all_pairs):
                    if p["got_tok"] == "ことなき" and p["exp_tok"] in variants:
                        m = et_r[i]
                        spans.append((m.start(), m.end(), m.group()))
                for s0, s1, tok in sorted(spans, reverse=True):
                    raw_exp = raw_exp[:s0] + target + raw_exp[s1:]
                    rewrite_detail.append({"from": tok, "to": target, "pos": s0})
                exp_mod = norm(raw_exp)
            # package 効果：rule(got) vs exp_mod、対比 d0=lev(got0, exp0)
            new_got = got0
            if rid in by_id:
                new_got, _n = _apply_count(got0, "ことなき", rule_repl)
            d1 = lev(new_got, exp_mod) if (new_got != got0 or exp_mod != exp0) else d00
            d0u = lev(got0, exp_mod) if exp_mod != exp0 else d00
            row_res[rid] = {"d0": d00, "d0_unified": d0u, "d1": d1,
                            "exp_changed": exp_mod != exp0,
                            "rewrites": rewrite_detail}
            total_d0 += d00
            total_d1 += d1
            if exp_mod != exp0:
                changed_exp_rows.append(rid)

        # 統計
        ids15 = set(by_id)
        b = sorted(rid for rid in ids15 if row_res[rid]["d1"] < row_res[rid]["d0"])
        w = sorted(rid for rid in ids15 if row_res[rid]["d1"] > row_res[rid]["d0"])
        s_ = sorted(rid for rid in ids15 if row_res[rid]["d1"] == row_res[rid]["d0"])
        # ② 変差 2 行の解消
        resolved = {rid: ("解消→改善" if row_res[rid]["d1"] < row_res[rid]["d0"]
                          else ("解消→持平" if row_res[rid]["d1"] == row_res[rid]["d0"]
                                else "未解消（仍変差 %d→%d）" % (row_res[rid]["d0"], row_res[rid]["d1"])))
                    for rid in WORSE2}
        # ③ 全域新增変差（exp 変更＋rule 発火は 15 行に限定＝全域走查で確認）
        all_changed = sorted(rid for rid in row_res
                             if row_res[rid]["d1"] != row_res[rid]["d0"]
                             or row_res[rid]["exp_changed"])
        gate(set(all_changed) <= ids15,
             "③ 統一効果が 15 行以外に波及: %s" % sorted(set(all_changed) - ids15))
        new_worse_outside = sorted(rid for rid in w if rid not in N99_WORSE6)
        # ④ Δ
        # 全域 Δ：15 行以外は d1==d0 なので 15 行の和のみ
        d8 = sum(row_res[rid]["d1"] - row_res[rid]["d0"] for rid in ids15)
        ids15_4 = ids15 & {r["id"] for r in rows4}
        d4 = sum(row_res[rid]["d1"] - row_res[rid]["d0"] for rid in ids15_4)
        delta8 = round(d8 / 8165, 3)
        delta4 = round(d4 / 4000, 3)
        pr("  ① 15 行内：改善 %d 行 %s／変差 %d 行 %s／持平 %d 行 %s"
           % (len(b), b, len(w), w, len(s_), s_))
        pr("  ② 変差 2 行：%s" % "・".join("%s %s" % (rid, resolved[rid]) for rid in sorted(WORSE2)))
        pr("  ③ 全域：exp 変更＋発火は 15 行に限定 ✓・N99 6 行集合外の新增変差 %d 行 %s"
           % (len(new_worse_outside), new_worse_outside or "なし"))
        pr("  ④ Δ8165 %.3f（%d 字）・Δ4000 %.3f（4000 内 %d 行）"
           % (delta8, d8, delta4, len(ids15_4)))
        pr("     改善内訳：N98 記録の 12 改善行の内 本向で改善維持 %d 行・変差 2 行の解消 %s"
           % (sum(1 for rid in b if by_id[rid]["d1"] < by_id[rid]["d0"]),
              "あり" if all(row_res[rid]["d1"] <= row_res[rid]["d0"] for rid in WORSE2) else "なし"))
        # ⑤ 莫かれ（統一後も got 不変・rule repl は 莫かれ を含まない）
        mk_after = sum(1 for r in rows8 if "莫かれ" in d0_cache[r["id"]][0])
        gate(mk_after == 72, "⑤ 統一後 got 莫かれ 行数 %d != 72" % mk_after)
        gate(target != "莫かれ", "統一形に 莫かれ は選べない（Rule N 出力系）")
        pr("  ⑤ got 莫かれ 72 行（統一後不変 ✓）・Rule N 対位 token（こと莫かれ の exp 側）は"
           "書き換え対象外 ✓")
        unify_results[key] = {
            "target": target, "variants": sorted(variants),
            "better": b, "worse": w, "same": s_,
            "resolved": resolved, "new_worse_outside_n99_6": new_worse_outside,
            "delta8165": delta8, "delta4000": delta4, "delta_chars8165": d8,
            "exp_changed_rows": sorted(changed_exp_rows),
            "exp_changed_count": len(changed_exp_rows),
            "in4000": len(ids15_4),
            "per_row": {rid: [row_res[rid]["d0"], row_res[rid]["d0_unified"],
                              row_res[rid]["d1"]] for rid in sorted(ids15)},
        }

    # ---------- (c) 改动清单（原文→統一後・full text） ----------
    pr("")
    pr("== (c) 改动清单（golden expected 書き換え行・ID＋原文→統一後・ファイルは書き換えない）==")
    # raw_exp の書き換え結果を保持するため再構築（unify ループ内で raw_mod を捨てていたのでやり直し）
    unify_rows_full = {}
    for key, target, variants in DIRS:
        rows_out = []
        for rid in sorted(unify_results[key]["exp_changed_rows"]):
            si = site_info[rid]
            raw_exp = si["raw_exp"]
            et_r = list(EXP_TOKEN_RE.finditer(raw_exp))
            all_pairs = si["pairs"]
            spans = []
            for i, p in enumerate(all_pairs):
                if p["got_tok"] == "ことなき" and p["exp_tok"] in variants:
                    m = et_r[i]
                    spans.append((m.start(), m.end(), m.group()))
            for s0, s1, tok in sorted(spans, reverse=True):
                raw_exp = raw_exp[:s0] + target + raw_exp[s1:]
            rows_out.append({"id": rid, "before": si["raw_exp"], "after": raw_exp,
                             "sites": [{"from": t, "to": target} for _s, _e, t in spans]})
            pr("  [%s] %s（site %d 箇所：%s）" % (
                key, rid, len(spans), "・".join("%s→%s" % (t, target) for _s, _e, t in spans)))
            pr("    before: %s" % si["raw_exp"])
            pr("    after : %s" % raw_exp)
        unify_rows_full[key] = {"target": target, "rows": rows_out,
                                "count": len(rows_out)}
        pr("  → 向 %s の golden expected 改动＝%d 行" % (key, len(rows_out)))
    sim["unify"] = unify_results
    sim["unify_changed_exp_rows"] = {k: v["count"] for k, v in unify_rows_full.items()}

    # ---------- 探索測定（guard 外 毋系 4 行・非収録対象） ----------
    pr("")
    pr("== 探索測定：guard 外 毋系 ことなき 行（recon 新知見・非本夜収録対象）==")
    gf_h = guard_forms(("毋",))
    pr("  guard_forms(毋)=%s" % gf_h)
    expl = run_rule(rows8, "ことなき", "こと毋き", gf_h, d0_cache, hb_of, cls)
    for c in expl:
        pr("    %-16s [%s] %d→%d %s" % (
            c["id"], c["cls"], c["d0"], c["d1"],
            "BETTER" if c["d1"] < c["d0"] else ("WORSE" if c["d1"] > c["d0"] else "SAME")))
        pr("      got: %s" % c["got"][:80])
        pr("      exp: %s" % d0_cache[c["id"]][1][:80])
    dsum_x = sum(c["d1"] - c["d0"] for c in expl)
    sim["exploratory_m"] = {"rule": "ことなき→こと毋き（guard 毋）",
                            "fired": len(expl),
                            "detail": {c["id"]: [c["d0"], c["d1"]] for c in expl},
                            "delta_chars": dsum_x,
                            "note": "非本夜収録対象・次夜拍板材料（recon 新知見：ことなき の"
                                    "毋系 4 行は項 6 の莫 guard 外＝別候補族）"}
    pr("  → 発火 %d 行・合計 %d 字（Δ8165 ≈ %.6f・収録線級の在庫判定は次夜拍板で）"
       % (len(expl), dsum_x, dsum_x / 8165))

    # ---------- 输出 ----------
    sim["verdict"] = "REPORT_ONLY_MEASURED"
    sim["lev_impl"] = _LEV_IMPL
    sim["elapsed_sec"] = round(time.time() - t_start)
    out_json = os.path.join(EV, "night103_sim.json")
    json.dump(sim, open(out_json, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    json.dump(unify_rows_full, open(os.path.join(EV, "night103_unify_rows.json"),
              "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night103_sim.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    pr("")
    pr("written: eval/night103_sim.json / night103_unify_rows.json / night103_sim.txt")
    for key, _t, _v in DIRS:
        u = unify_results[key]
        pr("SUMMARY %s: 改善 %d 変差 %d 持平 %d | Δ8165 %.3f Δ4000 %.3f | exp 改动 %d 行"
           % (key, len(u["better"]), len(u["worse"]), len(u["same"]),
              u["delta8165"], u["delta4000"], u["exp_changed_count"]))
    pr("elapsed %.0fs" % sim["elapsed_sec"])


def close(x, y, tol=0.0005):
    return abs(x - y) <= tol


def write_out():
    try:
        open(os.path.join(EV, "night103_sim.txt"), "w", encoding="utf-8", newline="\n").write(
            "\n".join(lines) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
