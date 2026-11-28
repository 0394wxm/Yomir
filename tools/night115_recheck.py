# -*- coding: utf-8 -*-
"""night115_recheck.py — Night 115 ②：剥夹注管線設計夜・現状重测（sim-first・禁抄旧数）。

基线＝night111 归档（4000 13.455/24/0・8165 13.464/30/0＝N114 合并夜記録）。
重测口径：
  (A) 行分类（engine/echo/no_tail/rerun）復核＝N113 記録 7916/30/218/1・reachable 8134
  (B) 夹注残渣 2 行（rikutou59-2・soji07-6）：night98_audit B9 判定式逐位重测
      ＝engine 行 ∧ 白文含（ ∧ got 含（…仮名…）〔re （[^（）]*[ぁ-ゖー][^（）]*）〕
      各行＝d0 lev(got,exp)／d1 lev(白文,exp)・白文（ 位置・got（…仮名…）形態全 span・exp
  (C) sonshi09-38：no_tail 確認（tail 空串・got 空串・d0=13）＝剥夹注管線外の設計入力
  (D) echo 30 行：構成重测（直出/新字体化/other・d0==0）＋逐行分類
      ＝含（注记 行数・与夹注无关 行数（echo が管線範囲内かの設計入力）
  (E) census：8165 中白文含（ 行数（分類別内訳）・got 含（ 行数・got 含（…仮名…） 行数・
      4000 内対応行数（管線影響面定量）
漂移判定＝N113 §2(e)/N109 §2(e) 記録値との cmp_val。输出 eval/night115_recheck.json + .txt。
用法: python -I tools/night115_recheck.py
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

OLD = {"cls": {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1},
       "reachable": 8134,
       "paren_rows": ["rikutou59-2", "soji07-6"],
       "sonshi09_38": {"cls": "no_tail", "tail_empty": True, "d0": 13},
       "echo": {"count": 30, "got_eq_tail": 14, "shinjitai": 16, "other": 0, "d0_zero": 0},
       # N114 合并夜記録（night111 归档基线）
       "avg4": 13.455, "exact4": 24, "avg8": 13.464, "exact8": 30}

PAREN_KANA = re.compile(r"（[^（）]*[ぁ-ゖー][^（）]*）")

lines = []
DRIFT = []
board = {}


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
        open(os.path.join(EV, "night115_recheck.txt"), "w", encoding="utf-8",
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
    _LEV_IMPL = "纯 Python 回退"


def lev(a, b):
    if _lev_c is not None:
        return _lev_c(a, b)
    return _lev_pure(a, b)


def norm(s):
    return re.sub(r"\s+", "", s or "")


def main():
    t_start = time.time()
    board = {"script": "tools/night115_recheck.py", "night": 115,
             "mode": "剥夹注管線設計夜・現状重测（sim-first・night111 基线）",
             "verdict": None}
    pr("== night111 归档読込（双口径）==")
    doc8 = json.load(open(os.path.join(EV, "night111_results_8165.json"), encoding="utf-8"))
    doc4 = json.load(open(os.path.join(EV, "night111_results_4000.json"), encoding="utf-8"))
    rows8 = [r for r in doc8["results"] if r.get("udkundoku_kakikudashi") is not None]
    rows4 = [r for r in doc4["results"] if r.get("udkundoku_kakikudashi") is not None]
    gate(len(rows8) == 8165, "night111_results_8165 行数 %d != 8165" % len(rows8))
    gate(len(rows4) == 4000, "night111_results_4000 行数 %d != 4000" % len(rows4))

    # 基线数字重算（禁抄旧数＝归档 edit_distance/exact_match 再集計）
    avg8 = round(sum(r["edit_distance"] for r in rows8) / len(rows8), 3)
    avg4 = round(sum(r["edit_distance"] for r in rows4) / len(rows4), 3)
    exact8 = sum(1 for r in rows8 if r["exact_match"])
    exact4 = sum(1 for r in rows4 if r["exact_match"])
    # error 行数は生 results で数える（rows8/rows4 は None 除け済み＝恒 0 の堕胎防止）
    err8 = sum(1 for r in doc8["results"] if r.get("udkundoku_kakikudashi") is None)
    err4 = sum(1 for r in doc4["results"] if r.get("udkundoku_kakikudashi") is None)
    pr("  4000: avgDist %s / exact %d / error %d（N114 記録 13.455/24/0）"
       % (avg4, exact4, err4))
    pr("  8165: avgDist %s / exact %d / error %d（N114 記録 13.464/30/0）"
       % (avg8, exact8, err8))
    cmp_val("baseline", "avg4000", OLD["avg4"], avg4)
    cmp_val("baseline", "exact4000", OLD["exact4"], exact4)
    cmp_val("baseline", "avg8165", OLD["avg8"], avg8)
    cmp_val("baseline", "exact8165", OLD["exact8"], exact8)
    gate(err8 == 0, "8165 error 行 %d != 0" % err8)
    board["baseline"] = {"avg4": avg4, "exact4": exact4, "avg8": avg8, "exact8": exact8}

    from backend.main import detect_text_type, _ruby_tail_kanbun
    from backend.kundoku_rules import normalize_shinjitai

    pr("")
    pr("== (A) 行分类復核（N113 記録 7916/30/218/1・reachable 8134）==")
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
    reach = sum(1 for r in rows8 if cls[r["id"]] in ("engine", "rerun"))
    pr("  reachable（engine+rerun＝引擎可达）%d 行" % reach)
    cmp_val("cls", "engine", OLD["cls"]["engine"], cc.get("engine", 0))
    cmp_val("cls", "echo", OLD["cls"]["echo"], cc.get("echo", 0))
    cmp_val("cls", "rerun", OLD["cls"]["rerun"], cc.get("rerun", 0))
    cmp_val("cls", "no_tail", OLD["cls"]["no_tail"], cc.get("no_tail", 0))
    cmp_val("cls", "reachable", OLD["reachable"], reach)
    board["cls"] = dict(cc)
    board["reachable"] = reach

    got = {r["id"]: norm(r["udkundoku_kakikudashi"]) for r in rows8}
    exp = {r["id"]: norm(r["expected_kakikudashi"]) for r in rows8}
    hb = {r["id"]: norm(r["hakubun"] or "") for r in rows8}
    ids4 = set(r["id"] for r in rows4)

    pr("")
    pr("== (B) 夹注残渣 2 行・B9 判定式逐位重测 ==")
    paren_rows = []
    for r in rows8:
        rid = r["id"]
        raw = r["hakubun"] or ""
        if cls[rid] == "engine" and "（" in raw:
            spans = PAREN_KANA.findall(got[rid])
            if spans:
                paren_rows.append({
                    "id": rid,
                    "cls": cls[rid],
                    "d0": lev(got[rid], exp[rid]),
                    "d1_hakubun": lev(hb[rid], exp[rid]),
                    "hakubun": r["hakubun"],
                    "hakubun_paren_pos": [i for i, c in enumerate(r["hakubun"] or "")
                                          if c == "（"],
                    "got": got[rid],
                    "got_paren_spans": spans,
                    "exp": exp[rid],
                })
    pr("  夹注残渣行：%d 行（N98/N109/N113 実測 2＝rikutou59-2・soji07-6）" % len(paren_rows))
    for p_ in paren_rows:
        pr("    %s d0=%d d1(白文)=%d" % (p_["id"], p_["d0"], p_["d1_hakubun"]))
        pr("      白文（位置 %s" % p_["hakubun_paren_pos"])
        pr("      白文 %s" % p_["hakubun"][:120])
        for sp in p_["got_paren_spans"]:
            pr("      got（…仮名…）形態 span %r" % sp)
        pr("      got  %s" % p_["got"][:120])
        pr("      exp  %s" % p_["exp"][:120])
    cmp_val("paren_residue", "count", 2, len(paren_rows))
    cmp_val("paren_residue", "ids", OLD["paren_rows"],
            sorted(p_["id"] for p_ in paren_rows))
    board["paren_residue_rows"] = paren_rows

    pr("")
    pr("== (C) sonshi09-38（no_tail・管線外の設計入力）==")
    sonshi_id = "sonshi09-38"
    gate(cls.get(sonshi_id) == "no_tail", "sonshi09-38 分类 %s != no_tail" % cls.get(sonshi_id))
    sonshi = {"cls": cls.get(sonshi_id), "tail": tail_raw.get(sonshi_id),
              "got": got.get(sonshi_id), "exp": exp.get(sonshi_id),
              "d0": lev(got.get(sonshi_id, ""), exp.get(sonshi_id, ""))}
    pr("  sonshi09-38: cls=%s tail=%r got=%r d0=%d（N98/N109/N113 記録 d0=13）"
       % (sonshi["cls"], sonshi["tail"], sonshi["got"], sonshi["d0"]))
    cmp_val("sonshi09_38", "cls", OLD["sonshi09_38"]["cls"], sonshi["cls"])
    cmp_val("sonshi09_38", "tail_empty", OLD["sonshi09_38"]["tail_empty"],
            sonshi["tail"] == "")
    cmp_val("sonshi09_38", "d0", OLD["sonshi09_38"]["d0"], sonshi["d0"])
    board["sonshi09_38"] = sonshi

    pr("")
    pr("== (D) echo 30 行・構成重测＋逐行分類（管線範囲内かの設計入力）==")
    echo_rows = []
    for r in rows8:
        if cls[r["id"]] != "echo":
            continue
        rid = r["id"]
        t = tail_raw[rid] or ""
        g, tn = got[rid], norm(t)
        kind = "direct" if g == tn else ("shinjitai" if g == norm(normalize_shinjitai(t))
                                         else "other")
        raw_hb = r["hakubun"] or ""
        echo_rows.append({
            "id": rid, "kind": kind,
            "tail": tn, "got": g, "d0": lev(g, exp[rid]),
            "hb_paren": raw_hb.count("（"),
            "hb_kana_paren": bool(PAREN_KANA.search(raw_hb)),
            "hb": raw_hb[:160],
        })
    n_direct = sum(1 for e in echo_rows if e["kind"] == "direct")
    n_shin = sum(1 for e in echo_rows if e["kind"] == "shinjitai")
    n_other = sum(1 for e in echo_rows if e["kind"] == "other")
    n_zero = sum(1 for e in echo_rows if e["d0"] == 0)
    n_with_annot = sum(1 for e in echo_rows if e["hb_kana_paren"])
    n_unrelated = sum(1 for e in echo_rows if not e["hb_kana_paren"])
    pr("  echo %d 行 | 直出 %d | 新字体化 %d | other %d | d0==0 %d 行"
       % (len(echo_rows), n_direct, n_shin, n_other, n_zero))
    pr("  逐行分類：白文含（…仮名…）注记 %d 行・与夹注无关 %d 行"
       % (n_with_annot, n_unrelated))
    for e in echo_rows:
        pr("    %s kind=%s d0=%d hb（x%d kana注=%s tail=%s"
           % (e["id"], e["kind"], e["d0"], e["hb_paren"], e["hb_kana_paren"], e["tail"][:40]))
    cmp_val("echo", "count", OLD["echo"]["count"], len(echo_rows))
    cmp_val("echo", "got_eq_tail", OLD["echo"]["got_eq_tail"], n_direct)
    cmp_val("echo", "shinjitai", OLD["echo"]["shinjitai"], n_shin)
    cmp_val("echo", "other", OLD["echo"]["other"], n_other)
    cmp_val("echo", "d0_zero", OLD["echo"]["d0_zero"], n_zero)
    board["echo"] = {"count": len(echo_rows), "direct": n_direct,
                     "shinjitai": n_shin, "other": n_other, "d0_zero": n_zero,
                     "with_annotation": n_with_annot, "unrelated": n_unrelated,
                     "rows": echo_rows}

    pr("")
    pr("== (E) census：管線影響面定量（8165・4000 双口径）==")
    # 白文含（（分類別内訳）／got 含（／got 含（…仮名…）
    hb_paren_all = [r["id"] for r in rows8 if "（" in (r["hakubun"] or "")]
    hb_paren_by_cls = collections.Counter(cls[i] for i in hb_paren_all)
    got_paren_all = [r["id"] for r in rows8 if "（" in got[r["id"]]]
    got_kana_all = [r["id"] for r in rows8 if PAREN_KANA.search(got[r["id"]])]
    hb_paren_4 = [i for i in hb_paren_all if i in ids4]
    got_kana_4 = [i for i in got_kana_all if i in ids4]
    pr("  白文含（ %d 行（分類別 %s）｜4000 内 %d 行"
       % (len(hb_paren_all), dict(hb_paren_by_cls), len(hb_paren_4)))
    pr("  got 含（ %d 行｜4000 内 %d 行" % (len(got_paren_all),
                                          len([i for i in got_paren_all if i in ids4])))
    pr("  got 含（…仮名…） %d 行（B9 残渣 %d 行＝そのうち engine 分支）｜4000 内 %d 行"
       % (len(got_kana_all), len(paren_rows),
          len(got_kana_4)))
    for i in got_kana_all:
        if cls[i] != "engine":
            pr("    got-kana 非 engine 行 %s cls=%s got %s" % (i, cls[i], got[i][:80]))
    board["census"] = {
        "hb_paren_total": len(hb_paren_all),
        "hb_paren_by_cls": dict(hb_paren_by_cls),
        "hb_paren_in4000": len(hb_paren_4),
        "got_paren_total": len(got_paren_all),
        "got_paren_in4000": len([i for i in got_paren_all if i in ids4]),
        "got_kana_total": len(got_kana_all),
        "got_kana_in4000": len(got_kana_4),
        "got_kana_ids": got_kana_all,
    }

    pr("")
    pr("== 汇总：基线 4000 %s/%d/%d・8165 %s/%d/%d・行分类 %s・reachable %d・"
       "残渣 %d 行・sonshi d0=%d・echo %d（直出 %d＋新字体化 %d・含注记 %d／无关 %d）・"
       "census 白文含（ %d/got 含（ %d/got 含（…仮名…） %d・漂移 %d 件 =="
       % (avg4, exact4, err4,
          avg8, exact8, err8, dict(cc), reach,
          len(paren_rows), sonshi["d0"], len(echo_rows), n_direct, n_shin,
          n_with_annot, n_unrelated,
          len(hb_paren_all), len(got_paren_all), len(got_kana_all), len(DRIFT)))
    board["drift"] = DRIFT
    board["lev_impl"] = _LEV_IMPL
    board["elapsed_sec"] = round(time.time() - t_start)
    board["verdict"] = "PASS" if not DRIFT else "DRIFT"
    json.dump(board, open(os.path.join(EV, "night115_recheck.json"), "w",
                          encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night115_recheck.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    pr("")
    pr("written: eval/night115_recheck.json / night115_recheck.txt")
    pr("DRIFT=%d verdict=%s" % (len(DRIFT), board["verdict"]))
    pr("elapsed %.0fs" % board["elapsed_sec"])


if __name__ == "__main__":
    main()
