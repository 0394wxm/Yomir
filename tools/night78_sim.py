# -*- coding: utf-8 -*-
"""night78_sim.py — N78 Rule N 候选离线模拟＋收录判定＋组合双口径
（机制照抄 night73_sim.py：lev / apply_one / run / idempotent，
基线 = night73 真机 8165（Rule M 后链尾）。

N72/N73 性能机制沿用：Levenshtein C 库（.night72_deps 隔离目录，import 失败自动
回退纯 Python，200 对逐位等价抽查）＋ d0=lev(got,exp) 全候选共享缓存＋未改动行
跳过第二次 lev。
变差>0 一律不收（任务书硬规则）。0 変差且 delta<0 才进组合。

候补設計（night78_mine/probe 実数に基づく）：
  ことな族（exp に こと莫かれ/こと莫し/莫し 3 字形、exp 自書 kana 0 行・白文守り 100%）：
    死行 kokyo09-5（白文「嚴父莫大於配天」）は すことなかれ 行——
    prefix keys する/ざる/なる/〜る（=ることなかれ 1 本で substring 覆盖 61 行）
    は死行を避ける。ことなかれ umbrella（死行含む）は对照測定のみ。
  現代副詞族（got 側現代語 adverb → exp 側漢字、got/exp 互补計数）：
    しばしば→屢〻(4)・ほとんど→殆(3)・はいよいよ→弥〻(6)・いよいよ→弥(3)
    ・やや→稍(5)・はやや→稍く(2)・たま→偶〻(3)・なんぞ→胡 guard 胡(2)。
守り字：新旧字体两形并查（N72 移交①成文执行）。
输出 eval/night78_sim.json / night78_sim.txt。
"""
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, ".night72_deps"))  # 隔离目录：Levenshtein
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
    _LEV_IMPL = "Levenshtein C 0.27.5 (.night72_deps 隔离目录)"
except Exception:  # pragma: no cover
    _lev_c = None
    _LEV_IMPL = "纯 Python 回退"


def lev(a, b):
    if _lev_c is not None:
        return _lev_c(a, b)
    return _lev_pure(a, b)


CANDIDATES = {
    # ---- ことな族（repl こと莫かれ＝exp 実書形 こと莫かれ 行 exact＋他字形行も改善）----
    "koto_full":       {"kana": "ことなかれ", "repl": "こと莫かれ", "guard": ("莫",), "longer": (),
                        "tag": "【对照測定】ことなかれ→こと莫かれ umbrella（死行 kokyo09-5＝すことなかれ 行を含む・拒案予想）"},
    "koto_suru":       {"kana": "することなかれ", "repl": "すること莫かれ", "guard": ("莫",), "longer": (),
                        "tag": "することなかれ→すること莫かれ（16 行・死行 kokyo09-5 は す-form で非該当）"},
    "koto_ru":         {"kana": "ることなかれ", "repl": "ること莫かれ", "guard": ("莫",), "longer": (),
                        "tag": "ることなかれ→ること莫かれ（substring 覆盖 なる/する/ざる/〜る 系 61 行・死行非該当）"},
    "koto_uzaru":      {"kana": "ざることなかれ", "repl": "ざること莫かれ", "guard": ("莫",), "longer": (),
                        "tag": "ざることなかれ→ざること莫かれ（13 行・kamireikei-1 型）"},
    "koto_naru":       {"kana": "なることなかれ", "repl": "なること莫かれ", "guard": ("莫",), "longer": (),
                        "tag": "なることなかれ→なること莫かれ（10 行・kowokaete-4 莫大構文含む→る rule に包含される）"},
    "koto_u":          {"kana": "うことなかれ", "repl": "うこと莫かれ", "guard": ("莫",), "longer": (),
                        "tag": "うことなかれ→うこと莫かれ（9 行・kanae-2 型）"},
    "koto_ki":         {"kana": "きことなかれ", "repl": "きこと莫かれ", "guard": ("莫",), "longer": (),
                        "tag": "きことなかれ→きこと莫かれ（2〜3 行・ichinenkoku-1 型）"},
    "koto_bu":         {"kana": "ぶことなかれ", "repl": "ぶこと莫かれ", "guard": ("莫",), "longer": (),
                        "tag": "ぶことなかれ→ぶこと莫かれ（2 行・rongo1709-1 型）"},
    "koto_ku":         {"kana": "くことなかれ", "repl": "くこと莫かれ", "guard": ("莫",), "longer": (),
                        "tag": "くことなかれ→くこと莫かれ（2 行）"},
    "koto_tsu":        {"kana": "つことなかれ", "repl": "つこと莫かれ", "guard": ("莫",), "longer": (),
                        "tag": "つことなかれ→つこと莫かれ（1 行）"},
    # ---- 現代副詞族 ----
    "shibashiba_maru": {"kana": "しばしば", "repl": "屢〻", "guard": ("屢",), "longer": (),
                        "tag": "しばしば→屢〻（4 行・exp 屢〻/屢）"},
    "shibashiba":      {"kana": "しばしば", "repl": "屢", "guard": ("屢",), "longer": (),
                        "tag": "【字形比较】しばしば→屢"},
    "hondo":           {"kana": "ほとんど", "repl": "殆", "guard": ("殆",), "longer": (),
                        "tag": "ほとんど→殆（3 行）"},
    "haiyoiyoi_maru":  {"kana": "はいよいよ", "repl": "弥〻", "guard": ("弥", "彌"), "longer": (),
                        "tag": "はいよいよ→弥〻（6 行・余計な は 付き；白文 旧字体 彌＝新旧両形 guard）"},
    "haiyoiyoi":       {"kana": "はいよいよ", "repl": "弥", "guard": ("弥", "彌"), "longer": (),
                        "tag": "【字形比较】はいよいよ→弥"},
    "yoiyoi_maru":     {"kana": "いよいよ", "repl": "弥〻", "guard": ("弥", "彌"), "longer": (),
                        "tag": "いよいよ→弥〻（3 行 standalone＋は付きは長 key が先）"},
    "yoiyoi":          {"kana": "いよいよ", "repl": "弥", "guard": ("弥", "彌"), "longer": (),
                        "tag": "【字形比较】いよいよ→弥"},
    "hayayaya":        {"kana": "はやや", "repl": "稍く", "guard": ("稍",), "longer": (),
                        "tag": "はやや→稍く（2 行・exp 稍く）"},
    "yaya":            {"kana": "やや", "repl": "稍", "guard": ("稍",), "longer": (),
                        "tag": "やや→稍（5 行・got/exp 5/5 互补）"},
    "tama_maru":       {"kana": "たま", "repl": "偶〻", "guard": ("偶",), "longer": (),
                        "tag": "たま→偶〻（3 行）"},
    "tama":            {"kana": "たま", "repl": "偶", "guard": ("偶",), "longer": (),
                        "tag": "【字形比较】たま→偶"},
    "nanzo_hu":        {"kana": "なんぞ", "repl": "胡", "guard": ("胡",), "longer": (),
                        "tag": "なんぞ→胡 guard 胡（K 何ぞ/奚/曷 の分工補完・2 行）"},
}
COMBO_ORDER = ["koto_suru", "koto_uzaru", "koto_naru", "koto_u", "koto_ki",
               "koto_bu", "koto_ku", "koto_tsu", "koto_ru",
               "haiyoiyoi_maru", "yoiyoi_maru", "shibashiba_maru", "hondo",
               "hayayaya", "yaya", "tama", "nanzo_hu"]


def norm(s):
    return re.sub(r"\s+", "", s or "")


def apply_one(text, kana, repl, longer):
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


def seg_of(r):
    url = r.get("source_url", "") or ""
    if "kanbun.info/shibu02/" in url.lower():
        return "shibu02"
    if "/syubu/" in url.lower():
        return "kansi"
    return None


def run(rows, kana_rules, d0_cache, keep_changed=False):
    better = worse = same = 0
    changed_entries = 0
    total_old = total_new = 0
    worse_detail = []
    changed_rows = []
    segs = {"s4000": [0, 0, 0], "s3908": [0, 0, 0], "s257": [0, 0, 0],
            "shibu02": [0, 0, 0], "kansi": [0, 0, 0]}
    for idx, r in enumerate(rows):
        rid = r["id"]
        hb = norm(r["hakubun"])
        got0, exp, d0 = d0_cache[rid]
        new = got0
        nchg = 0
        for kana, repl, guard, longer in kana_rules:
            if guard and not any(g in hb for g in guard):
                continue
            new, n = apply_one(new, kana, repl, longer)
            nchg += n
        d1 = d0 if nchg == 0 else lev(new, exp)
        total_old += d0
        total_new += d1
        if idx < 4000:
            sk = "s4000"
        elif idx < 7908:
            sk = "s3908"
        else:
            sk = "s257"
        seg_ofs = seg_of(r)
        if nchg:
            changed_entries += 1
            delta = d1 - d0
            for key in [sk] + ([seg_ofs] if seg_ofs else []):
                segs[key][0 if delta < 0 else (1 if delta > 0 else 2)] += 1
            if keep_changed:
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
    out = {"entries": n, "changed_entries": changed_entries,
           "avg_old": round(total_old / n, 3), "avg_new": round(total_new / n, 3),
           "delta": round((total_new - total_old) / n, 3),
           "better": better, "worse": worse, "same": same,
           "segs": {k: {"better": v[0], "worse": v[1], "same": v[2]} for k, v in segs.items()},
           "worse_detail": worse_detail[:40]}
    if keep_changed:
        out["changed_rows"] = changed_rows
    return out


def idempotent(rows, kana_rules, d0_cache):
    bad = 0
    for r in rows:
        hb = norm(r["hakubun"])
        got = d0_cache[r["id"]][0]
        new = got
        for kana, repl, guard, longer in kana_rules:
            if guard and not any(g in hb for g in guard):
                continue
            new, _ = apply_one(new, kana, repl, longer)
        twice = new
        for kana, repl, guard, longer in kana_rules:
            if guard and not any(g in hb for g in guard):
                continue
            twice, _ = apply_one(twice, kana, repl, longer)
        if twice != new:
            bad += 1
    return bad


def exact_count(rows, kana_rules, d0_cache):
    before = after = 0
    for r in rows:
        hb = norm(r["hakubun"])
        got, exp, _d0 = d0_cache[r["id"]]
        new = got
        for kana, repl, guard, longer in kana_rules:
            if guard and not any(g in hb for g in guard):
                continue
            new, _ = apply_one(new, kana, repl, longer)
        before += got == exp
        after += new == exp
    return before, after


def main():
    doc = json.load(open(os.path.join(EV, "night73_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序" % i
    rows8 = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    assert len(rows8) == 8165, "基线行数 %d != 8165" % len(rows8)
    doc4 = json.load(open(os.path.join(EV, "night73_results_4000.json"), encoding="utf-8"))
    rows4 = doc4["results"]
    assert [r["id"] for r in rows4] == [r["id"] for r in rows8[:4000]], "4000/8165 前 4000 行不同序"
    for a, b in zip(rows4, rows8[:4000]):
        assert norm(a["udkundoku_kakikudashi"]) == norm(b["udkundoku_kakikudashi"]), \
            "4000/8165 got 不一致: %s" % a["id"]

    # repl 终字形断言
    from backend.kundoku_rules import normalize_shinjitai, SHINJITAI_MAP
    for k, c in CANDIDATES.items():
        assert normalize_shinjitai(c["repl"]) == c["repl"], \
            "repl 非终字形: %s %s" % (k, c["repl"])

    gmap = {g["id"]: g for g in golden}
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

    # ---- d0 全局缓存 ----
    t0 = time.time()
    d0_cache = {}
    checked = 0
    for r in rows8:
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        d = lev(got, exp)
        if _lev_c is not None and checked < 200 and len(got) > 20:
            assert _lev_pure(got, exp) == d, "C 库与参照实现不等价: %s" % r["id"]
            checked += 1
        d0_cache[r["id"]] = (got, exp, d)
    pr_base = "lev 实现: %s（抽查 %d 对等价）| d0 缓存 8165 行耗时 %.0fs" % (_LEV_IMPL, checked, time.time() - t0)

    out = {}
    lines = []

    def pr(s=""):
        lines.append(s)
        print(s, flush=True)

    pr(pr_base)
    pr("样本 8165 条 | 基线 avgDist %.3f" % (sum(v[2] for v in d0_cache.values()) / len(d0_cache)))

    # ==== 预检：候补行実例＋長詞走査＋守り字検証 ====
    pr("")
    pr("== 预检 ==")
    # a) 各候补の実例 2 行（got/exp/白文）＋守り字命中
    for k, c in CANDIDATES.items():
        gf = guard_forms(c["guard"])
        recs = []
        for r in rows8:
            got, exp, _ = d0_cache[r["id"]]
            if c["kana"] not in got:
                continue
            hb = norm(r["hakubun"])
            if gf and not any(f in hb for f in gf):
                continue
            recs.append((r["id"], got, exp, hb))
        pr("  [%s] 守り %s 命中行 %d" % (k, "/".join(gf), len(recs)))
        for rid, got, exp, hb in recs[:2]:
            pr("    %s" % rid)
            pr("      got: %s" % got[:100])
            pr("      exp: %s" % exp[:100])
            pr("      白文: %s" % hb[:100])
    # b) 長詞走査（kana＋後続假名＝誤発火の疑い）
    pr("")
    for w in ("しばしば", "ほとんど", "いよいよ", "はいよいよ", "やや", "はやや", "たま", "なんぞ"):
        long_hits = []
        for r in rows8:
            got = d0_cache[r["id"]][0]
            for m in re.finditer(w, got):
                tail = got[m.end():m.end() + 2]
                if tail and re.match(r"[ぁ-ゖー]", tail):
                    long_hits.append((r["id"], got[max(0, m.start() - 6):m.end() + 6]))
        pr("  [長詞] %s＋後続假名: %s" % (w, long_hits[:6] or "無し"))
    # c) ことな族の守り字外行（莫 無し白文）
    nog = []
    for r in rows8:
        got, exp, _ = d0_cache[r["id"]]
        if "ことなかれ" in got and "莫" not in norm(r["hakubun"]):
            nog.append(r["id"])
    pr("  [ことな族] ことなかれ 行で白文 莫 無し（守り外・収集漏れ）: %s" % (nog or "無し"))
    # d) 死行実確認
    for rid in ("kokyo09-5", "kowokaete-4"):
        got, exp, _ = d0_cache[rid]
        hb = norm(gmap[rid]["hakubun"])
        pr("  [死行] %s 白文: %s" % (rid, hb[:80]))
        pr("         got: %s" % got[:80])
        pr("         exp: %s" % exp[:80])
    # e) なんぞ 残量 7 行の内訳（K 守り外）
    nz = []
    for r in rows8:
        got, exp, _ = d0_cache[r["id"]]
        if "なんぞ" in got:
            hb = norm(r["hakubun"])
            nz.append((r["id"], next((c for c in ("何", "奚", "曷", "胡") if c in hb), "-"),
                       got[:40], exp[:40]))
    pr("  [なんぞ] 残量 %d 行（K 何ぞ/奚/曷 の守り外残量）" % len(nz))
    for rid, g, got, exp in nz:
        pr("    %s 守り=%s got: %s | exp: %s" % (rid, g, got, exp))
    pr("")

    # ---- 多守り行检查 ----
    multi = []
    for r in rows8:
        hb = norm(r["hakubun"])
        got = d0_cache[r["id"]][0]
        if "ことなかれ" in got and "莫" in hb and "勿" in hb:
            multi.append(r["id"] + "(莫∧勿)")
        if "ことなかれ" in got and "莫" in hb and "毋" in hb:
            multi.append(r["id"] + "(莫∧毋)")
        if "なんぞ" in got and "胡" in hb and ("何" in hb or "奚" in hb or "曷" in hb):
            multi.append(r["id"] + "(胡∧何/奚/曷)")
    pr("多守り行: %s" % (multi or "無し"))
    pr("")

    # ---- 单条 0 变差门 ----
    pr("== 单条 0 変差門 ==")
    accepted = []
    gate = {}
    for k in list(CANDIDATES.keys()):
        t1 = time.time()
        c = CANDIDATES[k]
        res = run(rows8, [(c["kana"], c["repl"], c["guard"], c["longer"])], d0_cache)
        gate[k] = {"tag": c["tag"], "changed": res["changed_entries"],
                   "better": res["better"], "worse": res["worse"],
                   "delta": res["delta"],
                   "worse_detail": res["worse_detail"][:8]}
        verdict = "収" if (res["worse"] == 0 and res["delta"] < 0) else (
            "拒（変差 %d）" % res["worse"] if res["worse"] else "拒（無益/無目標）")
        gate[k]["verdict"] = verdict
        # accepted は後で COMBO_ORDER 順に構成（dict 順に依存しない）
        gate[k]["verdict"] = verdict
        pr("  %-16s 改写 %4d 行 better %4d worse %d delta %8.3f → %s (%.0fs) | %s" % (
            k, res["changed_entries"], res["better"], res["worse"], res["delta"],
            verdict, time.time() - t1, c["tag"]))
        for wd in res["worse_detail"][:4]:
            pr("      変差行 %s %d→%d" % (wd["id"], wd["old"], wd["new"]))
    accepted = [k for k in COMBO_ORDER if gate[k]["verdict"] == "収"]
    pr("収録候補（COMBO 順）: %s" % ",".join(accepted))
    pr("（収録数 %d / 门槛 3）" % len(accepted))
    pr("")

    # ---- 组合 ----
    combo = [(CANDIDATES[k]["kana"], CANDIDATES[k]["repl"],
              CANDIDATES[k]["guard"], CANDIDATES[k]["longer"]) for k in accepted]
    pr("== 组合（%d 条）幂等验证 ==" % len(combo))
    bad = idempotent(rows8, combo, d0_cache)
    pr("  idempotent bad = %d（0 で冪等）" % bad)

    pr("")
    pr("== 组合双口径离线真算 ==")
    res8 = run(rows8, combo, d0_cache, keep_changed=True)
    ex8 = exact_count(rows8, combo, d0_cache)
    res4 = run(rows4, combo, d0_cache)
    ex4 = exact_count(rows4, combo, d0_cache)
    for tag, res, ex in (("4000", res4, ex4), ("8165", res8, ex8)):
        pr("  [golden_%s] 改写 %d 行 | better %d worse %d | avgDist %.3f→%.3f (Δ%.3f) | exact %d→%d" % (
            tag, res["changed_entries"], res["better"], res["worse"],
            res["avg_old"], res["avg_new"], res["delta"], ex[0], ex[1]))
        for sk, v in res["segs"].items():
            if v["better"] or v["worse"] or v["same"]:
                pr("      %-8s better %4d worse %d same %d" % (sk, v["better"], v["worse"], v["same"]))
    pr("")
    pr("  变差行明细（8165）: %s" % ("無し" if res8["worse"] == 0 else ""))
    for wd in res8["worse_detail"][:10]:
        pr("    %s %d→%d | got %s | exp %s | new %s" % (
            wd["id"], wd["old"], wd["new"], wd["got"][:40], wd["exp"][:40], wd["newtext"][:40]))

    out["lev_impl"] = _LEV_IMPL
    out["baseline"] = "night73_results_8165.json"
    out["gate"] = gate
    out["accepted"] = accepted
    out["multi_guard_rows"] = multi
    out["idempotent_bad"] = bad
    out["precheck"] = {"kotona_noguard": nog, "long_words": "see txt",
                       "nanzo_residual": nz}
    out["combo_8165"] = {k: v for k, v in res8.items() if k != "changed_rows"}
    out["combo_4000"] = res4
    out["exact_8165"] = {"before": ex8[0], "after": ex8[1]}
    out["exact_4000"] = {"before": ex4[0], "after": ex4[1]}
    json.dump(out, open(os.path.join(EV, "night78_sim.json"), "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    json.dump(res8["changed_rows"], open(os.path.join(EV, "night78_combo_changed_rows.json"),
              "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night78_sim.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("")
    print("written: eval/night78_sim.json / night78_sim.txt / night78_combo_changed_rows.json")


if __name__ == "__main__":
    main()
