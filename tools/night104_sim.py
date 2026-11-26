# -*- coding: utf-8 -*-
"""night104_sim.py — Night 104 拍板夜：なかれ→莫かれ 复活収録前 sim 検証（night99_sim 型）。

用户 2026-11-26 拍板（N98 §3 决策表項 3・N99 同框）：なかれ→莫かれ（guard 莫）允变差
1 行（kokyo09-5），撤 0 变差硬门仅限本条；排除 guard 已在 N86 实测否定不再试。
変差行总数须为 1 行（kokyo09-5・N98 実測 15→16・死因＝白文「嚴父莫大於配天」莫大
co-occurrence＝got「すことなかれ」行・exp 側は「…大なるは莫し」＝莫し/莫かれ 字形差・
N78 実測否定判别式＝不另加排除 guard・不修死因＝拍板条件），超出即停下报数（exit 2）。

机制照抄 tools/night99_sim.py（lev / _apply_count / run / 行分类 / guard_forms）。
sim 基线＝night101_results_8165.json / night101_results_4000.json（N101 链尾＝Rule T
3 条生效済み、U の链尾追加位置と同じ出発点）。N98 実測 17 改写 13 改善 1 変差は
night97 基线（Rule T 無し）で測定——Rule T は べからず族・べきなり のみ触り なかれ 行は
非改写なので 17/13/1 は night101 基线でも复现する前提（本 sim がそれを gate する）。

硬断言（对不上 exit 2＝「停下报数」）：
  S1 行分类 engine 7916 / echo 30 / rerun 218 / no_tail 1（reachable 8134）
  S2 night101 vs night100 归档 got diff 0 行（合并夜门＝0・基线健全性）
  S3 基线 avgDist 4000=13.462 / 8165=13.469（归档値再計算一致）＋exact 24/30＋词库 1531
  S4 guard_forms(莫)＝["莫"]（新旧変異なし＝双形并查同形）＋repl 终字形＋莫かれ に
     なかれ 非含有（構造冪等）＋長詞マスク なかれ主義（事勿れ主義＝N64 probe 守り）
  S5 なかれ→莫かれ：17 改写 13 改善 1 変差（worse_ids＝["kokyo09-5"] 恰 1 行）
     Δ8165 ≈ −0.002・幂等 bad 0
  S6 echo/no_tail 規則不可達（30+1 行 got に なかれ 无し＝製品側の空白文発火と
     sim skip の意味差は不発）＋engine/rerun 全行 hb 非空（guard 語义乖離なし）

输出 eval/night104_sim.json（全実績＋変差行明细）＋ eval/night104_changed_rows.json
（改写 17 行预测＝night104_eval_* の逐位对照源）＋ eval/night104_sim.txt。
用法: python -I tools/night104_sim.py
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

# N98 実測（night97 基线・本夜拍板の根拠）：17 改写 13 改善 1 変差・kokyo09-5 15→16
WORSE_ALLOWED = ["kokyo09-5"]


def close(x, y, tol=0.0005):
    return abs(x - y) <= tol


def main():
    t_start = time.time()
    sim = {"script": "tools/night104_sim.py", "night": 104,
           "mode": "拍板夜 Rule U 1 条 sim 検証（なかれ→莫かれ guard 莫・変差 1 行 kokyo09-5 許容）"}

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
                   and "なかれ" in norm(r["udkundoku_kakikudashi"])]
    gate(not unreach_key, "S6 echo/no_tail 行に なかれ 出現（規則可達化で sim/実跑乖離の恐れ）: %s"
         % unreach_key[:8])
    empty_hb = [r["id"] for r in reachable if not hb_of[r["id"]]]
    gate(not empty_hb, "S6 engine/rerun に hb 空行（guard 語义乖離の恐れ）: %s" % empty_hb[:8])
    pr("== S6 echo/no_tail 規則不可達（なかれ 0 行）＋reachable 全行 hb 非空 ✓ ==")

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
                       "exact4000": exact_base4, "exact8165": exact_base8}
    gate(close(base_avg4, 13.462), "基线 avgDist 4000 %.3f != 13.462" % base_avg4)
    gate(close(base_avg8, 13.469), "基线 avgDist 8165 %.3f != 13.469" % base_avg8)
    gate(exact_base4 == 24 and exact_base8 == 30,
         "基线 exact %d/%d != 24/30" % (exact_base4, exact_base8))

    # ---------- 候补表（1 条拍板・guard 莫＝新旧変異なし・longer 空壳） ----------
    CANDIDATES = {
        "nakare": {"kana": "なかれ", "repl": "莫かれ", "guard": ("莫",), "longer": ("なかれ主義",),
                   "tag": "拍板項 3 なかれ→莫かれ（N98 実測 17/13/1・kokyo09-5 15→16）"},
    }
    for k, c in CANDIDATES.items():
        gate(normalize_shinjitai(c["repl"]) == c["repl"], "repl 非终字形: %s" % k)
    gate("なかれ" not in "莫かれ", "構造冪等：repl 莫かれ に なかれ 含有")
    gf_boku = guard_forms(("莫",))
    pr("== 候补 guard_forms(莫)=%s（莫 は新旧変異なし＝双形并查同形）==" % gf_boku)
    gate(gf_boku == ["莫"], "guard_forms(莫) != ['莫']")
    gate(new_to_old.get("莫") is None and old_to_new.get("莫") is None,
         "莫 が SHINJITAI_MAP に存在（双形并查前提崩れ）")

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
    pr("== S5 測定（なかれ→莫かれ guard 莫・単条）==")
    t1 = time.time()
    m_nakare = measure(["nakare"])
    pr("  (%.0fs)" % (time.time() - t1))

    m = m_nakare
    pr("  %-8s 改写 %4d(4000内 %3d) better %4d/%3d worse %d/%d same %d | "
       "Δ8165 %.3f Δ4000 %.3f | avg 8165 %.3f→%.3f 4000 %.3f→%.3f | 幂等 bad %d"
       % ("nakare", m["changed"], m["changed4000"], m["better"], m["better4000"],
          m["worse"], m["worse4000"], m["same"],
          m["delta8165"], m["delta4000"],
          m["full8165"]["avg_old"], m["full8165"]["avg_new"],
          m["full4000"]["avg_old"], m["full4000"]["avg_new"], m["idempotent_bad"]))
    pr("      worse_ids %s" % m["worse_ids"])
    for wd in m["worse_detail"][:6]:
        pr("      変差 %s %d→%d | got %s" % (wd["id"], wd["old"], wd["new"], wd["got"][:44]))

    # ---------- 硬断言（N98 実測との逐位对照） ----------
    pr("")
    pr("== 硬断言（N98 §3 項 3 実測 17/13/1 との逐位对照）==")
    g = m_nakare
    gate(g["changed"] == 17 and g["better"] == 13 and g["worse"] == 1,
         "S5 なかれ→莫かれ %d/%d/%d != 17/13/1（N98 実測）"
         % (g["changed"], g["better"], g["worse"]))
    gate(g["worse_ids"] == WORSE_ALLOWED,
         "S5 変差行 %s != 拍板許容 1 行 %s（kokyo09-5 恰 1 行・超出＝即停止）"
         % (g["worse_ids"], WORSE_ALLOWED))
    in4 = any(r["id"] == WORSE_ALLOWED[0] for r in rows4)
    exp4 = list(WORSE_ALLOWED) if in4 else []
    gate(g["worse_ids4000"] == exp4,
         "S5 4000 口径変差行 %s != %s（kokyo09-5 の 4000 内外と不整合）"
         % (g["worse_ids4000"], exp4))
    gate(g["idempotent_bad"] == 0, "S5 幂等 bad %d != 0" % g["idempotent_bad"])
    gate(close(g["delta8165"], -0.002), "S5 Δ8165 %.3f != -0.002（N98 実測）" % g["delta8165"])
    pr("  全硬断言 PASS：変差 1 行 %s（Δ8165 %.3f・Δ4000 %.3f 実測記録）"
       % (g["worse_ids"], g["delta8165"], g["delta4000"]))

    # ---------- 输出 ----------
    sim["gates"] = {"nakare": {k: v for k, v in m_nakare.items() if k != "changed_rows"}}
    sim["lev_impl"] = _LEV_IMPL
    sim["baseline"]["archive"] = ("night101_results_8165.json / night101_results_4000.json"
                                  "（N101 链尾＝Rule T 生效済み）")
    sim["elapsed_sec"] = round(time.time() - t_start)
    sim["verdict"] = "PASS"

    out_changed = os.path.join(EV, "night104_changed_rows.json")
    json.dump(m_nakare["changed_rows"], open(out_changed, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    out_json = os.path.join(EV, "night104_sim.json")
    json.dump(sim, open(out_json, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night104_sim.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    pr("")
    pr("written: eval/night104_sim.json / night104_changed_rows.json / night104_sim.txt")
    pr("PRED_4000=%d PRED_8165=%d | PRED_EXACT_4000=%d PRED_EXACT_8165=%d"
       % (m_nakare["changed4000"], m_nakare["changed"],
          m_nakare["pred_exact4000"], m_nakare["pred_exact8165"]))
    pr("elapsed %.0fs" % sim["elapsed_sec"])


def write_out():
    try:
        open(os.path.join(EV, "night104_sim.txt"), "w", encoding="utf-8", newline="\n").write(
            "\n".join(lines) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
