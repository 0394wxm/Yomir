# -*- coding: utf-8 -*-
"""night98_audit.py — Night 98 报告-only 夜：全项目状态审计＋待拍板清单 9 项复测（只读，TestClient 完整链）。

机制照抄 night96_sim.py（lev / apply_one / run / 行分类 / guard_forms）＋night97_eval_*.py
（golden 全量真跑・全行逐位对照）。本夜零改动产品代码：审计只读引擎、只写
eval/night98_audit.json 与 untracked 临时文件 eval/night98_check_4000.tmp.json /
eval/night98_check_8165.tmp.json（不覆盖任何已跟踪归档）。

PART A 现状复核（硬断言，对不上 exit 2）：
  A1 pytest tests -q → 469 passed
  A2 tools/verify_readme_facts.py → 22/22 exit 0
  A3 golden_4000 全量真跑 → vs night97_results_4000.json 全行逐位一致（13.488/24/0）
  A4 golden_8165 全量真跑 → vs night97_results_8165.json 全行逐位一致（13.496/30/0）
  A5 词库 import 实证 209+291+1031=1531

PART B 待拍板清单 9 项复测（数字以本夜实测为准，sim 基线＝night97_results_8165.json）：
  B1 べからず族：bekarazu／bekarazaru 各单独＋两条 combo 的双口径（4000/8165）Δ
  B2 べきなり→可きなり：bekimari 双口径 Δ（変差 1 p-gekirin-1）
  B3 なかれ→莫かれ：nakare_mokaku（post-N 17 行・kokyo09-5 唯一変差否）
  B4 がため／何のごとく：rikutou37-2／shiki050-4 现状（rerun tail 守り字有无）
  B5 は系 1 字块：wa_mashini／wa_imada（N92 blanket scramble 对照 265/207・172/131）
  B6 ことなき→こと莫き：kotonaki_moki（変差行・got 含莫かれ 行数 N96 vs N97）
  B7 嗟や→嗟乎：saya_kyo 在庫 Δ−0.000367 是否仍未达线＋同型歎詞语料统计
  B8 ことなく guard 外残量：当前 guard 外行集（白文侧字形分布）
  B9 N84 遗留：夹注残渣行实测・sonshi09-38・echo 30 行

用法: python -I tools/night98_audit.py
"""
import collections
import json
import os
import re
import subprocess
import sys
import time
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, ".night72_deps"))  # 隔离目录（あれば C 库）
EV = os.path.join(ROOT, "eval")

PY = sys.executable


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


def main():
    t_start = time.time()
    audit = {"script": "tools/night98_audit.py", "night": 98,
             "mode": "report-only audit (read-only engine)"}

    # ---------- PART A1: pytest ----------
    pr("== A1 pytest 全套 ==")
    p = subprocess.run([PY, "-m", "pytest", "tests", "-q", "--rootdir=."],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=1800)
    m = re.search(r"(\d+) passed(?:, (\d+) skipped)?", p.stdout or "")
    passed_n = int(m.group(1)) if m else -1
    audit["pytest"] = {"returncode": p.returncode, "passed": passed_n,
                       "tail": (p.stdout or "").strip().splitlines()[-1:] or []}
    pr("  pytest exit %d | %s" % (p.returncode, audit["pytest"]["tail"]))
    if passed_n != 469 or p.returncode != 0:
        pr("[FAIL] pytest %d passed != 469 → 停下报数" % passed_n)
        sys.exit(2)

    # ---------- PART A2: verify_readme_facts ----------
    pr("== A2 verify_readme_facts ==")
    p = subprocess.run([PY, "tools/verify_readme_facts.py"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=600)
    mv = re.search(r"README 比对:\s*(\d+)/(\d+)\s*对上", p.stdout or "")
    ok_n, tot_n = (int(mv.group(1)), int(mv.group(2))) if mv else (-1, -1)
    audit["verify"] = {"returncode": p.returncode, "ok": ok_n, "total": tot_n}
    pr("  verify exit %d | %d/%d" % (p.returncode, ok_n, tot_n))
    if p.returncode != 0 or (ok_n, tot_n) != (22, 22):
        pr("[FAIL] verify %d/%d exit %d != 22/22 exit 0 → 停下报数" % (ok_n, tot_n, p.returncode))
        sys.exit(2)

    # ---------- 词库 import 实证（A5，先做供断言） ----------
    pr("== A5 词库 import 实证 ==")
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
    audit["lexicon"] = lex
    if not (old_n == 209 and core_n == 500 and extra_n == 291 and ex2_n == 1031
            and ordered_n == 1531):
        pr("[FAIL] 词库实测 %s != 209+291+1031=1531 → 停下报数" % lex)
        sys.exit(2)

    # ---------- PART A3/A4: golden 双口径全量真跑 ----------
    from fastapi.testclient import TestClient
    from backend.main import app
    import backend.db as dbmod

    def full_run(golden_path, base_path, out_tmp, expect, label):
        golden = json.load(open(os.path.join(EV, golden_path), encoding="utf-8"))
        base = json.load(open(os.path.join(EV, base_path), encoding="utf-8"))["results"]
        assert len(golden) == len(base)
        assert [g["id"] for g in golden] == [b["id"] for b in base]
        old = {b["id"]: b for b in base}
        results = []
        t0 = time.time()
        with TestClient(app) as client:
            real = dbmod.save_kundoku
            dbmod.save_kundoku = lambda *a, **k: 1
            try:
                for i, g in enumerate(golden, 1):
                    r = client.post("/api/kundoku", json={"text": g["hakubun"]})
                    if r.status_code != 200:
                        results.append({"id": g["id"], "source_url": g.get("source_url", ""),
                                        "hakubun": g["hakubun"],
                                        "expected_kakikudashi": g["expected_kakikudashi"],
                                        "udkundoku_kakikudashi": None,
                                        "edit_distance": None, "exact_match": False,
                                        "error": repr(r.text)[:200]})
                        continue
                    got = r.json().get("kakikudashi", "")
                    a, b = norm(got), norm(g["expected_kakikudashi"])
                    results.append({
                        "id": g["id"], "source_url": g.get("source_url", ""),
                        "hakubun": g["hakubun"],
                        "expected_kakikudashi": g["expected_kakikudashi"],
                        "udkundoku_kakikudashi": got,
                        "edit_distance": lev(a, b),
                        "exact_match": a == b,
                    })
                    if i % 2000 == 0:
                        pr("    %s %d/%d (%.0fs)" % (label, i, len(golden), time.time() - t0))
            finally:
                dbmod.save_kundoku = real
        ok = [r for r in results if r["edit_distance"] is not None]
        n = len(ok)
        exact = sum(1 for r in ok if r["exact_match"])
        avg = round(sum(r["edit_distance"] for r in ok) / n, 3) if n else None
        errors = len(results) - n
        diff_rows = [r["id"] for r in results
                     if norm(r["udkundoku_kakikudashi"] or "") !=
                     norm(old[r["id"]]["udkundoku_kakikudashi"] or "")]
        fails = []
        if errors != expect["errors"]:
            fails.append("error %d != %d" % (errors, expect["errors"]))
        if exact != expect["exact"]:
            fails.append("exact %d != %d" % (exact, expect["exact"]))
        if avg != expect["avg"]:
            fails.append("avgDist %.3f != %.3f" % (avg, expect["avg"]))
        if diff_rows:
            fails.append("与 %s 不一致行 %d: %s" % (base_path, len(diff_rows), diff_rows[:8]))
        pr("  [%s] avgDist %.3f / exact %d / error %d | vs %s diff %d 行"
           % (label, avg, exact, errors, base_path, len(diff_rows)))
        if fails:
            pr("[FAIL] %s 硬断言不通过（先查实现，不改 expected）:" % label, )
            for f in fails:
                pr("  - %s" % f)
            sys.exit(2)
        json.dump({"total": len(results),
                   "summary": {"n": n, "errors": errors, "exact": exact, "avg_edit_distance": avg,
                               "expect": expect, "baseline": base_path,
                               "bit_identical_vs_baseline": True},
                   "results": results},
                  open(os.path.join(EV, out_tmp), "w", encoding="utf-8", newline="\n"),
                  ensure_ascii=False, indent=1)
        return {"avg": avg, "exact": exact, "errors": errors, "diff_rows": len(diff_rows)}

    pr("== A3 golden_4000 全量真跑（vs night97_results_4000.json）==")
    audit["golden_4000"] = full_run("golden_4000.json", "night97_results_4000.json",
                                    "night98_check_4000.tmp.json",
                                    {"avg": 13.488, "exact": 24, "errors": 0}, "4000")
    pr("== A4 golden_8165 全量真跑（vs night97_results_8165.json）==")
    audit["golden_8165"] = full_run("golden_8165.json", "night97_results_8165.json",
                                    "night98_check_8165.tmp.json",
                                    {"avg": 13.496, "exact": 30, "errors": 0}, "8165")

    # ---------- PART B 基准备 ----------
    doc8 = json.load(open(os.path.join(EV, "night97_results_8165.json"), encoding="utf-8"))
    golden8 = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    rows8 = [r for r in doc8["results"] if r.get("udkundoku_kakikudashi") is not None]
    assert len(rows8) == 8165
    doc4 = json.load(open(os.path.join(EV, "night97_results_4000.json"), encoding="utf-8"))
    rows4 = doc4["results"]
    assert [r["id"] for r in rows4] == [r["id"] for r in rows8[:4000]]

    # N97 vs N96 归档 got diff=0（合并夜逐位一致复核）
    doc8_n96 = json.load(open(os.path.join(EV, "night96_results_8165.json"), encoding="utf-8"))["results"]
    m96 = {b["id"]: b for b in doc8_n96}
    diff96 = [r["id"] for r in rows8
              if norm(r["udkundoku_kakikudashi"]) != norm(m96[r["id"]]["udkundoku_kakikudashi"])]
    pr("== B 基线：night97 vs night96 归档 got diff %d 行（合并夜门＝0）==" % len(diff96))
    if diff96:
        pr("[FAIL] night97/night96 归档差异 %d 行 != 0 → 停下报数" % len(diff96))
        sys.exit(2)
    audit["n97_vs_n96_diff"] = 0

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

    # 行分类＋guard 上下文（night96_sim 同款）
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
    pr("== 行分类 %s（期待 %s）==" % (dict(cc), EXPECTED_CLASS))
    audit["class"] = dict(cc)
    if dict(cc) != EXPECTED_CLASS:
        pr("[FAIL] 行分类実数 %s != 期待 %s → 停下报数" % (dict(cc), EXPECTED_CLASS))
        sys.exit(2)
    reachable = [r for r in rows8 if cls[r["id"]] in ("engine", "rerun")]

    d0_cache = {}
    for r in rows8:
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        d0_cache[r["id"]] = (got, exp, lev(got, exp))
    base_avg8 = round(sum(v[2] for v in d0_cache.values()) / 8165, 3)
    base_avg4 = round(sum(d0_cache[r["id"]][2] for r in rows4) / 4000, 3)
    pr("  reachable %d 行 | 基线 avgDist 4000=%.3f 8165=%.3f（归档 13.488/13.496）"
       % (len(reachable), base_avg4, base_avg8))

    # ---------- 候补表（9 项拍板对照・repl/guard 全部承 N86/N88/N92/N94/N96 sim 表） ----------
    CANDIDATES = {
        "bekarazu": {"kana": "べからず", "repl": "可からず", "guard": ("可",), "longer": (),
                     "tag": "拍板① べからず族（N86 89 行 79 改善 5 変差・Rule Q 16 行収録後残量 78）"},
        "bekarazaru": {"kana": "べからざる", "repl": "可からざる", "guard": ("可",), "longer": (),
                       "tag": "拍板① べからず族（N86 82 発火 79/1）"},
        "bekimari": {"kana": "べきなり", "repl": "可きなり", "guard": ("可",), "longer": (),
                     "tag": "拍板② べきなり→可きなり（N88 31 行 29 改善 1 変差 p-gekirin-1）"},
        "nakare_mokaku": {"kana": "なかれ", "repl": "莫かれ", "guard": ("莫",), "longer": (),
                          "tag": "拍板③ なかれ→莫かれ post-N（N94 17/13/1 kokyo09-5）"},
        "kotonaki_moki": {"kana": "ことなき", "repl": "こと莫き", "guard": ("莫",), "longer": (),
                          "tag": "拍板⑥ ことなき→こと莫き（N92 T4/N96 T9 禁区 2 変差）"},
        "saya_kyo": {"kana": "嗟や", "repl": "嗟乎", "guard": ("乎",), "longer": (),
                     "tag": "拍板⑦ 嗟や→嗟乎 在庫（N94 3/3/0 Δ−0.000367 線未達）"},
        "wa_mashini": {"kana": "は", "repl": "将に", "guard": ("将",), "longer": (),
                       "tag": "拍板⑤ は系（N92 T1 blanket 265/207）"},
        "wa_imada": {"kana": "は", "repl": "未だ", "guard": ("未",), "longer": (),
                     "tag": "拍板⑤ は系（N92 T2 blanket 172/131）"},
    }
    for k, c in CANDIDATES.items():
        assert normalize_shinjitai(c["repl"]) == c["repl"], "repl 非终字形: %s" % k

    def gate_one(key):
        c = CANDIDATES[key]
        rules = [(c["kana"], c["repl"], tuple(guard_forms(c["guard"])), c["longer"])]
        res8 = run(reachable, rules, d0_cache, hb_of)
        res4 = run(rows4, rules, d0_cache, hb_of)
        total_old8 = sum(d0_cache[r["id"]][2] for r in rows8)
        chg_map = {cr["id"]: cr for cr in res8["changed_rows"]}
        full_new8 = total_old8 + sum(cr["new_dist"] - cr["old_dist"] for cr in res8["changed_rows"])
        total_old4 = sum(d0_cache[r["id"]][2] for r in rows4)
        full_new4 = total_old4 + sum(
            (chg_map[r["id"]]["new_dist"] - chg_map[r["id"]]["old_dist"])
            for r in rows4 if r["id"] in chg_map)
        return {"kana": c["kana"], "repl": c["repl"], "guard": list(c["guard"]), "tag": c["tag"],
                "changed": res8["changed_entries"], "better": res8["better"],
                "worse": res8["worse"], "same": res8["same"],
                "delta_reachable": res8["delta"],
                "full8165": {"avg_old": round(total_old8 / 8165, 3),
                             "avg_new": round(full_new8 / 8165, 3),
                             "delta": round((full_new8 - total_old8) / 8165, 3)},
                "full4000": {"avg_old": round(total_old4 / 4000, 3),
                             "avg_new": round(full_new4 / 4000, 3),
                             "delta": round((full_new4 - total_old4) / 4000, 3)},
                "worse_detail": res8["worse_detail"][:12],
                "changed_rows": [{"id": cr["id"], "old": cr["old_dist"], "new": cr["new_dist"]}
                                 for cr in res8["changed_rows"]]}

    def combo_gate(keys):
        rules = [(CANDIDATES[k]["kana"], CANDIDATES[k]["repl"],
                  tuple(guard_forms(CANDIDATES[k]["guard"])), CANDIDATES[k]["longer"])
                 for k in keys]
        res8 = run(reachable, rules, d0_cache, hb_of)
        res4 = run(rows4, rules, d0_cache, hb_of)
        total_old8 = sum(d0_cache[r["id"]][2] for r in rows8)
        chg_map = {cr["id"]: cr for cr in res8["changed_rows"]}
        full_new8 = total_old8 + sum(cr["new_dist"] - cr["old_dist"] for cr in res8["changed_rows"])
        total_old4 = sum(d0_cache[r["id"]][2] for r in rows4)
        full_new4 = total_old4 + sum(
            (chg_map[r["id"]]["new_dist"] - chg_map[r["id"]]["old_dist"])
            for r in rows4 if r["id"] in chg_map)
        bad = idempotent(reachable, rules, d0_cache, hb_of)
        return {"combo": keys, "changed": res8["changed_entries"], "better": res8["better"],
                "worse": res8["worse"], "same": res8["same"], "idempotent_bad": bad,
                "full8165": {"avg_old": round(total_old8 / 8165, 3),
                             "avg_new": round(full_new8 / 8165, 3),
                             "delta": round((full_new8 - total_old8) / 8165, 3)},
                "full4000": {"avg_old": round(total_old4 / 4000, 3),
                             "avg_new": round(full_new4 / 4000, 3),
                             "delta": round((full_new4 - total_old4) / 4000, 3)},
                "worse_detail": res8["worse_detail"][:12]}

    board = {}
    pr("")
    pr("== B1 べからず族：べからず→可からず／べからざる→可からざる ==")
    t1 = time.time()
    board["bekarazu"] = gate_one("bekarazu")
    board["bekarazaru"] = gate_one("bekarazaru")
    board["bekarazu_zaru_combo"] = combo_gate(["bekarazu", "bekarazaru"])
    for k in ("bekarazu", "bekarazaru", "bekarazu_zaru_combo"):
        b = board[k]
        pr("  %-20s 改写 %4d better %4d worse %d | Δ8165 %.3f Δ4000 %.3f | avg %.3f→%.3f(8165)"
           % (k, b["changed"], b["better"], b["worse"],
              b["full8165"]["delta"], b["full4000"]["delta"],
              b["full8165"]["avg_old"], b["full8165"]["avg_new"]))
        for wd in b["worse_detail"][:6]:
            pr("      変差 %s %d→%d | got %s" % (wd["id"], wd["old"], wd["new"], wd["got"][:44]))
    pr("  (%.0fs)" % (time.time() - t1))

    pr("")
    pr("== B2 べきなり→可きなり ==")
    board["bekimari"] = gate_one("bekimari")
    b = board["bekimari"]
    pr("  改写 %d better %d worse %d | Δ8165 %.3f Δ4000 %.3f"
       % (b["changed"], b["better"], b["worse"], b["full8165"]["delta"], b["full4000"]["delta"]))
    for wd in b["worse_detail"]:
        pr("      変差 %s %d→%d | got %s" % (wd["id"], wd["old"], wd["new"], wd["got"][:50]))

    pr("")
    pr("== B3 なかれ→莫かれ post-N ==")
    board["nakare_mokaku"] = gate_one("nakare_mokaku")
    b = board["nakare_mokaku"]
    pr("  改写 %d better %d worse %d | Δ8165 %.3f" % (b["changed"], b["better"], b["worse"],
                                                      b["full8165"]["delta"]))
    for wd in b["worse_detail"]:
        pr("      変差 %s %d→%d | got %s" % (wd["id"], wd["old"], wd["new"], wd["got"][:50]))

    pr("")
    pr("== B4 がため／何のごとく 各 1 行现状 ==")
    b4 = {}
    for rid, key in (("rikutou37-2", "がため"), ("shiki050-4", "何のごとく")):
        r = next((x for x in rows8 if x["id"] == rid), None)
        if r is None:
            b4[rid] = {"in_corpus": False}
            pr("  %s：语料中不存在（漂移）" % rid)
            continue
        got, exp, d0 = d0_cache[rid]
        hb = hb_of[rid]
        keepers = [g for g in ("莫", "勿", "毋", "無", "罔") if g in hb]
        b4[rid] = {"in_corpus": True, "cls": cls[rid], "got": got, "expected": exp,
                   "got_has_key": key in got, "hb_tail": hb[:60],
                   "keeper_chars_in_hb": keepers}
        pr("  %s: cls=%s | got 含 %s=%s | tail=%s | 守り字 %s"
           % (rid, cls[rid], key, key in got, hb[:44], keepers or "無し"))
    board["gatanai_nanogotoku"] = b4

    pr("")
    pr("== B5 は系 1 字块 blanket（は→将に／は→未だ）==")
    board["wa_mashini"] = gate_one("wa_mashini")
    board["wa_imada"] = gate_one("wa_imada")
    for k in ("wa_mashini", "wa_imada"):
        b = board[k]
        pr("  %-12s 改写 %4d better %4d worse %4d（N92 对照 265/207・172/131）"
           % (k, b["changed"], b["better"], b["worse"]))

    pr("")
    pr("== B6 ことなき→こと莫き（got 含莫かれ 行数 N96 vs N97）==")
    board["kotonaki_moki"] = gate_one("kotonaki_moki")
    b = board["kotonaki_moki"]
    pr("  改写 %d better %d worse %d | 変差行 %s"
       % (b["changed"], b["better"], b["worse"],
          [(wd["id"], wd["old"], wd["new"]) for wd in b["worse_detail"][:4]]))
    mok96 = sum(1 for r in doc8_n96 if "莫かれ" in norm(r["udkundoku_kakikudashi"]))
    mok97 = sum(1 for r in rows8 if "莫かれ" in norm(r["udkundoku_kakikudashi"]))
    pr("  got 含莫かれ 行数: night96=%d night97=%d" % (mok96, mok97))
    board["got_mokukare_rows"] = {"night96": mok96, "night97": mok97}

    pr("")
    pr("== B7 嗟や→嗟乎 在庫＋同型歎詞语料统计 ==")
    board["saya_kyo"] = gate_one("saya_kyo")
    b = board["saya_kyo"]
    pr("  改写 %d better %d worse %d Δ8165 %.3f（在庫 N94 Δ−0.000367）"
       % (b["changed"], b["better"], b["worse"], b["full8165"]["delta"]))
    excl = {}
    for w in ("嗟乎", "嗟夫", "呜呼", "于嗟", "嗟哉", "嗟"):
        got_n = sum(1 for r in rows8 if w in norm(r["udkundoku_kakikudashi"]))
        exp_n = sum(1 for r in rows8 if w in norm(r["expected_kakikudashi"]))
        excl[w] = {"got_rows": got_n, "exp_rows": exp_n}
        pr("  %-4s got %3d 行 / exp %3d 行" % (w, got_n, exp_n))
    board["interjection_corpus"] = excl

    pr("")
    pr("== B8 ことなく guard 外残量（Rule Q guard 莫）==")
    gf_motsu = guard_forms(("莫",))
    guard_out = []
    for r in reachable:
        got = d0_cache[r["id"]][0]
        if "ことなく" in got and not any(f in hb_of[r["id"]] for f in gf_motsu):
            guard_out.append({"id": r["id"], "cls": cls[r["id"]],
                              "hb": hb_of[r["id"]][:80], "got": got[:80]})
    pr("  guard 外 ことなく 行数 %d（历夜 5）" % len(guard_out))
    for g_ in guard_out:
        pr("    %s (%s) hb %s" % (g_["id"], g_["cls"], g_["hb"]))
    board["kotonaku_guard_outside"] = guard_out

    pr("")
    pr("== B9 N84 遗留三项 ==")
    # (i) 夹注残渣行（kanbun 分支・含（・got 含（…）假名残渣）
    paren_rows = []
    for r in rows8:
        raw = r["hakubun"] or ""
        if cls[r["id"]] == "engine" and "（" in raw:
            got = d0_cache[r["id"]][0]
            if re.search(r"（[^（）]*[ぁ-ゖー][^（）]*）", got):
                paren_rows.append({"id": r["id"], "got": got[:90]})
    pr("  夹注残渣行（engine 分支・got 带（…）假名）：%d 行（N84 记录 8）" % len(paren_rows))
    for p_ in paren_rows:
        pr("    %s got %s" % (p_["id"], p_["got"]))
    # (ii) sonshi09-38（no_tail 空串）
    sonshi = d0_cache.get("sonshi09-38")
    b_sonshi = {"cls": cls.get("sonshi09-38"), "got": sonshi[0] if sonshi else None,
                "dist": sonshi[2] if sonshi else None}
    pr("  sonshi09-38: cls=%s got=%r d0=%s（N84：无尾段空串保持）"
       % (b_sonshi["cls"], b_sonshi["got"], b_sonshi["dist"]))
    # (iii) echo 30 行
    echo_rows = [{"id": r["id"], "tail": hb_of[r["id"]],
                  "got": d0_cache[r["id"]][0], "d0": d0_cache[r["id"]][2]}
                 for r in rows8 if cls[r["id"]] == "echo"]
    echo_got_eq_tail = sum(1 for e in echo_rows if e["got"] == e["tail"])
    echo_zero = sum(1 for e in echo_rows if e["d0"] == 0)
    pr("  echo %d 行（N84 记录 30）| got==尾段直出 %d 行 | d0==0 %d 行"
       % (len(echo_rows), echo_got_eq_tail, echo_zero))
    board["n84_legacy"] = {"paren_residue_rows": paren_rows,
                           "paren_residue_count": len(paren_rows),
                           "sonshi09_38": b_sonshi,
                           "echo_count": len(echo_rows),
                           "echo_got_eq_tail": echo_got_eq_tail,
                           "echo_zero_dist": echo_zero,
                           "echo_ids": [e["id"] for e in echo_rows]}

    # ---------- 输出 ----------
    audit["board"] = {k: v for k, v in board.items()}
    audit["lev_impl"] = _LEV_IMPL
    audit["baseline"] = "night97_results_8165.json / night97_results_4000.json"
    audit["elapsed_sec"] = round(time.time() - t_start)
    out = os.path.join(EV, "night98_audit.json")
    json.dump(audit, open(out, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night98_audit.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    pr("")
    pr("written: eval/night98_audit.json / night98_audit.txt（+ night98_check_*.tmp.json untracked）")
    pr("elapsed %.0fs" % audit["elapsed_sec"])


if __name__ == "__main__":
    main()
