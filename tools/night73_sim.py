# -*- coding: utf-8 -*-
"""night73_sim.py — N73 Rule M 候选离线模拟＋收录判定＋组合双口径
（机制照抄 night72_sim.py：lev / apply_one / run / idempotent，
基线 = night72 真机 8165（Rule L 后链尾）。

N72 性能机制沿用：Levenshtein C 库（.night72_deps 隔离目录，import 失败自动
回退纯 Python，200 对逐位等价抽查）＋ d0=lev(got,exp) 全候选共享缓存＋未改动行
跳过第二次 lev。
变差>0 一律不收（任务书硬规则）。0 变差且 delta<0 才进组合。

守り字：N72 移交①成文执行——新旧字体两形并查（卽/即 由 SHINJITAI_MAP 反查）。
输出 eval/night73_sim.json / night73_sim.txt。
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
    # ---- 禁止词族（I の 毋かれ guard 毋 の分工補完：莫/勿 白文行）----
    "nakare_mokare":   {"kana": "なかれ", "repl": "莫かれ", "guard": ("莫",), "longer": (),
                        "tag": "なかれ→莫かれ guard 莫（I 毋かれ 同構・guard 分工；exp 莫かれ/莫し 両形）"},
    "nakare_mokare_b": {"kana": "なかれ", "repl": "莫", "guard": ("莫",), "longer": (),
                        "tag": "【字形比较】なかれ→莫（裸形）"},
    "nakare_mokare_s": {"kana": "なかれ", "repl": "莫し", "guard": ("莫",), "longer": (),
                        "tag": "【字形比较】なかれ→莫し"},
    "nakare_butsu":    {"kana": "なかれ", "repl": "勿かれ", "guard": ("勿",), "longer": (),
                        "tag": "なかれ→勿かれ guard 勿（同上・勿 白文行）"},
    "nakare_butsu_b":  {"kana": "なかれ", "repl": "勿", "guard": ("勿",), "longer": (),
                        "tag": "【字形比较】なかれ→勿（裸形）"},
    "nakare_butsu_s":  {"kana": "なかれ", "repl": "勿し", "guard": ("勿",), "longer": (),
                        "tag": "【字形比较】なかれ→勿し"},
    # ---- そく＝即（白文 即/卽 新旧両形并查）----
    "soku":            {"kana": "そく", "repl": "即ち", "guard": ("即", "卽"), "longer": (),
                        "tag": "そく→即ち（exp 即ち 12/12 均一；守り 即 9＋卽 3——新旧两形并查）"},
    # ---- 或いは（エンジンが題詞に余計な は を付ける＋或を仮名出力）----
    "aruiwa":          {"kana": "はあるいは", "repl": "或いは", "guard": ("或",), "longer": (),
                        "tag": "はあるいは→或いは（余計な は を含む仮名連鎖ごと或いはへ）"},
    "aruiwa_short":    {"kana": "はある", "repl": "或", "guard": ("或",), "longer": (),
                        "tag": "【字形比较】はある→或（短 key——「限りはある」等誤発火の疑い）"},
    # ---- 之（daigaku08 之其所…系列のみ）----
    "yuki":            {"kana": "ゆき", "repl": "之", "guard": ("之",), "longer": (),
                        "tag": "ゆき→之（之其所…系列 5 行のみ；got は ゆき を 5 行しか書かない）"},
    # ---- 其れ（は＝ particle＋それ → 其れ；J/I の それ と分工）----
    "hasore":          {"kana": "はそれ", "repl": "其れ", "guard": ("其",), "longer": (),
                        "tag": "はそれ→其れ（I それ→夫れ guard 夫 の分工・guard 其）"},
    "hasore_mo":       {"kana": "はそれ", "repl": "も其れ", "guard": ("其",), "longer": (),
                        "tag": "【字形比较】はそれ→も其れ（onoreosame 型は も を補う）"},
    # ---- 奈何（J の ごとし/ごとく guard 如 の分工補完・guard 奈）----
    "nanigotoshi":     {"kana": "何のごとし", "repl": "奈何", "guard": ("奈",), "longer": (),
                        "tag": "何のごとし→奈何（guard 奈＝J 如 之外の分工）"},
    "nanigotoku":      {"kana": "何のごとく", "repl": "奈何ぞ", "guard": ("奈",), "longer": (),
                        "tag": "何のごとく→奈何ぞ（同上）"},
    # ---- 予拒复核（N55 系・门不过即拒）----
    "moshi_waka":      {"kana": "もし", "repl": "若し", "guard": ("若",), "longer": (),
                        "tag": "【预拒复核】もし→若し guard 若（I は 如 のみ；若 行は未処理）"},
    "moshi":           {"kana": "もし", "repl": "若", "guard": ("若",), "longer": ("もしも", "もしや", "もしか"),
                        "tag": "もし→若（裸形＝exp 実書形 若、×2＋共有字論証；若し は kyugyu-2 1 変差で拒；長詞＝I 同款）"},
    "beki":            {"kana": "べき", "repl": "可き", "guard": ("可",), "longer": (),
                        "tag": "【预拒复核】べき→可き（F べし→可し/べく→可く の完結；N55 gap 再検）"},
    # ---- SHINJITAI 候補の拒案実証（文字置換を kana rule 机制で數值化）----
    "chin_jin":        {"kana": "陳", "repl": "陣", "guard": (), "longer": (),
                        "tag": "【预拒复核】陳→陣 無条件文字置換（kanbun.info 通假歸一の疑い；exp 側陳自書 39 回）"},
}
COMBO_ORDER = ["nakare_butsu", "soku", "aruiwa", "yuki", "hasore",
               "nanigotoshi", "nanigotoku", "moshi"]


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
    doc = json.load(open(os.path.join(EV, "night72_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序" % i
    rows8 = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    assert len(rows8) == 8165, "基线行数 %d != 8165" % len(rows8)
    doc4 = json.load(open(os.path.join(EV, "night72_results_4000.json"), encoding="utf-8"))
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

    # ==== 预检：歧义行取证（只读）====
    pr("")
    pr("== 预检 ==")
    # a) B2 歧义对（ことな→勿/莫・るべ→可）の具体行
    for w in ("ことな", "るべ"):
        pr("  [B2 %s] got が假名連鎖中に %s を含む行:" % (w, w))
        shown = 0
        for r in rows8:
            got, exp, _ = d0_cache[r["id"]]
            hb = norm(r["hakubun"])
            # 假名連鎖の部分一致（ことなかれ 等の部分は除外するため、
            # 直後が假名でない ことな のみ）
            for m in re.finditer(w, got):
                nxt = got[m.end():m.end() + 1]
                if nxt and re.match(r"[ぁ-ゖー]", nxt):
                    continue
                pr("    %s 守り有無=%s" % (r["id"], "莫" if "莫" in hb else ("勿" if "勿" in hb else "-")))
                pr("      got: %s" % got[:90])
                pr("      exp: %s" % exp[:90])
                shown += 1
                break
            if shown >= 6:
                break
    # b) 陳/陣 実数（SHINJITAI 候補の事前確認）
    exp_chin = sum(norm(r["expected_kakikudashi"]).count("陳") for r in rows8)
    got_chin = sum(d0_cache[r["id"]][0].count("陳") for r in rows8)
    exp_jin = sum(norm(r["expected_kakikudashi"]).count("陣") for r in rows8)
    got_jin = sum(d0_cache[r["id"]][0].count("陣") for r in rows8)
    pr("  [陳→陣] got 陳 %d / exp 陳 %d | got 陣 %d / exp 陣 %d | map 陳収録: %s" % (
        got_chin, exp_chin, got_jin, exp_jin, "陳" in SHINJITAI_MAP))
    chin_rows = [r["id"] for r in rows8 if "陳" in d0_cache[r["id"]][0]]
    pr("    got 陳 行: %s" % (", ".join(chin_rows[:12]) + (" …計%d行" % len(chin_rows) if len(chin_rows) > 12 else "")))
    # c) はそれ 行数と守り
    hs = [(r["id"], norm(r["hakubun"])) for r in rows8 if "はそれ" in d0_cache[r["id"]][0]]
    pr("  [はそれ] 行数 %d | 守り 其: %d 行" % (len(hs), sum(1 for _, hb in hs if "其" in hb)))
    # d) 何のごとし/ごとく × 守り奈
    for w in ("何のごとし", "何のごとく"):
        ws = [(r["id"], norm(r["hakubun"])) for r in rows8 if w in d0_cache[r["id"]][0]]
        pr("  [%s] 行数 %d | 守り 奈: %d 行" % (w, len(ws), sum(1 for _, hb in ws if "奈" in hb)))
    # e) そく の長詞（そく＋後続假名）有無
    soku_long = set()
    for r in rows8:
        got = d0_cache[r["id"]][0]
        for m in re.finditer("そく", got):
            tail = got[m.end():m.end() + 3]
            if tail and re.match(r"[ぁ-ゖー]", tail):
                soku_long.add(r["id"])
    pr("  [そく] そく＋後続假名の行（長詞の疑い）: %s" % (sorted(soku_long) or "無し"))
    # f) なかれ 危険走査：exp が仮名 なかれ を自書する行
    danger_nk = []
    for r in rows8:
        got, exp, _ = d0_cache[r["id"]]
        hb = norm(r["hakubun"])
        if "なかれ" in got and "なかれ" in exp and ("莫" in hb or "勿" in hb):
            danger_nk.append(r["id"])
    pr("  [なかれ] exp 仮名 なかれ 自書（guard 莫/勿）: %s" % (danger_nk or "無し"))
    # g) べき の got 假名連鎖統計
    beki_n = sum(1 for r in rows8 if "べき" in d0_cache[r["id"]][0])
    pr("  [べき] got べき 行数 %d" % beki_n)
    # h) もし の exp 自書走査
    danger_ms = []
    for r in rows8:
        got, exp, _ = d0_cache[r["id"]]
        hb = norm(r["hakubun"])
        if "もし" in got and "もし" in exp and "若" in hb:
            danger_ms.append(r["id"])
    pr("  [もし] exp 仮名 もし 自書（guard 若）: %s" % (danger_ms or "無し"))
    pr("")

    # ---- 多守り行检查 ----
    multi = []
    for r in rows8:
        hb = norm(r["hakubun"])
        got = d0_cache[r["id"]][0]
        if "なかれ" in got and "莫" in hb and "勿" in hb:
            multi.append(r["id"] + "(莫∧勿)")
        if "そく" in got and "即" in hb and "卽" in hb:
            multi.append(r["id"] + "(即∧卽)")
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
        if verdict == "収" and k in COMBO_ORDER:
            accepted.append(k)
        gate[k]["verdict"] = verdict
        pr("  %-16s 改写 %4d 行 better %4d worse %d delta %8.3f → %s (%.0fs) | %s" % (
            k, res["changed_entries"], res["better"], res["worse"], res["delta"],
            verdict, time.time() - t1, c["tag"]))
        for wd in res["worse_detail"][:4]:
            pr("      変差行 %s %d→%d" % (wd["id"], wd["old"], wd["new"]))
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
    out["baseline"] = "night72_results_8165.json"
    out["gate"] = gate
    out["accepted"] = accepted
    out["multi_guard_rows"] = multi
    out["idempotent_bad"] = bad
    out["precheck"] = {"exp_chin": exp_chin, "got_chin": got_chin,
                       "hasore_rows": len(hs), "danger_nakare": danger_nk,
                       "danger_moshi": danger_ms, "soku_long": sorted(soku_long)}
    out["combo_8165"] = {k: v for k, v in res8.items() if k != "changed_rows"}
    out["combo_4000"] = res4
    out["exact_8165"] = {"before": ex8[0], "after": ex8[1]}
    out["exact_4000"] = {"before": ex4[0], "after": ex4[1]}
    json.dump(out, open(os.path.join(EV, "night73_sim.json"), "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    json.dump(res8["changed_rows"], open(os.path.join(EV, "night73_combo_changed_rows.json"),
              "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night73_sim.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("")
    print("written: eval/night73_sim.json / night73_sim.txt / night73_combo_changed_rows.json")


if __name__ == "__main__":
    main()
