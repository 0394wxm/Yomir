# -*- coding: utf-8 -*-
"""night109_status.py — Night 109 (e)：項 9 N84 遗留现状确认（报告-only・不设计剥夹注管线）。

任务书：夹注残渣是否仍为 2 行（rikutou59-2・soji07-6）、sonshi09-38 是否仍空串、
echo 是否仍为 30 行——只确认现状。判定口径＝tools/night98_audit.py B9（N98 実測源）：
  (i)  夹注残渣 = engine 行 ∧ 白文含（ ∧ got 含（…仮名…）〔re （[^（）]*[ぁ-ゖー][^（）]*）〕
  (ii) sonshi09-38 = no_tail 空串行・d0 実測
  (iii) echo 30 行 = 分类 echo 行数・got==尾段直出数・残り got==新字体化(尾段)数
基线＝night107_results_8165.json（现 master 链尾）。旧数对照＝N98 §3 項 9：
残渣 2 行（N84 报告文字 8 行＝口径混写・N95 step 0 先例以 JSON 为准）・sonshi d0=13・
echo 30（got==tail 14＋新字体化 16）。
输出 eval/night109_status.json + eval/night109_status.txt。
用法: python -I tools/night109_status.py
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

OLD = {"paren_rows": ["rikutou59-2", "soji07-6"],
       "sonshi09_38": {"cls": "no_tail", "d0": 13},
       "echo": {"count": 30, "got_eq_tail": 14, "shinjitai": 16}}

lines = []
DRIFT = []


def pr(s=""):
    lines.append(s)
    print(s, flush=True)


def gate(cond, msg):
    if not cond:
        pr("[FAIL] %s → 停下报数" % msg)
        board["verdict"] = "FAIL"
        write_out()
        sys.exit(2)


def cmp_val(item, field, old, new):
    if isinstance(old, float) or isinstance(new, float):
        ok = round(float(old), 6) == round(float(new), 6)
    else:
        ok = old == new
    if ok:
        pr("  [一致] %s.%s = %s" % (item, field, old))
    else:
        DRIFT.append({"item": item, "field": field, "old": old, "new": new})
        pr("  [DRIFT] %s.%s 旧 %s → 新 %s" % (item, field, old, new))


def write_out():
    try:
        open(os.path.join(EV, "night109_status.txt"), "w", encoding="utf-8",
             newline="\n").write("\n".join(lines) + "\n")
    except Exception:
        pass


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


board = {}


def main():
    t_start = time.time()
    board = {"script": "tools/night109_status.py", "night": 109,
             "mode": "項 9 N84 遗留现状确认（夹注残渣/sonshi09-38/echo 30）",
             "verdict": None}
    pr("== night107 归档読込 ==")
    doc8 = json.load(open(os.path.join(EV, "night107_results_8165.json"), encoding="utf-8"))
    rows8 = [r for r in doc8["results"] if r.get("udkundoku_kakikudashi") is not None]
    gate(len(rows8) == 8165, "night107_results_8165 行数 %d != 8165" % len(rows8))

    from backend.main import detect_text_type, _ruby_tail_kanbun
    from backend.kundoku_rules import normalize_shinjitai
    cls, tail_raw = {}, {}
    for r in rows8:
        raw = r["hakubun"] or ""
        t = None
        if detect_text_type(raw) == "kana":
            t = _ruby_tail_kanbun(raw)
            if not t:
                cls[r["id"]] = "no_tail"
            elif len(t) <= 8:
                cls[r["id"]] = "echo"
            else:
                cls[r["id"]] = "rerun"
        else:
            cls[r["id"]] = "engine"
        tail_raw[r["id"]] = t if cls[r["id"]] in ("echo", "rerun", "no_tail") else None
    cc = collections.Counter(cls.values())
    pr("  行分类 %s" % dict(cc))
    gate(cc.get("echo", 0) == 30 and cc.get("no_tail", 0) == 1,
         "echo/no_tail 行数 %s != 30/1（分类前提）" % dict(cc))

    got = {r["id"]: norm(r["udkundoku_kakikudashi"]) for r in rows8}
    exp = {r["id"]: norm(r["expected_kakikudashi"]) for r in rows8}

    pr("")
    pr("== (i) 夹注残渣行（engine 分支・got 带（…）仮名残渣・night98_audit B9 同款）==")
    paren_rows = []
    for r in rows8:
        raw = r["hakubun"] or ""
        if cls[r["id"]] == "engine" and "（" in raw:
            if re.search(r"（[^（）]*[ぁ-ゖー][^（）]*）", got[r["id"]]):
                paren_rows.append({"id": r["id"], "got": got[r["id"]][:90]})
    pr("  夹注残渣行：%d 行（N98 実測 2＝rikutou59-2・soji07-6）" % len(paren_rows))
    for p_ in paren_rows:
        pr("    %s got %s" % (p_["id"], p_["got"]))
    cmp_val("paren_residue", "count", 2, len(paren_rows))
    cmp_val("paren_residue", "ids", OLD["paren_rows"],
            sorted(p_["id"] for p_ in paren_rows))
    board["paren_residue_rows"] = paren_rows

    pr("")
    pr("== (ii) sonshi09-38（no_tail 空串保持）==")
    sonshi_id = "sonshi09-38"
    gate(cls.get(sonshi_id) == "no_tail", "sonshi09-38 分类 %s != no_tail" % cls.get(sonshi_id))
    sonshi = {"cls": cls.get(sonshi_id), "tail": tail_raw.get(sonshi_id),
              "got": got.get(sonshi_id), "exp": exp.get(sonshi_id),
              "d0": lev(got.get(sonshi_id, ""), exp.get(sonshi_id, ""))}
    pr("  sonshi09-38: cls=%s tail=%r d0=%d（N98 記録 d0=13）"
       % (sonshi["cls"], sonshi["tail"], sonshi["d0"]))
    cmp_val("sonshi09_38", "cls", OLD["sonshi09_38"]["cls"], sonshi["cls"])
    cmp_val("sonshi09_38", "tail_empty", True, sonshi["tail"] == "")
    cmp_val("sonshi09_38", "d0", OLD["sonshi09_38"]["d0"], sonshi["d0"])
    board["sonshi09_38"] = sonshi

    pr("")
    pr("== (iii) echo 30 行（got==尾段直出／新字体化差し替え）==")
    echo_rows = []
    for r in rows8:
        if cls[r["id"]] != "echo":
            continue
        rid = r["id"]
        t = tail_raw[rid] or ""
        g, tn = got[rid], norm(t)
        kind = "direct" if g == tn else ("shinjitai" if g == norm(normalize_shinjitai(t))
                                         else "other")
        echo_rows.append({"id": rid, "kind": kind,
                          "tail": tn, "got": g,
                          "d0": lev(g, exp[rid])})
    n_direct = sum(1 for e in echo_rows if e["kind"] == "direct")
    n_shin = sum(1 for e in echo_rows if e["kind"] == "shinjitai")
    n_other = sum(1 for e in echo_rows if e["kind"] == "other")
    n_zero = sum(1 for e in echo_rows if e["d0"] == 0)
    pr("  echo %d 行 | got==尾段直出 %d | 新字体化差し替え %d | other %d | d0==0 %d 行"
       % (len(echo_rows), n_direct, n_shin, n_other, n_zero))
    if n_other:
        for e in echo_rows:
            if e["kind"] == "other":
                pr("    other %s tail %r got %r" % (e["id"], e["tail"], e["got"]))
    for e in echo_rows:
        if e["kind"] == "shinjitai":
            pr("    新字体化 %s tail %s → got %s" % (e["id"], e["tail"], e["got"]))
    cmp_val("echo", "count", OLD["echo"]["count"], len(echo_rows))
    cmp_val("echo", "got_eq_tail", OLD["echo"]["got_eq_tail"], n_direct)
    cmp_val("echo", "shinjitai", OLD["echo"]["shinjitai"], n_shin)
    if n_other:
        DRIFT.append({"item": "echo", "field": "other", "old": 0, "new": n_other})
        pr("  [DRIFT] echo.other 旧 0 → 新 %d（direct/shinjitai 以外の差し替え形）" % n_other)
    board["echo"] = {"count": len(echo_rows), "direct": n_direct,
                     "shinjitai": n_shin, "other": n_other, "d0_zero": n_zero,
                     "rows": echo_rows}

    pr("")
    pr("== 盘点汇总：(e) 項 9 现状＝残渣 %d 行・sonshi09-38 d0=%d・echo %d 行"
       "（直出 %d＋新字体化 %d）・漂移 %d 件 =="
       % (len(paren_rows), sonshi["d0"], len(echo_rows), n_direct, n_shin, len(DRIFT)))
    board["drift"] = DRIFT
    board["lev_impl"] = _LEV_IMPL
    board["baseline"] = "night107_results_8165.json"
    board["elapsed_sec"] = round(time.time() - t_start)
    board["verdict"] = "PASS"
    json.dump(board, open(os.path.join(EV, "night109_status.json"), "w",
                          encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night109_status.txt"), "w", encoding="utf-8",
         newline="\n").write("\n".join(lines) + "\n")
    pr("")
    pr("written: eval/night109_status.json / night109_status.txt")
    pr("DRIFT=%d" % len(DRIFT))
    pr("elapsed %.0fs" % board["elapsed_sec"])


if __name__ == "__main__":
    main()
