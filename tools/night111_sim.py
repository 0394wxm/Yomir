# -*- coding: utf-8 -*-
"""night111_sim.py — Night 111:守り字后继字機構（follow_map）実施夜・sim 先行(N73 方法論)。

任務書(用户拍板 2026-11-28 11:50 点选"(d) follow_map 実施夜"):N106 §1/§2.3 機構設計
＋N109 §2(d) 逐位再验済みの守り字后继字機構を実装する。機構＝rule entry を
(kana, guard, follow_map, default_repl) 4 元組に拡張し、白文 guard 字直後 1 字
(後继字)で repl 変体を選ぶ。containment guard は第一 gate のまま・対位失敗/表外
後继字は default_repl(=単一 repl こと莫き=(a) 動作)fallback=発火不増の構造保証。

本夜唯一 entry:ことなき(guard 莫)・follow_map 10 字(N106 §2.3 多数決+语料多数形
tie-break 莫き優先)・default_repl=こと莫き。拍板:変差行 rikutou26-5(53→54,
N106/N109 既知の機構内残存変差=語順構造差)を許容、0-worsening 门はこの 1 行のみ
讓歩(N99/N104 同框)。その他の変差新增は 0。

sim 口径(任務書硬断言の通り・(a)→follow):
  d0 = default_repl のみ適用(=ことなき→こと莫き 単一 repl=(a) 動作)の got と exp の距離
  d1 = follow_map 機構適用後の got と exp の距離
  改善/変差 = d1 vs d0。Δ8165=−0.001(−7 字)・Δ4000=−0.002(−6 字)。
  改写文本 5 行 = follow 適用後 got が (a) 適用後 got と異なる行(大→莫し 2・
  知/吾→莫からん 2・如→莫かる 1)。
並行出力(参考・golden 予想根拠):raw(night107 归档 got=ことなき 残量)→follow の
総効果=N106 follow 記録 −19 字(8165)の再确认。

対位方式(N106 原型実測同款・tools/night106_guard_nxt.py):
  got 中 莫-token(こと莫かれ|こと莫く|こと莫き|こと莫し|ことなき)出現列 ×
  hb 中 莫 出現列を順序 1:1 対位(rikutou26-5 は token#3↔莫#4 で対位=実測済み)。
  個数不一致→default_repl 全置換(fail-safe・N106 §1.2 手順 2)。
実装との逐位一致は tests/test_night111_followmap.py と night111_eval_*(実跑後)で
確認する。基线=night107_results_8165/4000.json(13.466/13.460・exact 30/24)。

硬断言(对不上 exit 2=停下报数):
  S1 行分类 7916/30/218/1・S2 词库 1531・S3 基线 13.460/13.466・24/30
  A1 発火恰好 15 行(N103 記録 ID 集)・A2 対位全 15 行成立(fail-safe 発火 0)
  A3 site 18 個・後继字分布 N106 記録通り・表外後继字 0
  A4 (a) per-row=N106 記録 15 行逐位・A5 follow per-row=N106 記録 15 行逐位
  A6 改写文本恰好 5 行(ID・変体固定)
  A7 d 改善恰好 4 行(kagakujota-1 26→24・p-danjoshitsu-1 35→33・rongo0732-1 22→20・
     roushi46-2 35→34)・d 変差新增 0 行・rikutou26-5 54→54 維持(拍板行)
  A8 Δ8165 −7 字(round −0.001)・Δ4000 −6 字(round −0.002)
  A9 raw→follow 総効果 −19 字(8165)・4000 内 −20 字(N106 follow 記録一致)
  A10 冪等 bad 0
出力 eval/night111_sim.json ＋ eval/night111_sim.txt。
用法: python -I tools/night111_sim.py
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

# got 側 莫-token(ことなき site+既存 N/Q/U 出力 莫形)・exp 側 莫-token(N106 同款)
GOT_TOKEN_RE = re.compile("こと莫かれ|こと莫く|こと莫き|こと莫し|ことなき")
EXP_TOKEN_RE = re.compile("莫からん|莫くんば|莫かる|莫かれ|莫き|莫く|莫し")

# 任務書固定 follow_map(10 字・N106 §2.3 多数決+语料多数形 tie-break 莫き優先)
# 衝突字 能/己/之 は多数決で 莫き(判错 3 行 rongo1442-1・tonan-1・utsuryo03-7 は
# (a) 値維持=N106 §2.3 実測通り)
FOLLOW_MAP = {"由": "こと莫き", "予": "こと莫き", "我": "こと莫き", "之": "こと莫き",
              "能": "こと莫き", "己": "こと莫き", "大": "こと莫し",
              "知": "こと莫からん", "吾": "こと莫からん", "如": "こと莫かる"}
DEFAULT_REPL = "こと莫き"
GUARD = ("莫",)

# N106 記録 per-row((a) 単一 repl と follow)・night107 基線で逐位一致前提(N109 §2(d))
N106_PER_ROW_A = {
    "mujun-2": (11, 10), "onoreshiru-1": (18, 17), "kagakujota-1": (27, 26),
    "kanchuna-1": (82, 81), "rongo0615-1": (12, 11), "rongo0732-1": (23, 22),
    "rongo1315-1": (113, 110), "rongo1442-1": (55, 54), "p-danjoshitsu-1": (36, 35),
    "tarekako-1": (12, 11), "tonan-1": (29, 28), "warekimi-1": (35, 34),
    "roushi46-2": (34, 35), "utsuryo03-7": (63, 63), "rikutou26-5": (53, 54),
}
N106_PER_ROW_FOLLOW = {
    "mujun-2": (11, 10), "onoreshiru-1": (18, 17), "kagakujota-1": (27, 24),
    "kanchuna-1": (82, 81), "rongo0615-1": (12, 11), "rongo0732-1": (23, 20),
    "rongo1315-1": (113, 110), "rongo1442-1": (55, 54), "p-danjoshitsu-1": (36, 33),
    "tarekako-1": (12, 11), "tonan-1": (29, 28), "warekimi-1": (35, 34),
    "roushi46-2": (34, 34), "utsuryo03-7": (63, 63), "rikutou26-5": (53, 54),
}
N106_FOLLOW_MAP = {"能": "莫き", "己": "莫き", "我": "莫き", "知": "莫からん",
                   "之": "莫き", "由": "莫き", "吾": "莫からん", "予": "莫き",
                   "如": "莫かる", "大": "莫し"}
N106_FOLLOW_DIST = {"能": 2, "己": 2, "我": 1, "知": 1, "之": 4, "由": 2,
                    "吾": 1, "予": 2, "如": 1, "大": 2}

# 任務書改善 4 行(d0_a→d1)・改写 5 行(大→莫し 2・知/吾→莫からん 2・如→莫かる 1)
TASK_BETTER = {"kagakujota-1": (26, 24), "p-danjoshitsu-1": (35, 33),
               "rongo0732-1": (22, 20), "roushi46-2": (35, 34)}
TASK_REWRITE = {"roushi46-2": "こと莫し", "rikutou26-5": "こと莫し",
                "kagakujota-1": "こと莫からん", "rongo0732-1": "こと莫からん",
                "p-danjoshitsu-1": "こと莫かる"}
TASK_RIKUTOU = 54
EXPECTED_CLASS = {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}


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
    _LEV_IMPL = "纯 Python 回退(night85_eval 同一算法・归档逐位一致実績)"


def lev(a, b):
    if _lev_c is not None:
        return _lev_c(a, b)
    return _lev_pure(a, b)


def norm(s):
    return re.sub(r"\s+", "", s or "")


def splice(text, spans):
    """spans = [(start, end, repl)] を後方から置換。"""
    out = text
    for s0, s1, repl in sorted(spans, key=lambda x: -x[0]):
        out = out[:s0] + repl + out[s1:]
    return out


# ---- 機構本体(実装予定アルゴリズムと同一の独立実装・N106 §1.2 手順 1〜4) ----
def guard_followup_apply(text, hb):
    """(new_text, mode) を返す。mode = None(不発火)/"fail_safe"(対位失敗→default
    全置換)/"follow"(対位成立・site 級 follow_map 判定)。"""
    # 手順 1:containment guard(第一 gate・row 級・現行 guard 規則と同一語义)
    if GUARD and not any(g in hb for g in GUARD):
        return text, None
    tokens = list(GOT_TOKEN_RE.finditer(text))
    if not any(t.group() == "ことなき" for t in tokens):
        return text, None
    # 手順 2:対位(got 莫-token × hb 莫・順序 1:1)
    mo_iter = list(re.finditer("莫", hb))
    if len(tokens) != len(mo_iter):
        # 個数不一致 → default_repl で全置換(現行動作=(a) 単一 repl・fail-safe)
        return text.replace("ことなき", DEFAULT_REPL), "fail_safe"
    # 手順 3+4:site ごとに後继字判定→repl 選択(ことなき site のみ触る)
    sites = []
    spans = []
    for gi, gm in enumerate(tokens):
        if gm.group() != "ことなき":
            continue
        mo = mo_iter[gi]
        nxt = hb[mo.end():mo.end() + 1] or "⏎"
        repl = FOLLOW_MAP.get(nxt, DEFAULT_REPL)
        spans.append((gm.start(), gm.end(), repl))
        sites.append({"site_index": gi, "hb_pos": mo.start(), "follow": nxt,
                      "repl": repl})
    return splice(text, spans), sites


lines = []
sim = {}


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
        open(os.path.join(EV, "night111_sim.txt"), "w", encoding="utf-8",
             newline="\n").write("\n".join(lines) + "\n")
    except Exception:
        pass


def main():
    global sim
    t_start = time.time()
    sim = {"script": "tools/night111_sim.py", "night": 111,
           "mode": "守り字后继字機構 follow_map 実施夜・sim 先行(基线 night107 归档)",
           "verdict": None}

    pr("== S2 词库 import 实证(不動確認)==")
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

    doc8 = json.load(open(os.path.join(EV, "night107_results_8165.json"), encoding="utf-8"))
    rows8 = [r for r in doc8["results"] if r.get("udkundoku_kakikudashi") is not None]
    gate(len(rows8) == 8165, "night107_results_8165 行数 %d != 8165" % len(rows8))
    doc4 = json.load(open(os.path.join(EV, "night107_results_4000.json"), encoding="utf-8"))
    rows4 = doc4["results"]
    gate([r["id"] for r in rows4] == [r["id"] for r in rows8[:4000]],
         "night107_results_4000 与 8165 前 4000 行序不一致")

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
    pr("== S1 行分类 %s(期待 %s)==" % (dict(cc), EXPECTED_CLASS))
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
    pr("  基线 avgDist 4000=%.3f 8165=%.3f(归档 13.460/13.466)exact %d/%d(归档 24/30)"
       % (base_avg4, base_avg8, exact_base4, exact_base8))
    gate(close(base_avg4, 13.460) and close(base_avg8, 13.466), "基线 avgDist != 13.460/13.466")
    gate(exact_base4 == 24 and exact_base8 == 30, "基线 exact != 24/30")
    rows4_ids = {r["id"] for r in rows4}

    # ---------- A1 発火(guard 莫 containment・ことなき 残量) ----------
    pr("")
    pr("== A1 発火(guard 莫 containment 通過×got ことなき 残量)==")
    fired = []
    for r in reachable:
        rid = r["id"]
        hb = hb_of[rid]
        if hb and not any(g in hb for g in GUARD):
            continue
        got0, exp, d_raw = d0_cache[rid]
        n = got0.count("ことなき")
        if n:
            fired.append({"id": rid, "cls": cls[rid], "n_sites": n, "got": got0,
                          "exp": exp, "d_raw": d_raw})
    by_id = {c["id"]: c for c in fired}
    pr("  発火 %d 行(site 計 %d)" % (len(fired), sum(c["n_sites"] for c in fired)))
    gate(len(fired) == 15, "A1 発火 %d != 15" % len(fired))
    gate(set(by_id) == set(N106_PER_ROW_A), "A1 発火行集合 != N103/N106 記録 15 行")

    # ---------- A2 対位(got 莫-token × exp 莫-token × 白文 莫) ----------
    pr("")
    pr("== A2 対位(got 莫-token × exp 莫-token × 白文 莫・順序 1:1)==")
    n_fail_safe = 0
    site_rows = []
    for c in fired:
        rid = c["id"]
        hb = hb_of[rid]
        gt = list(GOT_TOKEN_RE.finditer(c["got"]))
        et = list(EXP_TOKEN_RE.finditer(c["exp"]))
        n_mo_hb = hb.count("莫")
        gate(len(gt) == len(et), "A2 %s token 数不一致 got %d vs exp %d"
             % (rid, len(gt), len(et)))
        gate(n_mo_hb == len(gt), "A2 %s 白文 莫 %d != got token %d(対位不能)"
             % (rid, n_mo_hb, len(gt)))
        # 機構アルゴリズムを走らせ fail-safe 分岐の発火を数える(15 行は全対位成立前提)
        _, mode = guard_followup_apply(c["got"], hb)
        if mode == "fail_safe":
            n_fail_safe += 1
        site_rows.append({"id": rid, "cls": c["cls"], "got": c["got"], "exp": c["exp"],
                          "hb": hb, "n_tokens": len(gt), "d_raw": c["d_raw"]})
    gate(n_fail_safe == 0, "A2 fail-safe 発火 %d 行 != 0(15 行全対位成立前提)" % n_fail_safe)
    pr("  15 行全対位成立・fail-safe 発火 0")

    # ---------- A3 site 後继字判定(follow_map 10 字・表外 0) ----------
    pr("")
    pr("== A3 site 後继字判定(follow_map 10 字)==")
    all_sites = []
    for sr in site_rows:
        rid = sr["id"]
        hb = sr["hb"]
        gt = list(GOT_TOKEN_RE.finditer(sr["got"]))
        mo_iter = list(re.finditer("莫", hb))
        et = list(EXP_TOKEN_RE.finditer(sr["exp"]))
        for gi, gm in enumerate(gt):
            if gm.group() != "ことなき":
                continue
            mo = mo_iter[gi]
            nxt = hb[mo.end():mo.end() + 1] or "⏎"
            em = et[gi]
            s = {"row_id": rid, "site_index": gi, "hb_pos": mo.start(), "follow": nxt,
                 "exp_tok": em.group(),
                 "pred": FOLLOW_MAP.get(nxt, DEFAULT_REPL)[2:],  # 活用形部分
                 "repl": FOLLOW_MAP.get(nxt, DEFAULT_REPL)}
            s["ok"] = ("こと" + s["pred"]) == ("こと" + s["exp_tok"]) or s["pred"] == s["exp_tok"]
            all_sites.append(s)
            pr("  %-16s site#%d 後继=%s 予測=%s 実=%s %s"
               % (rid, gi, nxt, s["pred"], s["exp_tok"], "○判対" if s["ok"] else "×判错"))
    gate(len(all_sites) == 18, "A3 site 总数 %d != 18(N103 census)" % len(all_sites))
    follow_c = collections.Counter(s["follow"] for s in all_sites)
    gate(dict(follow_c) == N106_FOLLOW_DIST,
         "A3 後继字分布 %s != N106 記録 %s" % (dict(follow_c), N106_FOLLOW_DIST))
    n_ok = sum(1 for s in all_sites if s["ok"])
    ng_ids = sorted({s["row_id"] for s in all_sites if not s["ok"]})
    gate(n_ok == 15 and ng_ids == ["rongo1442-1", "tonan-1", "utsuryo03-7"],
         "A3 site 判定 %d/18・判错行 %s != N106 記録 15/18・[rongo1442-1,tonan-1,utsuryo03-7]"
         % (n_ok, ng_ids))
    out_of_map = sorted({s["follow"] for s in all_sites if s["follow"] not in FOLLOW_MAP})
    gate(not out_of_map, "A3 表外後继字 %s != 0" % out_of_map)
    pr("  判対 %d/18(判错=%s)・表外後继字 0・10 字表で全 site 判定" % (n_ok, ng_ids))

    # ---------- A4/A5 per-row 逐位(N106 記録対照) ----------
    pr("")
    pr("== A4 (a) 単一 repl per-row(N106 記録対照)==")
    res_a = {}
    for sr in site_rows:
        rid = sr["id"]
        got_a = sr["got"].replace("ことなき", DEFAULT_REPL)
        res_a[rid] = {"d0": sr["d_raw"], "d1": lev(got_a, sr["exp"]), "new": got_a}
    for rid, (dd0, dd1) in N106_PER_ROW_A.items():
        gate(rid in res_a and res_a[rid]["d0"] == dd0 and res_a[rid]["d1"] == dd1,
             "A4 %s 実測 %s != N106 (a) 記録 %d→%d"
             % (rid, (res_a[rid]["d0"], res_a[rid]["d1"]) if rid in res_a else None, dd0, dd1))
    pr("  15 行逐位一致(N106 per_row a)")

    pr("")
    pr("== A5 follow 機構 per-row(N106 記録対照)==")
    res_f = {}
    for sr in site_rows:
        rid = sr["id"]
        new_f, mode = guard_followup_apply(sr["got"], sr["hb"])
        gate(mode != "fail_safe", "A5 %s fail-safe(対位不能)" % rid)
        res_f[rid] = {"d0": sr["d_raw"], "d1": lev(new_f, sr["exp"]), "new": new_f}
    for rid, (dd0, dd1) in N106_PER_ROW_FOLLOW.items():
        gate(rid in res_f and res_f[rid]["d0"] == dd0 and res_f[rid]["d1"] == dd1,
             "A5 %s 実測 %s != N106 follow 記録 %d→%d"
             % (rid, (res_f[rid]["d0"], res_f[rid]["d1"]) if rid in res_f else None, dd0, dd1))
    pr("  15 行逐位一致(N106 per_row follow)")
    sim["per_row_a"] = {rid: [v["d0"], v["d1"]] for rid, v in res_a.items()}
    sim["per_row_follow"] = {rid: [v["d0"], v["d1"]] for rid, v in res_f.items()}
    sim["sites"] = all_sites

    # ---------- A6 改写文本 5 行 ----------
    pr("")
    pr("== A6 改写文本(follow got != (a) got)==")
    rewrite = {rid: res_f[rid]["new"] for rid in res_f if res_f[rid]["new"] != res_a[rid]["new"]}
    gate(len(rewrite) == 5, "A6 改写 %d 行 != 5" % len(rewrite))
    gate(set(rewrite) == set(TASK_REWRITE),
         "A6 改写行集合 %s != 任務書 5 行 %s" % (sorted(rewrite), sorted(TASK_REWRITE)))
    for rid, want in TASK_REWRITE.items():
        # 変化 site の repl 変体が行に現れ・(a) 側(default のみ)には無いこと
        # (変体 site 以外は こと莫き=(a) 同値で良い:例 kagakujota-1 site#0 我→こと莫き)
        gate(rid in rewrite and rewrite[rid].count(want) > res_a[rid]["new"].count(want),
             "A6 %s 変体 %s 判定不一致(実測 %s)" % (rid, want, rewrite.get(rid)))
    by_variant = collections.Counter(TASK_REWRITE[rid] for rid in rewrite)
    gate(dict(by_variant) == {"こと莫し": 2, "こと莫からん": 2, "こと莫かる": 1},
         "A6 変体内訳 %s != こと莫し 2・こと莫からん 2・こと莫かる 1" % dict(by_variant))
    pr("  改写 5 行:%s" % {rid: TASK_REWRITE[rid] for rid in sorted(rewrite)})

    # ---------- A7 d 改善 4 行・変差 0 行・rikutou26-5 維持 ----------
    pr("")
    pr("== A7 d 改善/変差((a)→follow 口径)==")
    better = sorted(rid for rid in res_f if res_f[rid]["d1"] < res_a[rid]["d1"])
    worse = sorted(rid for rid in res_f if res_f[rid]["d1"] > res_a[rid]["d1"])
    gate(len(better) == 4 and set(better) == set(TASK_BETTER),
         "A7 改善 %d 行 %s != 任務書 4 行 %s" % (len(better), better, sorted(TASK_BETTER)))
    gate(not worse, "A7 変差新增 %d 行 %s != 0" % (len(worse), worse))
    for rid, (dd0, dd1) in TASK_BETTER.items():
        gate(res_a[rid]["d1"] == dd0 and res_f[rid]["d1"] == dd1,
             "A7 %s 実測 %d→%d != 任務書 %d→%d"
             % (rid, res_a[rid]["d1"], res_f[rid]["d1"], dd0, dd1))
        pr("  %-16s %d→%d BETTER" % (rid, res_a[rid]["d1"], res_f[rid]["d1"]))
    gate(res_a["rikutou26-5"]["d1"] == TASK_RIKUTOU and res_f["rikutou26-5"]["d1"] == TASK_RIKUTOU,
         "A7 rikutou26-5 (a)=%d follow=%d != 任務書維持 %d(拍板行)"
         % (res_a["rikutou26-5"]["d1"], res_f["rikutou26-5"]["d1"], TASK_RIKUTOU))
    pr("  rikutou26-5 %d→%d 維持(拍板行・語順構造差は機構でも不救=N106 §1.4)"
       % (res_a["rikutou26-5"]["d1"], res_f["rikutou26-5"]["d1"]))

    # ---------- A8 Δ(任務書値) ----------
    dsum8 = sum(res_f[rid]["d1"] - res_a[rid]["d1"] for rid in res_f)
    dsum4 = sum(res_f[rid]["d1"] - res_a[rid]["d1"] for rid in res_f if rid in rows4_ids)
    in4 = sum(1 for rid in res_f if rid in rows4_ids)
    pr("")
    pr("== A8 Δ((a)→follow)==")
    pr("  Δ8165 %+.4f(%d 字)・Δ4000 %+.4f(%d 字・4000 内 %d 行)"
       % (dsum8 / 8165, dsum8, dsum4 / 4000, dsum4, in4))
    gate(dsum8 == -7, "A8 Δ8165 %d 字 != −7 字" % dsum8)
    gate(dsum4 == -6, "A8 Δ4000 %d 字 != −6 字" % dsum4)
    sim["delta_follow_vs_a"] = {"chars8165": dsum8, "delta8165": round(dsum8 / 8165, 4),
                                "chars4000": dsum4, "delta4000": round(dsum4 / 4000, 4),
                                "in4000": in4, "better": better, "worse": worse}

    # ---------- A9 raw→follow 総効果(golden 予想根拠・N106 follow 記録対照) ----------
    tot8 = sum(res_f[rid]["d1"] - res_f[rid]["d0"] for rid in res_f)
    tot4 = sum(res_f[rid]["d1"] - res_f[rid]["d0"] for rid in res_f if rid in rows4_ids)
    pr("")
    pr("== A9 raw→follow 総効果(N106 follow 記録 −19 字 対照)==")
    pr("  総効果 8165 %+d 字・4000 内 %+d 字(4000 内 %d 行)"
       % (tot8, tot4, sum(1 for rid in res_f if rid in rows4_ids)))
    gate(tot8 == -19, "A9 raw→follow 8165 %d 字 != −19 字(N106 follow 記録)" % tot8)
    gate(tot4 == -20, "A9 raw→follow 4000 内 %d 字 != −20 字(N106 Δ4000 follow −0.0050×4000)" % tot4)
    est8 = round(base_avg8 + tot8 / 8165, 3)
    est4 = round(base_avg4 + tot4 / 4000, 3)
    pr("  golden 理論予想:4000 %.3f・8165 %.3f(基线 %s±実跑丸め)"
       % (est4, est8, "13.460/13.466"))
    sim["delta_raw_to_follow"] = {"chars8165": tot8, "chars4000": tot4,
                                  "est_golden_4000": est4, "est_golden_8165": est8}

    # ---------- A10 冪等 ----------
    pr("")
    pr("== A10 冪等(follow 適用後再適用=変化 0・(a) 後再適用=変化 0)==")
    bad_idem = []
    for sr in site_rows:
        new_f, _ = guard_followup_apply(sr["got"], sr["hb"])
        once2, mode2 = guard_followup_apply(new_f, sr["hb"])
        if once2 != new_f:
            bad_idem.append(sr["id"])
        got_a = res_a[sr["id"]]["new"]
        got_a2 = got_a.replace("ことなき", DEFAULT_REPL)
        if got_a2 != got_a:
            bad_idem.append(sr["id"] + "(a)")
        if "ことなき" in new_f:
            bad_idem.append(sr["id"] + "(残)")
    gate(not bad_idem, "A10 冪等 bad %d 件 %s" % (len(bad_idem), bad_idem))
    pr("  冪等 bad 0(15 行)")

    sim["verdict"] = "PASS"
    sim["lev_impl"] = _LEV_IMPL
    sim["elapsed_sec"] = round(time.time() - t_start)
    json.dump(sim, open(os.path.join(EV, "night111_sim.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night111_sim.txt"), "w", encoding="utf-8",
         newline="\n").write("\n".join(lines) + "\n")
    pr("")
    pr("written: eval/night111_sim.json / night111_sim.txt")
    pr("SUMMARY: 発火 15・改写 5・改善 4(任務書 4 行値一致)・変差新增 0・rikutou26-5 54 維持")
    pr("SUMMARY: Δ8165 −7 字(−0.001)・Δ4000 −6 字(−0.002)・raw→follow −19/−20 字")
    pr("elapsed %.0fs" % sim["elapsed_sec"])


if __name__ == "__main__":
    main()
