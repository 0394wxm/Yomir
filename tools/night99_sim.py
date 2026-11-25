# -*- coding: utf-8 -*-
"""night99_sim.py — Night 99 拍板夜：撤 0 変差硬门の三条収録前 sim 検証（night98_audit 型）。

用户 2026-11-25 拍板（N98 报告 §3/§4 决策表 1a/1b/1c/2 为据）：撤 0 变差硬门，
仅限本夜三条——べからず→可からず・べからざる→可からざる・べきなり→可きなり
（guard 可・新旧両形并查＝可 は新旧変異なし）。变差行上限 6 行，ID 须与 N98 实测
一致；超出即停下报数（exit 2）。

机制照抄 tools/night98_audit.py（lev / _apply_count / run / 行分类 / guard_forms）。
sim 基线＝night97_results_8165.json / night97_results_4000.json（N98 実測と同一基线・
N98 审计已用本夜三条候补測得 78/70/5・82/79/1・combo 157/146/5・31/29/1）。

硬断言（对不上 exit 2＝「停下报数」）：
  S1 行分类 engine 7916 / echo 30 / rerun 218 / no_tail 1（reachable 8134）
  S2 night97 vs night96 归档 got diff 0 行（合并夜门＝0）
  S3 基线 avgDist 4000=13.488 / 8165=13.496（归档値再計算一致）＋词库 1531 实证
  S4 T1 べからず→可からず：78 改写 70 改善 5 変差（shushu-4/shukateki-1/ryojo-3/
     saio-x13/toushisen216-7）Δ8165 −0.011 Δ4000 −0.008
  S5 T2 べからざる→可からざる：82 改写 79 改善 1 変差（shiseinishite-1 73→74）
     Δ8165 −0.011 Δ4000 −0.011
  S6 T1+T2 combo：157 改写 146 改善 5 変差（5 ID＝N98 実測集合・全部落在 N98 已知
     6 行集合内）幂等 bad 0・Δ8165 −0.022 Δ4000 −0.019
  S7 T3 べきなり→可きなり：31 改写 29 改善 1 変差（p-gekirin-1 8→9）Δ8165 −0.006
     Δ4000 −0.006
  S8 三条 combo：変差行总数＝6（S6 の 5 行＋p-gekirin-1・一行も超出集合不可）
     幂等 bad 0・Δ8165 ≈ −0.028 Δ4000 ≈ −0.025（±0.003）

输出 eval/night99_sim.json（全実績＋変差 6 行明细）＋ eval/night99_combo_changed_rows.json
（三条 combo 改写行预测＝night99_eval_* の逐位对照源）＋ eval/night99_sim.txt。
用法: python -I tools/night99_sim.py
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
            if guard and not any(g in hb for g in guard):
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


EXPECTED_CLASS = {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}

# N98 已知 6 行集合（任务书）＋combo 実測 5 行＋三条合计 6 行
KNOWN6_TASK = {"shushu-4", "shukateki-1", "ryojo-3", "saio-x13",
               "toushisen216-7", "shiseinishite-1"}
COMBO12_WORSE = {"shushu-4", "shukateki-1", "ryojo-3", "shiseinishite-1",
                 "toushisen216-7"}
TOTAL6_WORSE = COMBO12_WORSE | {"p-gekirin-1"}


def close(x, y, tol=0.0005):
    return abs(x - y) <= tol


def main():
    t_start = time.time()
    sim = {"script": "tools/night99_sim.py", "night": 99,
           "mode": "拍板夜 Rule T 3 条 sim 検証（撤 0 変差硬门・変差 6 行許容）"}

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
    doc8 = json.load(open(os.path.join(EV, "night97_results_8165.json"), encoding="utf-8"))
    rows8 = [r for r in doc8["results"] if r.get("udkundoku_kakikudashi") is not None]
    gate(len(rows8) == 8165, "night97_results_8165 行数 %d != 8165" % len(rows8))
    doc4 = json.load(open(os.path.join(EV, "night97_results_4000.json"), encoding="utf-8"))
    rows4 = doc4["results"]
    gate([r["id"] for r in rows4] == [r["id"] for r in rows8[:4000]],
         "night97_results_4000 与 8165 前 4000 行序不一致")

    doc8_n96 = json.load(open(os.path.join(EV, "night96_results_8165.json"),
                              encoding="utf-8"))["results"]
    m96 = {b["id"]: b for b in doc8_n96}
    diff96 = [r["id"] for r in rows8
              if norm(r["udkundoku_kakikudashi"]) != norm(m96[r["id"]]["udkundoku_kakikudashi"])]
    pr("== S2 基线：night97 vs night96 归档 got diff %d 行（合并夜门＝0）==" % len(diff96))
    gate(len(diff96) == 0, "night97/night96 归档差异 %d 行 != 0" % len(diff96))
    sim["n97_vs_n96_diff"] = 0

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

    d0_cache = {}
    for r in rows8:
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        d0_cache[r["id"]] = (got, exp, lev(got, exp))
    base_avg8 = round(sum(v[2] for v in d0_cache.values()) / 8165, 3)
    base_avg4 = round(sum(d0_cache[r["id"]][2] for r in rows4) / 4000, 3)
    exact_base8 = sum(1 for v in d0_cache.values() if v[2] == 0)
    exact_base4 = sum(1 for r in rows4 if d0_cache[r["id"]][2] == 0)
    pr("  基线 avgDist 4000=%.3f 8165=%.3f（归档 13.488/13.496）exact %d/%d（归档 24/30）"
       % (base_avg4, base_avg8, exact_base4, exact_base8))
    sim["baseline"] = {"avg4000": base_avg4, "avg8165": base_avg8,
                       "exact4000": exact_base4, "exact8165": exact_base8}
    gate(close(base_avg4, 13.488), "基线 avgDist 4000 %.3f != 13.488" % base_avg4)
    gate(close(base_avg8, 13.496), "基线 avgDist 8165 %.3f != 13.496" % base_avg8)
    gate(exact_base4 == 24 and exact_base8 == 30,
         "基线 exact %d/%d != 24/30" % (exact_base4, exact_base8))

    # ---------- 候补表（3 条拍板・guard 可＝新旧変異なし・longer 空壳） ----------
    CANDIDATES = {
        "bekarazu": {"kana": "べからず", "repl": "可からず", "guard": ("可",), "longer": (),
                     "tag": "拍板1a べからず族（N98 実測 78/70/5）"},
        "bekarazaru": {"kana": "べからざる", "repl": "可からざる", "guard": ("可",), "longer": (),
                       "tag": "拍板1b べからず族（N98 実測 82/79/1）"},
        "bekimari": {"kana": "べきなり", "repl": "可きなり", "guard": ("可",), "longer": (),
                     "tag": "拍板2 べきなり→可きなり（N98 実測 31/29/1）"},
    }
    for k, c in CANDIDATES.items():
        gate(normalize_shinjitai(c["repl"]) == c["repl"], "repl 非终字形: %s" % k)
    gf_kei = guard_forms(("可",))
    pr("== 候补 guard_forms(可)=%s（可 は新旧変異なし）==" % gf_kei)
    gate(gf_kei == ["可"], "guard_forms(可) != ['可']")

    def rules_of(keys):
        return [(CANDIDATES[k]["kana"], CANDIDATES[k]["repl"],
                 tuple(guard_forms(CANDIDATES[k]["guard"])), CANDIDATES[k]["longer"])
                for k in keys]

    def measure(keys):
        kana_rules = rules_of(keys)
        res8 = run(reachable, kana_rules, d0_cache, hb_of)
        res4 = run(rows4, kana_rules, d0_cache, hb_of)
        chg8 = {cr["id"]: cr for cr in res8["changed_rows"]}
        # 8165 全口径（reachable 外 31 行は d0 据置・night98_audit gate_one 同款）
        total_old8 = sum(d0_cache[r["id"]][2] for r in rows8)
        full_new8 = total_old8 + sum(cr["new_dist"] - cr["old_dist"]
                                     for cr in res8["changed_rows"])
        # 预测 exact（変更行は新距離・非変更行は d0 据置）
        pe8 = (sum(1 for r in rows8 if r["id"] not in chg8 and d0_cache[r["id"]][2] == 0)
               + sum(1 for cr in res8["changed_rows"] if cr["new_dist"] == 0))
        chg4 = {cr["id"]: cr for cr in res4["changed_rows"]}
        pe4 = (sum(1 for r in rows4 if r["id"] not in chg4 and d0_cache[r["id"]][2] == 0)
               + sum(1 for cr in res4["changed_rows"] if cr["new_dist"] == 0))
        bad = idempotent(reachable, kana_rules, d0_cache, hb_of)
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
                "worse_detail": res8["worse_detail"][:12],
                "changed_rows": res8["changed_rows"]}

    pr("")
    pr("== S4/S5/S6/S7/S8 測定 ==")
    t1 = time.time()
    m_bekarazu = measure(["bekarazu"])
    m_bekarazaru = measure(["bekarazaru"])
    m_combo12 = measure(["bekarazu", "bekarazaru"])
    m_bekimari = measure(["bekimari"])
    m_combo123 = measure(["bekarazu", "bekarazaru", "bekimari"])
    pr("  (%.0fs)" % (time.time() - t1))

    for label, m in (("bekarazu", m_bekarazu), ("bekarazaru", m_bekarazaru),
                     ("combo12", m_combo12), ("bekimari", m_bekimari),
                     ("combo123", m_combo123)):
        pr("  %-11s 改写 %4d(4000内 %3d) better %4d/%3d worse %d/%d same %d | "
           "Δ8165 %.3f Δ4000 %.3f | avg 8165 %.3f→%.3f 4000 %.3f→%.3f | 幂等 bad %d"
           % (label, m["changed"], m["changed4000"], m["better"], m["better4000"],
              m["worse"], m["worse4000"], m["same"],
              m["delta8165"], m["delta4000"],
              m["full8165"]["avg_old"], m["full8165"]["avg_new"],
              m["full4000"]["avg_old"], m["full4000"]["avg_new"], m["idempotent_bad"]))
        pr("      worse_ids %s" % m["worse_ids"])
        for wd in m["worse_detail"][:6]:
            pr("      変差 %s %d→%d | got %s" % (wd["id"], wd["old"], wd["new"], wd["got"][:44]))

    # ---------- 硬断言 ----------
    pr("")
    pr("== 硬断言（N98 実測との逐位对照）==")
    g = m_bekarazu
    gate(g["changed"] == 78 and g["better"] == 70 and g["worse"] == 5,
         "S4 べからず %d/%d/%d != 78/70/5" % (g["changed"], g["better"], g["worse"]))
    gate(set(g["worse_ids"]) == {"shushu-4", "shukateki-1", "ryojo-3",
                                 "saio-x13", "toushisen216-7"},
         "S4 べからず変差行 %s != N98 実測 5 行" % g["worse_ids"])
    gate(close(g["delta8165"], -0.011), "S4 Δ8165 %.3f != -0.011" % g["delta8165"])
    gate(close(g["delta4000"], -0.008), "S4 Δ4000 %.3f != -0.008" % g["delta4000"])

    g = m_bekarazaru
    gate(g["changed"] == 82 and g["better"] == 79 and g["worse"] == 1,
         "S5 べからざる %d/%d/%d != 82/79/1" % (g["changed"], g["better"], g["worse"]))
    gate(g["worse_ids"] == ["shiseinishite-1"],
         "S5 べからざる変差行 %s != [shiseinishite-1]" % g["worse_ids"])
    gate(close(g["delta8165"], -0.011), "S5 Δ8165 %.3f != -0.011" % g["delta8165"])
    gate(close(g["delta4000"], -0.011), "S5 Δ4000 %.3f != -0.011" % g["delta4000"])

    g = m_combo12
    gate(g["changed"] == 157 and g["better"] == 146 and g["worse"] == 5,
         "S6 combo %d/%d/%d != 157/146/5" % (g["changed"], g["better"], g["worse"]))
    gate(set(g["worse_ids"]) == COMBO12_WORSE,
         "S6 combo 変差行 %s != N98 実測 5 行" % g["worse_ids"])
    gate(set(g["worse_ids"]).issubset(KNOWN6_TASK),
         "S6 combo 変差行が N98 已知 6 行集合外: %s"
         % sorted(set(g["worse_ids"]) - KNOWN6_TASK))
    gate(g["idempotent_bad"] == 0, "S6 combo 幂等 bad %d != 0" % g["idempotent_bad"])
    gate(close(g["delta8165"], -0.022), "S6 Δ8165 %.3f != -0.022" % g["delta8165"])
    gate(close(g["delta4000"], -0.019), "S6 Δ4000 %.3f != -0.019" % g["delta4000"])

    g = m_bekimari
    gate(g["changed"] == 31 and g["better"] == 29 and g["worse"] == 1,
         "S7 べきなり %d/%d/%d != 31/29/1" % (g["changed"], g["better"], g["worse"]))
    gate(g["worse_ids"] == ["p-gekirin-1"],
         "S7 べきなり変差行 %s != [p-gekirin-1]" % g["worse_ids"])
    gate(close(g["delta8165"], -0.006), "S7 Δ8165 %.3f != -0.006" % g["delta8165"])
    gate(close(g["delta4000"], -0.006), "S7 Δ4000 %.3f != -0.006" % g["delta4000"])

    g = m_combo123
    gate(len(g["worse_ids"]) == 6 and set(g["worse_ids"]) == TOTAL6_WORSE,
         "S8 三条 combo 変差行 %s != 6 行 %s" % (g["worse_ids"], sorted(TOTAL6_WORSE)))
    gate(set(g["worse_ids"]).issubset(KNOWN6_TASK | {"p-gekirin-1"}),
         "S8 変差行超出集合: %s"
         % sorted(set(g["worse_ids"]) - (KNOWN6_TASK | {"p-gekirin-1"})))
    gate(g["idempotent_bad"] == 0, "S8 三条 combo 幂等 bad %d != 0" % g["idempotent_bad"])
    gate(close(g["delta8165"], -0.028, 0.003), "S8 Δ8165 %.3f != ≈-0.028" % g["delta8165"])
    gate(close(g["delta4000"], -0.025, 0.003), "S8 Δ4000 %.3f != ≈-0.025" % g["delta4000"])
    pr("  全硬断言 PASS：三条 combo 変差 6 行 %s" % g["worse_ids"])

    # ---------- 输出 ----------
    slim = {k: v for k, v in m_combo123.items() if k != "changed_rows"}
    sim["gates"] = {"bekarazu": {k: v for k, v in m_bekarazu.items() if k != "changed_rows"},
                    "bekarazaru": {k: v for k, v in m_bekarazaru.items() if k != "changed_rows"},
                    "combo12": {k: v for k, v in m_combo12.items() if k != "changed_rows"},
                    "bekimari": {k: v for k, v in m_bekimari.items() if k != "changed_rows"},
                    "combo123": slim}
    sim["lev_impl"] = _LEV_IMPL
    sim["baseline"] = sim.get("baseline", {})
    sim["baseline"]["archive"] = "night97_results_8165.json / night97_results_4000.json"
    sim["elapsed_sec"] = round(time.time() - t_start)
    sim["verdict"] = "PASS"

    out_changed = os.path.join(EV, "night99_combo_changed_rows.json")
    json.dump(m_combo123["changed_rows"], open(out_changed, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    out_json = os.path.join(EV, "night99_sim.json")
    json.dump(sim, open(out_json, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night99_sim.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    pr("")
    pr("written: eval/night99_sim.json / night99_combo_changed_rows.json / night99_sim.txt")
    pr("PRED_4000=%d PRED_8165=%d | PRED_EXACT_4000=%d PRED_EXACT_8165=%d"
       % (m_combo123["changed4000"], m_combo123["changed"],
          m_combo123["pred_exact4000"], m_combo123["pred_exact8165"]))
    pr("elapsed %.0fs" % sim["elapsed_sec"])


def write_out():
    try:
        open(os.path.join(EV, "night99_sim.txt"), "w", encoding="utf-8", newline="\n").write(
            "\n".join(lines) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
