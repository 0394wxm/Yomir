# -*- coding: utf-8 -*-
"""night72_sim.py — N72 Rule L 候选离线模拟＋收录判定＋组合双口径
（机制照抄 night69_sim.py：lev / apply_one / run / idempotent，基线 = night70 真机 8165）。

N72 性能注记：夜班机器被 N71（OCR+guwenbert 全量）占满，night69 式纯 Python lev
×24 遍实测卡 45 分钟（PID ~13% CPU）→ 三项加速（数值语义不变）：
  1) lev 优先用 Levenshtein C 库（pip --target .night72_deps 隔离目录，不碰全局
     site-packages）；启动时与纯 Python 参照实现在 200 个真实行对上断言逐位等价，
     import 失败自动回退纯 Python（数值相同，只差速度）。
  2) d0 = lev(got, exp) 全候选共享（基线同一条）→ 全局缓存只算一遍。
  3) run() 快速路径：规则未改动的行 d1 = d0（跳过第二次 lev）。
变差>0 一律不收（任务书硬规则）。0 变差且 delta<0（有改善）才进组合。
输出 eval/night72_sim.json / night72_sim.txt / night72_combo_changed_rows.json。
"""
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, ".night72_deps"))  # 隔离目录：Levenshtein/rapidfuzz
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


L_CANDIDATES = {
    "tsuhini":       {"kana": "つひに", "repl": "終に", "guard": ("終",), "longer": (),
                      "tag": "つひに→終に（N69 拒案 つひに→ついに 的真实词形翻案；守り 終 21/21）"},
    "izukunzo_an":   {"kana": "いずくんぞ", "repl": "安んぞ", "guard": ("安",), "longer": (),
                      "tag": "いずくんぞ→安んぞ（Rule I 焉护栏外残量；安んぞ⊂安くんぞ）"},
    "izukunzoaku":   {"kana": "いずくんぞ", "repl": "悪んぞ", "guard": ("惡", "悪"), "longer": (),
                      "tag": "いずくんぞ→悪んぞ（Xぞ族同型；守りは旧字 惡——新字体「悪」で探すと N69 為/爲 同款の 0 命中になる）"},
    "tada":          {"kana": "ただ", "repl": "但だ", "guard": ("但",),
                      "longer": ("ただいま", "ただす", "たださ", "ただし", "ただちに", "ただならぬ"),
                      "tag": "ただ→但だ（E 唯/I 惟 分工后的第三字形；exp 但だ 26/26；长词表＝E ただ 同款）"},
    "yue":           {"kana": "ゆえ", "repl": "由", "guard": ("由",), "longer": ("ゆえん", "ゆえに"),
                      "tag": "ゆえ→由（exp 由/由り/由る/由って 全由形，repl 由 每処恒 −2）"},
    "hajime":        {"kana": "はじめ", "repl": "始め", "guard": ("始",), "longer": (),
                      "tag": "はじめ→始め（守り 始 30/30；exp 始め 28/30）"},
    "hazaru_nari":   {"kana": "はざるなり", "repl": "わざるなり", "guard": (), "longer": (),
                      "tag": "はざるなり→わざるなり（接続拆分：排除 N69 唯一変差行 24shihin10-4=はざるとも）"},
    "hazaru_wo":     {"kana": "はざるを", "repl": "わざるを", "guard": (), "longer": (),
                      "tag": "はざるを→わざるを（同上）"},
    "hazaru_ka":     {"kana": "はざるか", "repl": "わざるか", "guard": (), "longer": (),
                      "tag": "はざるか→わざるか（同上）"},
    "hazaru_ni":     {"kana": "はざるに", "repl": "わざるに", "guard": (), "longer": (),
                      "tag": "はざるに→わざるに（同上）"},
    # ---- 预拒复核（N69/N70 拒案表；门不过即拒，留证存档）----
    "hazaru":        {"kana": "はざる", "repl": "わざる", "guard": (), "longer": (),
                      "tag": "【预拒复核】はざる→わざる（N69：1 変差 24shihin10-4）"},
    "tomo":          {"kana": "とも", "repl": "と", "guard": (), "longer": (),
                      "tag": "【预拒复核】とも→と（N69：1 変差 yoryoezu-1）"},
    "tomo_yoni":     {"kana": "とも", "repl": "与に", "guard": ("與", "与"), "longer": (),
                      "tag": "【预拒复核】とも→与に（guard 與/与——白文の旧字 舫…舊字「與」を初回プローブで見落としていた疑い）"},
    "gatame_gatameni": {"kana": "がため", "repl": "が為に", "guard": ("爲",), "longer": (),
                      "tag": "【预拒复核】がため→が為に guard 爲（N69 死因修正：守りは旧字 爲）"},
    "gatame_gatame": {"kana": "がため", "repl": "が為", "guard": ("爲",), "longer": (),
                      "tag": "【预拒复核】がため→が為（字形变体）"},
    "gatame_shini":  {"kana": "がため", "repl": "為に", "guard": ("爲",), "longer": (),
                      "tag": "【预拒复核】がため→為に（字形变体）"},
    "gatame_i":      {"kana": "がため", "repl": "為", "guard": ("爲",), "longer": (),
                      "tag": "【预拒复核】がため→為（字形变体）"},
    "bekaramazu":    {"kana": "べからず", "repl": "可からず", "guard": ("可",), "longer": (),
                      "tag": "【预拒复核】べからず→可からず（N68 §8-3 结构性 gap：exp 自写仮名 5 行）"},
    "bezu":          {"kana": "べず", "repl": "可ず", "guard": ("可",), "longer": (),
                      "tag": "【预拒复核】べず→可ず（目標 0・守り 0）"},
}
COMBO_ORDER = ["tsuhini", "izukunzo_an", "izukunzoaku", "tada", "yue", "hajime",
               "gatame_i", "hazaru_nari", "hazaru_wo"]


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
    """d0_cache: {id: (got, exp, d0)}——基线 lev 全候选共享，只算一遍。
    快速路径：规则未改动的行 d1 = d0（跳过第二次 lev）。"""
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
    """night58/64/68/69 同款两遍法：第二遍结果与第一遍不同 → 非幂等。（无 lev，纯串比较）"""
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
    doc = json.load(open(os.path.join(EV, "night70_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序" % i
    rows8 = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    assert len(rows8) == 8165, "基线行数 %d != 8165" % len(rows8)
    doc4 = json.load(open(os.path.join(EV, "night70_results_4000.json"), encoding="utf-8"))
    rows4 = doc4["results"]
    assert [r["id"] for r in rows4] == [r["id"] for r in rows8[:4000]], "4000/8165 前 4000 行不同序"
    for a, b in zip(rows4, rows8[:4000]):
        assert norm(a["udkundoku_kakikudashi"]) == norm(b["udkundoku_kakikudashi"]), \
            "4000/8165 got 不一致: %s" % a["id"]

    # repl 终字形断言：响应端 ortho=True 的 normalize_shinjitai 不得再改 repl
    from backend.kundoku_rules import normalize_shinjitai
    for k, c in L_CANDIDATES.items():
        assert normalize_shinjitai(c["repl"]) == c["repl"], \
            "repl 非终字形（SHINJITAI 会再改）: %s %s" % (k, c["repl"])

    # ---- d0 全局缓存（含 C 库与纯 Python 参照的等价性抽查）----
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

    # ---- 多守り行检查（表順先勝の意味論锁用）----
    multi = []
    for r in rows8:
        hb = norm(r["hakubun"])
        if "いずくんぞ" in norm(r["udkundoku_kakikudashi"]) and "安" in hb and "悪" in hb:
            multi.append(r["id"])
        if "ただ" in norm(r["udkundoku_kakikudashi"]) and "但" in hb and ("唯" in hb or "惟" in hb):
            multi.append(r["id"] + "(但∧唯/惟)")
    pr("多守り行（L 表内 guard 共存）: %s" % (multi or "無し"))
    pr("")

    # ---- 单条 0 变差门 ----
    pr("== 单条 0 変差門 ==")
    accepted = []
    gate = {}
    order = COMBO_ORDER + ["hazaru", "tomo", "tomo_yoni", "gatame_gatameni",
                           "gatame_gatame", "gatame_shini", "bekaramazu", "bezu"]
    for k in order:
        t1 = time.time()
        c = L_CANDIDATES[k]
        res = run(rows8, [(c["kana"], c["repl"], c["guard"], c["longer"])], d0_cache)
        gate[k] = {"tag": c["tag"], "changed": res["changed_entries"],
                   "better": res["better"], "worse": res["worse"],
                   "delta": res["delta"],
                   "worse_detail": res["worse_detail"][:6]}
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
    pr("収録候補: %s" % ",".join(accepted))
    pr("（収録数 %d / 门槛 3）" % len(accepted))

    # ---- 组合：收录候补全量（順序=COMBO_ORDER）----
    combo = [(L_CANDIDATES[k]["kana"], L_CANDIDATES[k]["repl"],
              L_CANDIDATES[k]["guard"], L_CANDIDATES[k]["longer"]) for k in accepted]
    pr("\n== 组合（%d 条）幂等验证 ==" % len(combo))
    bad = idempotent(rows8, combo, d0_cache)
    pr("  idempotent bad = %d（0 で冪等）" % bad)

    pr("\n== 组合双口径离线真算 ==")
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
    pr("\n  变差行明细（8165）: %s" % ("無し" if res8["worse"] == 0 else ""))
    for wd in res8["worse_detail"][:10]:
        pr("    %s %d→%d | got %s | exp %s | new %s" % (
            wd["id"], wd["old"], wd["new"], wd["got"][:40], wd["exp"][:40], wd["newtext"][:40]))

    out["lev_impl"] = _LEV_IMPL
    out["baseline"] = "night70_results_8165.json"
    out["gate"] = gate
    out["accepted"] = accepted
    out["multi_guard_rows"] = multi
    out["idempotent_bad"] = bad
    out["combo_8165"] = {k: v for k, v in res8.items() if k != "changed_rows"}
    out["combo_4000"] = res4
    out["exact_8165"] = {"before": ex8[0], "after": ex8[1]}
    out["exact_4000"] = {"before": ex4[0], "after": ex4[1]}
    json.dump(out, open(os.path.join(EV, "night72_sim.json"), "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    json.dump(res8["changed_rows"], open(os.path.join(EV, "night72_combo_changed_rows.json"),
              "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night72_sim.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("\nwritten: eval/night72_sim.json / night72_sim.txt / night72_combo_changed_rows.json")


if __name__ == "__main__":
    main()
