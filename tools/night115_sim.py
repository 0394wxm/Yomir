# -*- coding: utf-8 -*-
"""night115_sim.py — Night 115 ④：剥夹注管線設計（Stage 0–3）＋sim 验证（sim 層・禁动 backend/）。

設計（実装夜で backend/main.py に落とす spec・本夜は sim 層で同関数を再実装して検証）：
  Stage 0 検出：detect_text_type 本体は改訂しない。新 signal＝has_ruby_annotation(text)
    （RUBY_SPAN re （[^（）]*[ぁ-ゖー][^（）]*） の search・B9 証拠式と同一）。
    管線 scope＝engine 分支行のうち ruby 注记を含む行だけ剥いてから引擎（実測 2 行）。
    kana 分支行（echo30/rerun218/no_tail1）は N84 尾段路径維持＝既存の注记处理そのもの。
    誤判 fallback：kana 分岐は一切触らない（真・仮名文回帰ゼロ）。
  Stage 1 剥離：strip_annotation(text)＝RUBY_SPAN.sub("", text)（全角 （） のみ・
    仮名含 span だけ剥す・剥下物は捨てる〔拍板 3 選 1 の既定値〕）。
  Stage 2 規則鏈：剥離後 text は现行鏈 _kundoku_result_for(…,use_cache=False) そのまま（零改動）。
  Stage 3 出力契約：got＝normalize_shinjitai(kakikudashi)（response 層）・注记 span は got に現れない。
  不变量：I1 非注记行 strip=byte-identical・I2 冪等 strip∘strip=strip・I3 剥後無括号・
    I4 kana 分支（sonshi09-38 含む）路径不変・I6 管線行 got 無注记 span。
sim 验证：
  (S1) 不变量 I1–I3 を 8165 全行で実測。
  (S2) engine 分支 2 行：現行 got 再現（byte-identical）→ 設計版 d1＝lev(剥離→鏈→shinjitai, exp)。
  (S3) 被否替代案の証拠：kana 分支 248 行（echo30+rerun218）を「全剥→引擎」で走らせ
    d0 vs d1_full を数える（scope 外の根拠数据・実装しない）。
  判定门：残渣行改善 ∧ 設計 scope 内新增变差 0。
出力 eval/night115_sim.json + .txt（归档は書かない）。
用法: python -I tools/night115_sim.py
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

# ---- Stage 0/1 設計関数（sim 層・backend は一字未改）----
RUBY_SPAN = re.compile(r"（[^（）]*[ぁ-ゖー][^（）]*）")


def has_ruby_annotation(text):
    """Stage 0 新信号：ruby 夹注（仮名含 （…） span）の有無。B9 証拠式と同一口径。"""
    return bool(RUBY_SPAN.search(text))


def strip_annotation(text):
    """Stage 1 剥離：仮名含 （…） span を全剥す（剥下物捨て・冪等・非注记行は identity）。"""
    return RUBY_SPAN.sub("", text)


lines = []
FAIL = []


def pr(s=""):
    lines.append(s)
    print(s, flush=True)


def gate(cond, msg):
    if not cond:
        pr("[FAIL] %s → 停下报数" % msg)
        board["verdict"] = "FAIL"
        write_out()
        sys.exit(2)


def write_out():
    try:
        open(os.path.join(EV, "night115_sim.txt"), "w", encoding="utf-8",
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
except Exception:  # pragma: no cover
    _lev_c = None


def lev(a, b):
    if _lev_c is not None:
        return _lev_c(a, b)
    return _lev_pure(a, b)


def norm(s):
    return re.sub(r"\s+", "", s or "")


board = {}


def main():
    t_start = time.time()
    board = {"script": "tools/night115_sim.py", "night": 115,
             "mode": "剥夹注管線設計 sim（Stage 0–3・backend 零改動）", "verdict": None}
    doc = json.load(open(os.path.join(EV, "night111_results_8165.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    gate(len(rows) == 8165, "行数 %d != 8165" % len(rows))
    from backend.main import detect_text_type, _ruby_tail_kanbun, \
        _kundoku_result_for, _load_engine
    from backend.kundoku_rules import normalize_shinjitai

    cls = {}
    for r in rows:
        raw = r["hakubun"] or ""
        if detect_text_type(raw) == "kana":
            t = _ruby_tail_kanbun(raw)
            cls[r["id"]] = "no_tail" if not t else ("echo" if len(t) <= 8 else "rerun")
        else:
            cls[r["id"]] = "engine"
    got = {r["id"]: norm(r["udkundoku_kakikudashi"] or "") for r in rows}
    exp = {r["id"]: norm(r["expected_kakikudashi"] or "") for r in rows}
    hb = {r["id"]: (r["hakubun"] or "") for r in rows}

    # ---- (S1) 不变量 I1–I3・I4（8165 全行・regex 実測）----
    pr("== (S1) 不变量実測（8165 全行）==")
    n_ident = n_idem = n_clean_after = n_f1 = 0
    for r in rows:
        s = hb[r["id"]]
        st = strip_annotation(s)
        if not has_ruby_annotation(s):
            if st == s:
                n_ident += 1  # I1 非注记行 identity
        if strip_annotation(st) == st:
            n_idem += 1  # I2 冪等
        if has_ruby_annotation(s):
            n_f1 += 1
            if "（" not in st and "）" not in st:
                n_clean_after += 1  # I3 剥後無括号
    pr("  I1 非注记行 strip=identity %d/%d・I2 冪等 %d/8165・I3 F1 行剥後無括号 %d/%d"
       % (n_ident, 8165 - n_f1, n_idem, n_clean_after, n_f1))
    gate(n_ident == 8165 - n_f1 and n_idem == 8165 and n_clean_after == n_f1,
         "不变量 I1/I2/I3 失敗")
    # I4：sonshi09-38 は剥後も仮名主導（kana 分支維持＝管線外）
    son_st = strip_annotation(hb["sonshi09-38"])
    son_kana = detect_text_type(son_st)
    pr("  I4 sonshi09-38: strip 後 detect=%s（＝kana 分支維持・no_tail 不変＝管線外）"
       % son_kana)
    gate(son_kana == "kana", "sonshi09-38 剥後 kana でない → I4 失敗")
    # I5（參考）：dangling ） 6 行は I1 に含まれる（（ が無い＝span 不一致＝identity）
    dang = [i for i, s in hb.items() if "）" in s and "（" not in s]
    pr("  I5 參考：dangling ） %d 行 %s は I1 identity に含まれる" % (len(dang), dang))
    board["invariants"] = {"identity": n_ident, "idempotent": n_idem,
                           "f1_clean": n_clean_after, "f1": n_f1,
                           "sonshi_after": son_kana}

    # ---- (S2) engine 分支 2 行：現行再現＋設計版 d1 ----
    pr("")
    pr("== (S2) 設計管線（engine 分支注记行＝scope 恰 2 行）==")
    scope_ids = [r["id"] for r in rows
                 if cls[r["id"]] == "engine" and has_ruby_annotation(hb[r["id"]])]
    pr("  scope 行 %s（engine 分支 ∧ ruby 注记）" % scope_ids)
    gate(sorted(scope_ids) == ["rikutou59-2", "soji07-6"],
         "scope 行 %s != 残渣 2 行" % scope_ids)
    _load_engine()
    pr("  engine 加載済（7-8s）・現行 got 再現チェック→設計版 d1 測定")
    s2 = []
    for r in rows:
        if r["id"] not in scope_ids:
            continue
        rid = r["id"]
        # 現行再現（byte-identical 门）
        _, _, kk_now = _kundoku_result_for(hb[rid], True, True, use_cache=False,
                                           seg=collections.defaultdict(float))
        now = norm(normalize_shinjitai(kk_now))
        repro = (now == got[rid])
        pr("  %s 現行再現 %s d0=%d" % (rid, repro, lev(got[rid], exp[rid])))
        gate(repro, "%s 現行 got 再現失敗（sim 鏈≠歸档）" % rid)
        # 設計版：strip → 現行鏈（零改動）→ response 層 shinjitai
        cleaned = strip_annotation(hb[rid])
        _, _, kk_new = _kundoku_result_for(cleaned, True, True, use_cache=False,
                                           seg=collections.defaultdict(float))
        new = norm(normalize_shinjitai(kk_new))
        d0 = lev(got[rid], exp[rid])
        d1 = lev(new, exp[rid])
        verdict = "改善" if d1 < d0 else ("same" if d1 == d0 else "変差")
        pr("    %s d0=%d → d1=%d（%s Δ%+d）" % (rid, d0, d1, verdict, d1 - d0))
        pr("      剥後白文 %s" % cleaned[:100])
        pr("      設計 got %s" % new[:100])
        pr("      exp      %s" % exp[rid][:100])
        gate(not RUBY_SPAN.search(new), "%s 設計 got に注记 span 残存（I6 失敗）" % rid)
        s2.append({"id": rid, "d0": d0, "d1": d1, "verdict": verdict, "delta": d1 - d0})
    board["scope_design"] = s2
    n_better = sum(1 for x in s2 if x["verdict"] == "改善")
    n_worse = sum(1 for x in s2 if x["verdict"] == "変差")
    gate(n_worse == 0, "設計 scope 内変差 %d 行 > 0" % n_worse)

    # ---- (S3) 被否替代案の証拠：kana 分支 248 行「全剥→引擎」----
    pr("")
    pr("== (S3) 被否替代案（kana 分支全剥→引擎 reroute）の証拠測定＝実装しない ==")
    alt_ids = [r["id"] for r in rows if cls[r["id"]] in ("echo", "rerun")]
    gate(len(alt_ids) == 248, "kana 分支注记行 %d != 248" % len(alt_ids))
    pr("  対象 %d 行（echo30＋rerun218）・exp は尾段対齐（実測）＝全文経路は長大化見込み" % len(alt_ids))
    alt_rows = []
    cnt = collections.Counter()
    t0 = time.time()
    for k_, r in enumerate(rows):
        rid = r["id"]
        if rid not in set(alt_ids):
            continue
        cleaned = strip_annotation(hb[rid])
        try:
            _, _, kk_alt = _kundoku_result_for(cleaned, True, True, use_cache=False,
                                               seg=collections.defaultdict(float))
            alt = norm(normalize_shinjitai(kk_alt))
        except Exception as e_:  # 引擎例外行もデータとして数える（現行鏈で例外＝reroute 不可の証拠）
            alt = None
            pr("  [例外] %s %r" % (rid, e_))
        d0 = lev(got[rid], exp[rid])
        d1 = lev(alt, exp[rid]) if alt is not None else None
        if d1 is None:
            v = "exception"
        else:
            v = "改善" if d1 < d0 else ("same" if d1 == d0 else "変差")
        cnt[v] += 1
        alt_rows.append({"id": rid, "cls": cls[rid], "d0": d0, "d1_full": d1,
                         "verdict": v})
        if len(alt_rows) % 30 == 0:
            pr("  ... %d/%d 済 %.0fs（改善 %d・same %d・変差 %d・例外 %d）"
               % (len(alt_rows), len(alt_ids), time.time() - t0,
                  cnt["改善"], cnt["same"], cnt["変差"], cnt["exception"]))
            board["alt_partial"] = {"counts": dict(cnt)}
            json.dump(board, open(os.path.join(EV, "night115_sim.json"), "w",
                                  encoding="utf-8", newline="\n"),
                      ensure_ascii=False, indent=1)
    pr("  被否替代案：%s（%.0fs）" % (dict(cnt), time.time() - t0))
    per_cls = collections.Counter("%s|%s" % (x["cls"], x["verdict"]) for x in alt_rows)
    pr("  分類別 %s" % dict(per_cls))
    board["alt_rejected"] = {"counts": dict(cnt), "per_cls": dict(per_cls),
                             "rows": alt_rows}

    # ---- 判定 ----
    pr("")
    pr("== 判定 ==")
    pr("  設計 scope（engine 分支注记行 2 行）：改善 %d・same %d・変差 %d"
       % (n_better, len(s2) - n_better - n_worse, n_worse))
    pr("  不变量 I1/I2/I3/I4/I6 全 PASS・現行 got 再現 byte-identical")
    pr("  被否替代案（248 行全剥→引擎）：変差 %d・改善 %d・same %d・例外 %d"
       % (cnt["変差"], cnt["改善"], cnt["same"], cnt["exception"]))
    pr("  sonshi09-38＝管線外（剥後も kana・no_tail 維持）・echo/rerun＝N84 尾段路径維持"
       "（exp 尾段対齐実測・全剥経路は変差大）")
    design_ok = (n_worse == 0 and n_better >= 1)
    pr("  設計成立判定：%s（残渣行改善 ∧ scope 内新增变差 0）"
       % ("成立" if design_ok else "不成立"))
    board["design_ok"] = design_ok
    board["elapsed_sec"] = round(time.time() - t_start)
    board["verdict"] = "PASS" if design_ok else "DESIGN_FAIL"
    json.dump(board, open(os.path.join(EV, "night115_sim.json"), "w",
                          encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night115_sim.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    pr("")
    pr("written: eval/night115_sim.json / night115_sim.txt")
    pr("elapsed %.0fs verdict=%s" % (board["elapsed_sec"], board["verdict"]))


if __name__ == "__main__":
    main()
