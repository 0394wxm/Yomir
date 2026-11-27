# -*- coding: utf-8 -*-
"""night109_sim.py — Night 109 在庫盘点夜：(a)–(d) 在庫 sim 全重测（night107 基线・解析适用）。

任务书（Night 109・报告-only）：全部在庫 sim-first 重测、禁抄旧数。基线＝night107 归档
（4000 13.460/24/0・8165 13.466/30/0）。方法论＝N99/N104 sim 型（归档 got 上解析适用・
guard 語义 any(g in hb) エンジン同型）＋N106 guard_nxt 型（(d) follow_map 機構）。
N102 教训：拍板表の旧数は未測假设——每项在现 master（Rule T/U＋N107 guard 変更後）で
重测し、旧数との一致/漂移を drift flag で記録（盘点夜は漂移も「報告」が正・停下报数は
基线と構造 gate のみ）。

测项（在庫 4 项・(e) は tools/night109_status.py）：
  (a) 嗟や→嗟乎（guard 嗟・N94 在庫）       旧：3 発火 3 改善 0 変差 Δ−0.000367・
      同族歎詞（嗟夫/呜呼/于嗟/嗟哉）0 行・exp 嗟乎 3・got/exp 含嗟 12
  (b) per-guard 変体 こと勿く(guard 勿)/こと毋く(guard 毋)（N102 在庫）
                                            旧：4/2/0・1/1/0・combo 5/3/0 Δ−0.000367・
      構造 2 行（toushisen080-8・koshi19_01-8）不可達
  (c) 毋系 ことなき→こと毋き（guard 毋・N103 在庫）旧：4/4/0 Δ−0.000490
      ＋N103 A1 再验＝Rule U は 15 行に触れない（night101/104/107 got 逐行对照）
  (d) (c) 后继字機構 follow_map 実現値（N106）旧：better 12/worse 1（rikutou26-5）/
      same 2・Δ8165 −0.0023（−19 字）・ceiling −0.0027（−22 字）・(a) 対照 −0.0015・
      判对 15/18（判错 rongo1442-1/tonan-1/utsuryo03-7）・Δ4000 −0.005

硬断言（对不上 exit 2＝停下报数）：
  H1 词库 1531（209+291+1031）
  H2 night107 归档 8165 行・4000 行序一致
  H3 基线 avgDist 4000=13.460 / 8165=13.466・exact 24/30
  H4 行分类 engine 7916 / echo 30 / rerun 218 / no_tail 1（reachable 8134）
  H5 链完整性 night104 vs night107 got diff 恰 2 行（rikutou37-2・shiki050-4＝N107
     C1/C4）・night101 vs night104 恰 17 行（Rule U）・night101 vs night107 恰 19 行
  H6 各候补幂等 bad 0
  H7 (b) combo 適用後も 勿かれ 出現行数不変（N102 42 行・S4+M38）
  H8 echo/no_tail に各 key 出現 0（規則不可達）・reachable 全行 hb 非空
  H9 (d) A1 発火恰好 15 行（N103 記録 ID 集）・A2 対位 token 数一致（got 莫-token=
     exp 莫-token=白文 莫）・site 18・splice 後 rikutou26-5 行のことなき消滅

输出 eval/night109_sim.json + eval/night109_changed_rows.json + eval/night109_sim.txt。
用法: python -I tools/night109_sim.py
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


lines = []
DRIFT = []


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
        open(os.path.join(EV, "night109_sim.txt"), "w", encoding="utf-8",
             newline="\n").write("\n".join(lines) + "\n")
    except Exception:
        pass


def cmp_val(item, field, old, new):
    """旧数对照：一致/[DRIFT] 記録（盘点夜は漂移も報告が正）。"""
    if isinstance(old, float) or isinstance(new, float):
        ok = round(float(old), 6) == round(float(new), 6)
    else:
        ok = old == new
    if ok:
        pr("  [一致] %s.%s = %s" % (item, field, old))
    else:
        DRIFT.append({"item": item, "field": field, "old": old, "new": new})
        pr("  [DRIFT] %s.%s 旧 %s → 新 %s" % (item, field, old, new))
    return ok


EXPECTED_CLASS = {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}

# N103 記録（(a) 15 行・d0→d1・night101/104/107 逐夜 d0 不変のはず＝N103 A1 gate 再验）
N103_A = {
    "mujun-2": (11, 10), "onoreshiru-1": (18, 17), "kagakujota-1": (27, 26),
    "kanchuna-1": (82, 81), "rongo0615-1": (12, 11), "rongo0732-1": (23, 22),
    "rongo1315-1": (113, 110), "rongo1442-1": (55, 54), "p-danjoshitsu-1": (36, 35),
    "tarekako-1": (12, 11), "tonan-1": (29, 28), "warekimi-1": (35, 34),
    "roushi46-2": (34, 35), "utsuryo03-7": (63, 63), "rikutou26-5": (53, 54),
}

# N106 記録（eval/night106_guard_nxt.json 実測値・(d) 对照源）
N106_OLD = {
    "judge": {"ok": 15, "ng": 3, "three_way_ok": 12},
    "follow_map": {"能": "莫き", "己": "莫き", "我": "莫き", "知": "莫からん", "之": "莫き",
                   "由": "莫き", "吾": "莫からん", "予": "莫き", "如": "莫かる", "大": "莫し"},
    "conflicted": {"能": {"莫き": 1, "莫し": 1}, "己": {"莫き": 1, "莫くんば": 1}},
    "conflicted2": {"己知": {"莫き": 1, "莫くんば": 1}},
    "exp_forms": {"莫き": 10, "莫からん": 2, "莫くんば": 1, "莫かる": 1, "莫し": 4},
    "follow_chars": {"能": 2, "己": 2, "我": 1, "知": 1, "之": 4, "由": 2, "吾": 1,
                     "予": 2, "如": 1, "大": 2},
    "sites_pred": [
        ["mujun-2", 0, "能", "莫き", "莫き", True],
        ["onoreshiru-1", 0, "己", "莫き", "莫き", True],
        ["kagakujota-1", 0, "我", "莫き", "莫き", True],
        ["kagakujota-1", 1, "知", "莫からん", "莫からん", True],
        ["kanchuna-1", 0, "之", "莫き", "莫き", True],
        ["rongo0615-1", 0, "由", "莫き", "莫き", True],
        ["rongo0732-1", 0, "吾", "莫からん", "莫からん", True],
        ["rongo1315-1", 0, "予", "莫き", "莫き", True],
        ["rongo1315-1", 1, "之", "莫き", "莫き", True],
        ["rongo1315-1", 2, "之", "莫き", "莫き", True],
        ["rongo1442-1", 0, "己", "莫き", "莫くんば", False],
        ["p-danjoshitsu-1", 0, "如", "莫かる", "莫かる", True],
        ["tarekako-1", 0, "由", "莫き", "莫き", True],
        ["tonan-1", 0, "之", "莫き", "莫し", False],
        ["warekimi-1", 0, "予", "莫き", "莫き", True],
        ["roushi46-2", 2, "大", "莫し", "莫し", True],
        ["utsuryo03-7", 0, "能", "莫き", "莫し", False],
        ["rikutou26-5", 3, "大", "莫し", "莫し", True],
    ],
    "modes": {
        "a": {"better": ["kagakujota-1", "kanchuna-1", "mujun-2", "onoreshiru-1",
                         "p-danjoshitsu-1", "rongo0615-1", "rongo0732-1", "rongo1315-1",
                         "rongo1442-1", "tarekako-1", "tonan-1", "warekimi-1"],
              "worse": ["rikutou26-5", "roushi46-2"], "same": ["utsuryo03-7"],
              "delta8165": -0.0015, "chars": -12, "delta4000": -0.0035, "in4000": 12,
              "per_row": {"mujun-2": [11, 10], "onoreshiru-1": [18, 17],
                          "kagakujota-1": [27, 26], "kanchuna-1": [82, 81],
                          "rongo0615-1": [12, 11], "rongo0732-1": [23, 22],
                          "rongo1315-1": [113, 110], "rongo1442-1": [55, 54],
                          "p-danjoshitsu-1": [36, 35], "tarekako-1": [12, 11],
                          "tonan-1": [29, 28], "warekimi-1": [35, 34],
                          "roushi46-2": [34, 35], "utsuryo03-7": [63, 63],
                          "rikutou26-5": [53, 54]}},
        "ceiling": {"better": ["kagakujota-1", "kanchuna-1", "mujun-2", "onoreshiru-1",
                               "p-danjoshitsu-1", "rongo0615-1", "rongo0732-1",
                               "rongo1315-1", "rongo1442-1", "tarekako-1", "tonan-1",
                               "utsuryo03-7", "warekimi-1"],
                    "worse": ["rikutou26-5"], "same": ["roushi46-2"],
                    "delta8165": -0.0027, "chars": -22, "delta4000": -0.0055, "in4000": 12,
                    "per_row": {"mujun-2": [11, 10], "onoreshiru-1": [18, 17],
                                "kagakujota-1": [27, 24], "kanchuna-1": [82, 81],
                                "rongo0615-1": [12, 11], "rongo0732-1": [23, 20],
                                "rongo1315-1": [113, 110], "rongo1442-1": [55, 53],
                                "p-danjoshitsu-1": [36, 33], "tarekako-1": [12, 11],
                                "tonan-1": [29, 27], "warekimi-1": [35, 34],
                                "roushi46-2": [34, 34], "utsuryo03-7": [63, 62],
                                "rikutou26-5": [53, 54]}},
        "follow": {"better": ["kagakujota-1", "kanchuna-1", "mujun-2", "onoreshiru-1",
                              "p-danjoshitsu-1", "rongo0615-1", "rongo0732-1",
                              "rongo1315-1", "rongo1442-1", "tarekako-1", "tonan-1",
                              "warekimi-1"],
                   "worse": ["rikutou26-5"], "same": ["roushi46-2", "utsuryo03-7"],
                   "delta8165": -0.0023, "chars": -19, "delta4000": -0.005, "in4000": 12,
                   "per_row": {"mujun-2": [11, 10], "onoreshiru-1": [18, 17],
                               "kagakujota-1": [27, 24], "kanchuna-1": [82, 81],
                               "rongo0615-1": [12, 11], "rongo0732-1": [23, 20],
                               "rongo1315-1": [113, 110], "rongo1442-1": [55, 54],
                               "p-danjoshitsu-1": [36, 33], "tarekako-1": [12, 11],
                               "tonan-1": [29, 28], "warekimi-1": [35, 34],
                               "roushi46-2": [34, 34], "utsuryo03-7": [63, 63],
                               "rikutou26-5": [53, 54]}},
    },
}

# 在庫旧数（N94/N96/N98・N102 §6・N103 §3——盘点对照源・全部当「未測假设」再实测）
OLD = {
    "a_zaiya": {"changed": 3, "better": 3, "worse": 0, "chars": -3,
                "delta8165": -0.000367,
                "census": {"exp_嗟乎": 3, "exp_嗟夫": 0, "exp_呜呼": 0, "exp_于嗟": 0,
                           "exp_嗟哉": 0, "got_嗟": 12, "exp_嗟": 12}},
    "b1_motsu": {"changed": 4, "better": 2, "worse": 0},
    "b2_bou": {"changed": 1, "better": 1, "worse": 0},
    "b_combo": {"changed": 5, "better": 3, "worse": 0, "chars": -3,
                "delta8165": -0.000367,
                "fired": ["koshi19_01-8", "p-haigun-1", "rikutou04-2", "rikutou21-2",
                          "toushisen080-8"],
                "struct_no_gain": ["koshi19_01-8", "toushisen080-8"]},
    "c_boukei": {"changed": 4, "better": 4, "worse": 0, "chars": -4,
                 "delta8165": -0.00049,
                 "fired": ["daigaku06-1", "ichijicho-1", "rongo1125-1", "shindoku-1"],
                 "exp_tok": {"ichijicho-1": "毋かれ", "rongo1125-1": "毋かれ",
                             "shindoku-1": "毋き", "daigaku06-1": "毋き"}},
}

# 在庫候补（guard=白文守り字・longer=長詞マスク空壳）
CANDIDATES = {
    "a_zaiya": {"kana": "嗟や", "repl": "嗟乎", "guard": ("嗟",), "longer": (),
                "tag": "(a) N94 在庫 嗟や→嗟乎（guard 嗟）"},
    "b1_motsu": {"kana": "ことなく", "repl": "こと勿く", "guard": ("勿",), "longer": (),
                 "tag": "(b1) N102 在庫 per-guard こと勿く（guard 勿）"},
    "b2_bou": {"kana": "ことなく", "repl": "こと毋く", "guard": ("毋",), "longer": (),
               "tag": "(b2) N102 在庫 per-guard こと毋く（guard 毋）"},
    "c_boukei": {"kana": "ことなき", "repl": "こと毋き", "guard": ("毋",), "longer": (),
                 "tag": "(c) N103 在庫 毋系 ことなき→こと毋き（guard 毋）"},
}

GOT_TOKEN_RE = re.compile("こと莫かれ|こと莫く|こと莫き|こと莫し|ことなき")
EXP_TOKEN_RE = re.compile("莫からん|莫くんば|莫かる|莫かれ|莫き|莫く|莫し")
# 后继字→活用形 多数決表の tie-break 順（语料多数形 莫き 優先・N103 census 10/18）
FORM_ORDER = ["莫き", "莫し", "莫く", "莫からん", "莫くんば", "莫かる"]


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


def run(rows, kana_rules, d0_cache, hb_of):
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
        for kana, repl, guard, longer in kana_rules:
            if guard and not any(g in hb for g in guard):
                continue
            new, _ = _apply_count(new, kana, repl, longer)
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


def measure(rows8, rows4, kana_rules, d0_cache, hb_of):
    res8 = run(rows8, kana_rules, d0_cache, hb_of)
    res4 = run(rows4, kana_rules, d0_cache, hb_of)
    chg8 = {cr["id"]: cr for cr in res8["changed_rows"]}
    total_old8 = sum(d0_cache[r["id"]][2] for r in rows8)
    dsum8 = sum(cr["new_dist"] - cr["old_dist"] for cr in res8["changed_rows"])
    full_new8 = total_old8 + dsum8
    pe8 = (sum(1 for r in rows8 if r["id"] not in chg8 and d0_cache[r["id"]][2] == 0)
           + sum(1 for cr in res8["changed_rows"] if cr["new_dist"] == 0))
    pe4 = (sum(1 for r in rows4 if r["id"] not in {cr["id"] for cr in res4["changed_rows"]}
               and d0_cache[r["id"]][2] == 0)
           + sum(1 for cr in res4["changed_rows"] if cr["new_dist"] == 0))
    return {"changed": res8["changed_entries"],
            "better": res8["better"], "worse": res8["worse"], "same": res8["same"],
            "changed4000": res4["changed_entries"],
            "better4000": res4["better"], "worse4000": res4["worse"],
            "chars8165": dsum8,
            "delta8165": round(dsum8 / 8165, 3),
            "delta8165_round6": round(dsum8 / 8165, 6),
            "delta4000": res4["delta"],
            "full8165": {"avg_old": round(total_old8 / 8165, 3),
                         "avg_new": round(full_new8 / 8165, 3)},
            "pred_exact8165": pe8, "pred_exact4000": pe4,
            "worse_ids": sorted(wd["id"] for wd in res8["worse_detail"]),
            "worse_ids4000": sorted(wd["id"] for wd in res4["worse_detail"]),
            "fired": sorted(chg8),
            "changed_rows": res8["changed_rows"]}


def splice(text, spans):
    """spans = [(start, end, repl)] を後方から置換。"""
    out = text
    for s0, s1, repl in sorted(spans, key=lambda x: -x[0]):
        out = out[:s0] + repl + out[s1:]
    return out


sim = {}


def main():
    global sim
    t_start = time.time()
    sim = {"script": "tools/night109_sim.py", "night": 109,
           "mode": "在庫盘点夜 (a)–(d) sim 全重测（night107 基线・报告-only・不収録）",
           "verdict": None}
    sim["lev_impl"] = _LEV_IMPL

    pr("== H1 词库 import 实证（不動確認）==")
    import backend.glossary_lexicon as gl
    import backend.glossary_lexicon_extra as gle
    import backend.glossary_lexicon_extra2 as gle2
    lex = {"core": len(gl.GLOSSARY_LEXICON), "core_old_size": getattr(gl, "_OLD_SIZE", None),
           "extra": len(gle.as_dicts()), "extra2": len(gle2.LEXICON_EXTRA2),
           "ordered_all": len(gle2._ORDERED_ALL)}
    pr("  %s → 209+291+1031=%s" % (lex, lex["ordered_all"]))
    sim["lexicon"] = lex
    gate(lex["core_old_size"] == 209 and lex["core"] == 500 and lex["extra"] == 291
         and lex["extra2"] == 1031 and lex["ordered_all"] == 1531,
         "词库実測 %s != 209+291+1031=1531" % lex)

    # ---------- 基准（night107 归档） ----------
    doc8 = json.load(open(os.path.join(EV, "night107_results_8165.json"), encoding="utf-8"))
    rows8 = [r for r in doc8["results"] if r.get("udkundoku_kakikudashi") is not None]
    gate(len(rows8) == 8165, "night107_results_8165 行数 %d != 8165" % len(rows8))
    doc4 = json.load(open(os.path.join(EV, "night107_results_4000.json"), encoding="utf-8"))
    rows4 = doc4["results"]
    gate([r["id"] for r in rows4] == [r["id"] for r in rows8[:4000]],
         "night107_results_4000 与 8165 前 4000 行序不一致")
    sim["baseline_archive"] = ("night107_results_8165.json / night107_results_4000.json"
                               "（N107 链尾＝Rule U＋C1/C4 生效済み）")

    # ---------- H5 链完整性（night101/104/107 got 逐行对照） ----------
    got107 = {r["id"]: norm(r["udkundoku_kakikudashi"]) for r in rows8}
    rows101 = [r for r in json.load(open(os.path.join(EV, "night101_results_8165.json"),
                                         encoding="utf-8"))["results"]
               if r.get("udkundoku_kakikudashi") is not None]
    rows104 = [r for r in json.load(open(os.path.join(EV, "night104_results_8165.json"),
                                         encoding="utf-8"))["results"]
               if r.get("udkundoku_kakikudashi") is not None]
    gate(len(rows101) == 8165 and len(rows104) == 8165,
         "night101/104 归档行数 != 8165")
    got101 = {r["id"]: norm(r["udkundoku_kakikudashi"]) for r in rows101}
    got104 = {r["id"]: norm(r["udkundoku_kakikudashi"]) for r in rows104}
    gate(set(got101) == set(got107) == set(got104), "三归档 ID 集不一致")
    d_u = sorted(rid for rid in got107 if got101[rid] != got104[rid])
    d_c = sorted(rid for rid in got107 if got104[rid] != got107[rid])
    d_all = sorted(rid for rid in got107 if got101[rid] != got107[rid])
    pr("== H5 链完整性：night101→104 diff %d 行（Rule U）・104→107 diff %d 行（C1/C4）・"
       "101→107 diff %d 行 ==" % (len(d_u), len(d_c), len(d_all)))
    sim["chain"] = {"n101_to_104_ruleu": d_u, "n104_to_107_c1c4": d_c,
                    "n101_to_107": d_all}
    gate(len(d_u) == 17, "night101 vs night104 diff %d 行 != 17（Rule U 改写 17 行前提）"
         % len(d_u))
    gate(d_c == ["rikutou37-2", "shiki050-4"],
         "night104 vs night107 diff %s != [rikutou37-2, shiki050-4]（N107 C1/C4 恰 2 行）"
         % d_c)
    gate(sorted(set(d_u) | set(d_c)) == d_all and len(d_all) == 19,
         "night101 vs night107 diff %d 行 != 17+2=19（Rule U 与 C1/C4 非重叠前提）"
         % len(d_all))
    pr("  H5 PASS：C1/C4 恰 2 行（rikutou37-2・shiki050-4）・Rule U 恰 17 行・合计 19 行")

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

    # ---------- H4 行分类＋guard 上下文（night98_audit 同款） ----------
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
    pr("== H4 行分类 %s（期待 %s）==" % (dict(cc), EXPECTED_CLASS))
    sim["class"] = dict(cc)
    gate(dict(cc) == EXPECTED_CLASS, "行分类実数 %s != 期待 %s" % (dict(cc), EXPECTED_CLASS))
    reachable = [r for r in rows8 if cls[r["id"]] in ("engine", "rerun")]
    pr("  reachable %d 行" % len(reachable))

    # ---------- H8 echo/no_tail 規則不可達＋hb 非空 ----------
    all_keys = [c["kana"] for c in CANDIDATES.values()]
    unreach_hits = {}
    for k in all_keys:
        unreach_hits[k] = [r["id"] for r in rows8 if cls[r["id"]] in ("echo", "no_tail")
                           and k in got107[r["id"]]]
    for k, ids in unreach_hits.items():
        gate(not ids, "H8 echo/no_tail 行に key %s 出現（規則可達化で sim/実跑乖離）: %s"
             % (k, ids[:8]))
    empty_hb = [r["id"] for r in reachable if not hb_of[r["id"]]]
    gate(not empty_hb, "H8 engine/rerun に hb 空行（guard 語义乖離）: %s" % empty_hb[:8])
    pr("== H8 echo/no_tail 全 key 不可達（0 行）＋reachable 全行 hb 非空 ✓ ==")

    d0_cache = {}
    for r in rows8:
        got = got107[r["id"]]
        exp = norm(r["expected_kakikudashi"])
        d0_cache[r["id"]] = (got, exp, lev(got, exp))
    base_avg8 = round(sum(v[2] for v in d0_cache.values()) / 8165, 3)
    base_avg4 = round(sum(d0_cache[r["id"]][2] for r in rows4) / 4000, 3)
    exact_base8 = sum(1 for v in d0_cache.values() if v[2] == 0)
    exact_base4 = sum(1 for r in rows4 if d0_cache[r["id"]][2] == 0)
    pr("  基线 avgDist 4000=%.3f 8165=%.3f（归档 13.460/13.466）exact %d/%d（归档 24/30）"
       % (base_avg4, base_avg8, exact_base4, exact_base8))
    sim["baseline"] = {"avg4000": base_avg4, "avg8165": base_avg8,
                       "exact4000": exact_base4, "exact8165": exact_base8}
    gate(close(base_avg4, 13.460), "基线 avgDist 4000 %.3f != 13.460" % base_avg4)
    gate(close(base_avg8, 13.466), "基线 avgDist 8165 %.3f != 13.466" % base_avg8)
    gate(exact_base4 == 24 and exact_base8 == 30,
         "基线 exact %d/%d != 24/30" % (exact_base4, exact_base8))

    # ---------- 候补 guard_forms 断言 ----------
    for gch in ("嗟", "勿", "毋"):
        gf = guard_forms((gch,))
        pr("  guard_forms(%s)=%s" % (gch, gf))
        gate(gf == [gch], "guard_forms(%s) %s != ['%s']（双形并查前提）" % (gch, gf, gch))
        gate(new_to_old.get(gch) is None and old_to_new.get(gch) is None,
             "%s が SHINJITAI_MAP に存在（guard_forms 前提崩れ）" % gch)
    for k, c in CANDIDATES.items():
        gate(normalize_shinjitai(c["repl"]) == c["repl"], "repl 非终字形: %s" % k)
        gate(c["kana"] not in c["repl"], "構造冪等：repl に key 含有: %s" % k)

    def rules_of(keys):
        return [(CANDIDATES[k]["kana"], CANDIDATES[k]["repl"],
                 tuple(guard_forms(CANDIDATES[k]["guard"])), CANDIDATES[k]["longer"])
                for k in keys]

    pr("")
    pr("== (a) 嗟や→嗟乎（guard 嗟・N94 在庫）単条測定 ==")
    m_a = measure(rows8, rows4, rules_of(["a_zaiya"]), d0_cache, hb_of)
    pr("  改写 %d(4000内 %d) better %d/%d worse %d/%d same %d | Δ8165 %.6f（%d 字）"
       "Δ4000 %.3f | 幂等 bad %d"
       % (m_a["changed"], m_a["changed4000"], m_a["better"], m_a["better4000"],
          m_a["worse"], m_a["worse4000"], m_a["same"], m_a["delta8165_round6"],
          m_a["chars8165"], m_a["delta4000"], idempotent(reachable, rules_of(["a_zaiya"]),
                                                         d0_cache, hb_of)))
    pr("  fired %s" % m_a["fired"])
    for cr in m_a["changed_rows"]:
        pr("    %s %d→%d | got %s" % (cr["id"], cr["old_dist"], cr["new_dist"],
                                      cr["old_text"][:60]))
    # 同族歎詞 census（N98 記録＝旧数对照）
    census = {"exp_嗟乎": sum(1 for r in rows8 if "嗟乎" in norm(r["expected_kakikudashi"])),
              "exp_嗟夫": sum(1 for r in rows8 if "嗟夫" in norm(r["expected_kakikudashi"])),
              "exp_呜呼": sum(1 for r in rows8 if "呜呼" in norm(r["expected_kakikudashi"])),
              "exp_于嗟": sum(1 for r in rows8 if "于嗟" in norm(r["expected_kakikudashi"])),
              "exp_嗟哉": sum(1 for r in rows8 if "嗟哉" in norm(r["expected_kakikudashi"])),
              "got_嗟": sum(1 for r in rows8 if "嗟" in got107[r["id"]]),
              "exp_嗟": sum(1 for r in rows8 if "嗟" in norm(r["expected_kakikudashi"]))}
    census_ext = {"exp_嗚呼": sum(1 for r in rows8 if "嗚呼" in norm(r["expected_kakikudashi"])),
                  "exp_於嗟": sum(1 for r in rows8 if "於嗟" in norm(r["expected_kakikudashi"]))}
    pr("  census %s（拡張参照 嗚呼/於嗟 %s）" % (census, census_ext))
    pr("  -- 旧数对照（N94/N96/N98 記録）--")
    o = OLD["a_zaiya"]
    cmp_val("a_zaiya", "changed", o["changed"], m_a["changed"])
    cmp_val("a_zaiya", "better", o["better"], m_a["better"])
    cmp_val("a_zaiya", "worse", o["worse"], m_a["worse"])
    cmp_val("a_zaiya", "chars8165", o["chars"], m_a["chars8165"])
    cmp_val("a_zaiya", "delta8165", o["delta8165"], m_a["delta8165_round6"])
    for ck, cv in o["census"].items():
        cmp_val("a_zaiya.census", ck, cv, census[ck])
    sim["a_zaiya"] = {k: v for k, v in m_a.items() if k != "changed_rows"}
    sim["a_zaiya"]["census"] = census
    sim["a_zaiya"]["census_ext"] = census_ext

    pr("")
    pr("== (b) per-guard 変体 こと勿く/こと毋く（N102 在庫）＋combo 測定 ==")
    m_b1 = measure(rows8, rows4, rules_of(["b1_motsu"]), d0_cache, hb_of)
    m_b2 = measure(rows8, rows4, rules_of(["b2_bou"]), d0_cache, hb_of)
    m_bc = measure(rows8, rows4, rules_of(["b1_motsu", "b2_bou"]), d0_cache, hb_of)
    bad_b1 = idempotent(reachable, rules_of(["b1_motsu"]), d0_cache, hb_of)
    bad_b2 = idempotent(reachable, rules_of(["b2_bou"]), d0_cache, hb_of)
    bad_bc = idempotent(reachable, rules_of(["b1_motsu", "b2_bou"]), d0_cache, hb_of)
    gate(bad_b1 == 0 and bad_b2 == 0 and bad_bc == 0,
         "H6 (b) 幂等 bad %d/%d/%d != 0" % (bad_b1, bad_b2, bad_bc))
    pr("  b1 こと勿く(guard 勿): 改写 %d better %d worse %d | fired %s"
       % (m_b1["changed"], m_b1["better"], m_b1["worse"], m_b1["fired"]))
    pr("  b2 こと毋く(guard 毋): 改写 %d better %d worse %d | fired %s"
       % (m_b2["changed"], m_b2["better"], m_b2["worse"], m_b2["fired"]))
    pr("  combo: 改写 %d(4000内 %d) better %d/%d worse %d/%d | Δ8165 %.6f（%d 字）"
       "Δ4000 %.3f | 幂等 bad %d"
       % (m_bc["changed"], m_bc["changed4000"], m_bc["better"], m_bc["better4000"],
          m_bc["worse"], m_bc["worse4000"], m_bc["delta8165_round6"], m_bc["chars8165"],
          m_bc["delta4000"], bad_bc))
    pr("  combo fired %s" % m_bc["fired"])
    for cr in m_bc["changed_rows"]:
        pr("    %s %d→%d | got %s" % (cr["id"], cr["old_dist"], cr["new_dist"],
                                      cr["old_text"][:60]))
    # H7 勿かれ 出現行数不変（N102 42 行＝S4+M38）
    def yukare_rows(texts):
        return sum(1 for t in texts if "勿かれ" in t)
    before_yk = yukare_rows(got107[r["id"]] for r in rows8)
    combo_texts = {cr["id"]: cr["new_text"] for cr in m_bc["changed_rows"]}
    after_yk = yukare_rows(combo_texts.get(r["id"], got107[r["id"]]) for r in rows8)
    pr("  H7 勿かれ 出現行数 before=%d after=%d（N102 記録 42）" % (before_yk, after_yk))
    gate(before_yk == after_yk, "H7 勿かれ 出現行数不変壊れ %d→%d" % (before_yk, after_yk))
    cmp_val("b_combo", "yukare_rows", 42, before_yk)
    pr("  -- 旧数对照（N102 §6 記録）--")
    cmp_val("b1_motsu", "changed", OLD["b1_motsu"]["changed"], m_b1["changed"])
    cmp_val("b1_motsu", "better", OLD["b1_motsu"]["better"], m_b1["better"])
    cmp_val("b1_motsu", "worse", OLD["b1_motsu"]["worse"], m_b1["worse"])
    cmp_val("b2_bou", "changed", OLD["b2_bou"]["changed"], m_b2["changed"])
    cmp_val("b2_bou", "better", OLD["b2_bou"]["better"], m_b2["better"])
    cmp_val("b2_bou", "worse", OLD["b2_bou"]["worse"], m_b2["worse"])
    cmp_val("b_combo", "changed", OLD["b_combo"]["changed"], m_bc["changed"])
    cmp_val("b_combo", "better", OLD["b_combo"]["better"], m_bc["better"])
    cmp_val("b_combo", "worse", OLD["b_combo"]["worse"], m_bc["worse"])
    cmp_val("b_combo", "fired", OLD["b_combo"]["fired"], m_bc["fired"])
    cmp_val("b_combo", "chars8165", OLD["b_combo"]["chars"], m_bc["chars8165"])
    cmp_val("b_combo", "delta8165", OLD["b_combo"]["delta8165"], m_bc["delta8165_round6"])
    # 構造行（combo 発火内 d0==d1）実測＋N102 §5 行 94 の行名对照
    chg_bc = {cr["id"]: cr for cr in m_bc["changed_rows"]}
    struct_measured = sorted(rid for rid, cr in chg_bc.items()
                             if cr["new_dist"] == cr["old_dist"])
    pr("  構造行（combo 発火内 d0==d1）実測 %s" % struct_measured)
    pr("  N102 §5 行 94 記録「残り 2 行」=%s" % OLD["b_combo"]["struct_no_gain"])
    cmp_val("b_combo.struct_no_gain", "d0==d1 行（N102 記録 vs 実測）",
            OLD["b_combo"]["struct_no_gain"], struct_measured)
    # 5 行 got 三归档同一＝N102 per-guard sim と同一入力（行名偏差は記録偏差と断定できる根拠）
    for rid in sorted(chg_bc):
        gate(got101[rid] == got104[rid] == got107[rid],
             "(b) %s got が night101/104/107 間で変化（N102 基线と非同一）" % rid)
    pr("  combo 5 行 got は night101/104/107 で逐字节同一（N102 sim と同一入力）✓")
    struct_note = ("N102 §5 行 94「残り 2 行（toushisen080-8・koshi19_01-8）」は行名复制错位"
                   "の記録偏差（§4 死因表 72-73 行からの転記・N84 8 行/N96 rousxi46-2 先例）"
                   "——実測＝rikutou21-2・koshi19_01-8（rikutou21-2 は長文 scramble 対位遠方"
                   "＝§4 75 行・koshi19_01-8 は 勿からん 推量禁止形＝§4 73 行の死因どおり）。"
                   "toushisen080-8 は こと勿く で 勿 が exp 勿れ と align し 12→11 改善"
                   "（在庫总量 4/2/0・1/1/0・5/3/0・Δ−0.000367・勿かれ 42・幂等 0 は全部一致）。"
                   "combo 5 行の got は night101/104/107 逐字节同一＝N102 per-guard sim と"
                   "同一入力で aggregate が再現する＝总量一致・行名のみ偏差。")
    sim["b_per_guard"] = {"b1": {k: v for k, v in m_b1.items() if k != "changed_rows"},
                          "b2": {k: v for k, v in m_b2.items() if k != "changed_rows"},
                          "combo": {k: v for k, v in m_bc.items() if k != "changed_rows"},
                          "yukare_rows_before": before_yk, "yukare_rows_after": after_yk,
                          "struct_no_gain_measured": struct_measured,
                          "struct_no_gain_note": struct_note}

    pr("")
    pr("== (c) 毋系 ことなき→こと毋き（guard 毋・N103 在庫）単条測定 ==")
    m_c = measure(rows8, rows4, rules_of(["c_boukei"]), d0_cache, hb_of)
    bad_c = idempotent(reachable, rules_of(["c_boukei"]), d0_cache, hb_of)
    gate(bad_c == 0, "H6 (c) 幂等 bad %d != 0" % bad_c)
    pr("  改写 %d(4000内 %d) better %d/%d worse %d/%d same %d | Δ8165 %.6f（%d 字）"
       "Δ4000 %.3f | 幂等 bad %d"
       % (m_c["changed"], m_c["changed4000"], m_c["better"], m_c["better4000"],
          m_c["worse"], m_c["worse4000"], m_c["same"], m_c["delta8165_round6"],
          m_c["chars8165"], m_c["delta4000"], bad_c))
    pr("  fired %s" % m_c["fired"])
    for cr in m_c["changed_rows"]:
        pr("    %s %d→%d | got %s" % (cr["id"], cr["old_dist"], cr["new_dist"],
                                      cr["old_text"][:60]))
    pr("  -- 旧数对照（N103 §3 記録 4/4/0 Δ−0.000490）--")
    cmp_val("c_boukei", "changed", OLD["c_boukei"]["changed"], m_c["changed"])
    cmp_val("c_boukei", "better", OLD["c_boukei"]["better"], m_c["better"])
    cmp_val("c_boukei", "worse", OLD["c_boukei"]["worse"], m_c["worse"])
    cmp_val("c_boukei", "fired", OLD["c_boukei"]["fired"], m_c["fired"])
    cmp_val("c_boukei", "chars8165", OLD["c_boukei"]["chars"], m_c["chars8165"])
    cmp_val("c_boukei", "delta8165", OLD["c_boukei"]["delta8165"], m_c["delta8165_round6"])
    exp_tok_c = {cr["id"]: "毋かれ" if "毋かれ" in cr["expected"] else
                 ("毋き" if "毋き" in cr["expected"] else "?") for cr in m_c["changed_rows"]}
    cmp_val("c_boukei", "exp_tok", OLD["c_boukei"]["exp_tok"], exp_tok_c)
    sim["c_boukei"] = {k: v for k, v in m_c.items() if k != "changed_rows"}

    pr("")
    pr("== (c) 付帯：N103 A1 再验＝Rule U は 15 行に触れない（night101/104/107 逐行）==")
    untouched = {}
    for rid, (dd0, _dd1) in N103_A.items():
        same101_104 = got101[rid] == got104[rid]
        same101_107 = got101[rid] == got107[rid]
        untouched[rid] = {"got_101_104_same": same101_104, "got_101_107_same": same101_107,
                          "d0_107": d0_cache[rid][2], "d0_n103": dd0,
                          "d0_same": d0_cache[rid][2] == dd0}
        if not (same101_104 and same101_107 and d0_cache[rid][2] == dd0):
            DRIFT.append({"item": "c_ruleu_15rows", "field": rid, "old": dd0,
                          "new": d0_cache[rid][2]})
            pr("  [DRIFT] %s 101==104:%s 101==107:%s d0 %d vs N103 %d"
               % (rid, same101_104, same101_107, d0_cache[rid][2], dd0))
        else:
            pr("  [一致] %s got 三归档同一・d0=%d" % (rid, dd0))
    n_touch = sum(1 for v in untouched.values()
                  if not (v["got_101_104_same"] and v["got_101_107_same"] and v["d0_same"]))
    pr("  → 15 行中 Rule U/C1/C4 触れ %d 行（N103 A1 前提＝0）" % n_touch)
    sim["c_ruleu_15rows"] = {"untouched": untouched, "touched": n_touch}
    # 項 6 関連 census（N96/N98 記録 72 行＝night101 pre-U 口径・Rule U 後は自然増）
    got_mokare_101 = sum(1 for rid in got101 if "莫かれ" in got101[rid])
    got_mokare_107 = sum(1 for rid in got107 if "莫かれ" in got107[rid])
    cmp_val("census", "got 含莫かれ 行数（night101 pre-U・N96/N98 記録）", 72,
            got_mokare_101)
    u_rows_with = sum(1 for rid in d_u if "莫かれ" in got107[rid])
    u_rows_before = sum(1 for rid in d_u if "莫かれ" in got101[rid])
    pr("  night107（Rule U 後）=%d 行＝pre-U %d＋Rule U 17 行中既在 %d/新規 %d"
       % (got_mokare_107, got_mokare_101, u_rows_before, u_rows_with - u_rows_before))
    gate(got_mokare_107 == got_mokare_101 + (u_rows_with - u_rows_before),
         "莫かれ census 増分が Rule U で説明できない")
    sim["census_mokare"] = {"n101_pre_u": got_mokare_101, "n107": got_mokare_107,
                            "ruleu_overlap": u_rows_before,
                            "ruleu_new": u_rows_with - u_rows_before,
                            "note": "N96/N98 記録 72＝pre-U 口径。Rule U（N104）発火 17 行の"
                                    "うち新規 %d 行が 莫かれ を got に加え %d＝自然増。"
                                    "在庫候補との無関係は A1 gate（15 行 0 触れ）と (b) combo"
                                    " 5 行三归档同一 gate で実証済み"
                                    % (u_rows_with - u_rows_before, got_mokare_107)}

    # ---------- (d) follow_map 機構（N106 guard_nxt 型クローン・night107 基线） ----------
    pr("")
    pr("== (d) (c) 后继字機構 follow_map 実現値（N106 型・night107 基线）==")
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
    gate(len(chg_a) == 15, "H9 A1 発火 %d != 15" % len(chg_a))
    gate(set(by_id) == set(N103_A), "H9 A1 発火行集合 != N103 記録 15 行")
    for rid, (dd0, dd1) in N103_A.items():
        gate(rid in by_id and by_id[rid]["d0"] == dd0,
             "H9 A1 %s d0 実測 %s != 記録 %d（night107 基线 d0 不変前提）"
             % (rid, by_id[rid]["d0"] if rid in by_id else None, dd0))
    b_a = [c for c in chg_a if c["d1"] < c["d0"]]
    w_a = [c for c in chg_a if c["d1"] > c["d0"]]
    s_a = [c for c in chg_a if c["d1"] == c["d0"]]
    pr("  (a) 対照：発火 %d 行 | better %d / worse %d / same %d"
       % (len(chg_a), len(b_a), len(w_a), len(s_a)))
    site_rows = []
    for c in chg_a:
        rid = c["id"]
        hb_full = hb_of[rid]
        gt = list(GOT_TOKEN_RE.finditer(c["got"]))
        et = list(EXP_TOKEN_RE.finditer(d0_cache[rid][1]))
        gate(len(gt) == len(et), "H9 A2 %s token 数不一致 got %d vs exp %d"
             % (rid, len(gt), len(et)))
        n_mo_hb = hb_full.count("莫")
        gate(n_mo_hb == len(gt), "H9 A2 %s 白文 莫 %d != got token %d（対位不能）"
             % (rid, n_mo_hb, len(gt)))
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
        site_rows.append({"id": rid, "cls": c["cls"], "got": c["got"],
                          "exp": d0_cache[rid][1], "hb": hb_full,
                          "n_tokens": len(gt), "sites": sites})
    all_sites = []
    for sr in site_rows:
        for s in sr["sites"]:
            s["row_id"] = sr["id"]
            all_sites.append(s)
    gate(len(all_sites) == 18, "H9 site 总数 %d != 18（N103 census）" % len(all_sites))
    form_c = collections.Counter(s["exp_tok"] for s in all_sites)
    follow_c = collections.Counter(s["follow"] for s in all_sites)
    pr("  site 字形分布：%s" % dict(form_c))
    pr("  后继字分布（1 字）：%s" % dict(follow_c))
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
            pick = min(winners, key=lambda f: FORM_ORDER.index(f) if f in FORM_ORDER else 99)
            follow_map[fc] = pick
            conflicted[fc] = dict(cc2)
    table2 = collections.defaultdict(collections.Counter)
    for s in all_sites:
        table2[s["follow2"]][s["exp_tok"]] += 1
    conf2 = {fc: dict(cc2) for fc, cc2 in table2.items() if len(cc2) > 1}
    pr("  follow_map: %s" % follow_map)
    pr("  conflicted: %s | 2 字衝突: %s" % (conflicted, conf2))
    n_ok = n_ng = 0
    for s in all_sites:
        pred = follow_map[s["follow"]]
        s["pred"] = pred
        s["ok"] = (pred == s["exp_tok"])
        n_ok += s["ok"]
        n_ng += (not s["ok"])
    three_way_ok = sum(1 for s in all_sites
                       if s["ok"] and s["exp_tok"] in ("莫き", "莫し", "莫く"))
    pr("  判对 %d / 判错 %d（%d/18）｜三向内判对 %d" % (n_ok, n_ng, n_ok, three_way_ok))

    rows4_ids = {r["id"] for r in rows4}

    def run_mode(mode):
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
                gt = list(GOT_TOKEN_RE.finditer(got0))
                gm = gt[s["site_index"]]
                gate(gm.group() == "ことなき",
                     "H9 %s site#%d token != ことなき" % (rid, s["site_index"]))
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
        return {"better": b, "worse": w, "same": s_,
                "delta8165": round(dsum8 / 8165, 4), "chars": dsum8,
                "delta4000": round(dsum4 / 4000, 4), "in4000": in4,
                "per_row": {rid: [v["d0"], v["d1"]] for rid, v in rows_res.items()},
                "texts": {rid: v["new"] for rid, v in rows_res.items()}}

    res_a = run_mode("a")
    res_ceiling = run_mode("ceiling")
    res_follow = run_mode("follow")
    for mode, res in (("a", res_a), ("ceiling", res_ceiling), ("follow", res_follow)):
        pr("  [%s] better %d / worse %d / same %d | Δ8165 %.4f（%d 字）Δ4000 %.4f"
           "（4000 内 %d 行）"
           % (mode, len(res["better"]), len(res["worse"]), len(res["same"]),
              res["delta8165"], res["chars"], res["delta4000"], res["in4000"]))
    pr("  [follow] per_row %s" % json.dumps(res_follow["per_row"], ensure_ascii=False))
    rid = "rikutou26-5"
    s_ok = [s for s in all_sites if s["row_id"] == rid]
    pr("  rikutou26-5（N103 語順構造差行）: pred %s / 実 %s / %s → d %d→%d（語順差 d 変差は"
       "機構でも不救＝N106 結論）"
       % (s_ok[0]["pred"], s_ok[0]["exp_tok"], "判对" if s_ok[0]["ok"] else "判错",
          res_follow["per_row"][rid][0], res_follow["per_row"][rid][1]))
    sim["d_follow"] = {
        "a_fired": len(chg_a), "judge": {"ok": n_ok, "ng": n_ng, "three_way_ok": three_way_ok},
        "follow_map": follow_map, "conflicted": conflicted, "conflicted2": conf2,
        "exp_forms": dict(form_c), "follow_chars": dict(follow_c),
        "sites_pred": [[s["row_id"], s["site_index"], s["follow"], s["pred"],
                        s["exp_tok"], bool(s["ok"])] for s in all_sites],
        "modes": {m: {k: v for k, v in res.items() if k != "texts"}
                  for m, res in (("a", res_a), ("ceiling", res_ceiling),
                                 ("follow", res_follow))},
        "rikutou26_5": {"pred_ok": bool(s_ok[0]["ok"]),
                        "d_follow": res_follow["per_row"][rid]},
    }
    pr("  -- 旧数对照（N106 eval/night106_guard_nxt.json 記録）--")
    cmp_val("d_follow.judge", "ok/ng", [N106_OLD["judge"]["ok"], N106_OLD["judge"]["ng"]],
            [n_ok, n_ng])
    cmp_val("d_follow.judge", "three_way_ok", N106_OLD["judge"]["three_way_ok"],
            three_way_ok)
    cmp_val("d_follow", "follow_map", N106_OLD["follow_map"], follow_map)
    cmp_val("d_follow", "conflicted", N106_OLD["conflicted"], conflicted)
    cmp_val("d_follow", "conflicted2", N106_OLD["conflicted2"], conf2)
    cmp_val("d_follow", "exp_forms", N106_OLD["exp_forms"], dict(form_c))
    cmp_val("d_follow", "follow_chars", N106_OLD["follow_chars"], dict(follow_c))
    cmp_val("d_follow", "sites_pred", N106_OLD["sites_pred"],
            sim["d_follow"]["sites_pred"])
    for mode in ("a", "ceiling", "follow"):
        o = N106_OLD["modes"][mode]
        n = sim["d_follow"]["modes"][mode]
        cmp_val("d_follow.%s" % mode, "better", o["better"], n["better"])
        cmp_val("d_follow.%s" % mode, "worse", o["worse"], n["worse"])
        cmp_val("d_follow.%s" % mode, "same", o["same"], n["same"])
        cmp_val("d_follow.%s" % mode, "chars", o["chars"], n["chars"])
        cmp_val("d_follow.%s" % mode, "delta8165", o["delta8165"], n["delta8165"])
        cmp_val("d_follow.%s" % mode, "delta4000", o["delta4000"], n["delta4000"])
        cmp_val("d_follow.%s" % mode, "per_row", o["per_row"], n["per_row"])

    # ---------- 汇总 ----------
    pr("")
    items = [("a_zaiya", "(a) 嗟や→嗟乎"), ("b_per_guard", "(b) こと勿く/毋く per-guard"),
             ("c_boukei", "(c) 毋系 こと毋き"), ("d_follow", "(d) follow_map 機構")]
    drift_items = sorted({d["item"].split(".")[0] for d in DRIFT})
    pr("== 盘点汇总：(a)–(d) 全重测完了・漂移 %d 件 %s ==" % (len(DRIFT),
       drift_items if drift_items else "（一致）"))
    sim["drift"] = DRIFT
    sim["verdict"] = "PASS" if not [d for d in DRIFT
                                    if d["item"] != "census.got 含莫かれ 行数"] else "PASS_WITH_DRIFT"

    # ---------- 输出 ----------
    changed_out = {
        "a_zaiya": m_a["changed_rows"],
        "b1_motsu": m_b1["changed_rows"],
        "b2_bou": m_b2["changed_rows"],
        "b_combo": m_bc["changed_rows"],
        "c_boukei": m_c["changed_rows"],
        "d_follow_follow": [{"id": rid, "old_dist": res_follow["per_row"][rid][0],
                             "new_dist": res_follow["per_row"][rid][1],
                             "new_text": res_follow["texts"][rid]}
                            for rid in sorted(res_follow["texts"])],
    }
    json.dump(changed_out, open(os.path.join(EV, "night109_changed_rows.json"), "w",
                                encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    sim["elapsed_sec"] = round(time.time() - t_start)
    json.dump(sim, open(os.path.join(EV, "night109_sim.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night109_sim.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    pr("")
    pr("written: eval/night109_sim.json / night109_changed_rows.json / night109_sim.txt")
    pr("DRIFT=%d items=%s" % (len(DRIFT), drift_items if drift_items else "none"))
    pr("elapsed %.0fs" % sim["elapsed_sec"])


if __name__ == "__main__":
    main()
