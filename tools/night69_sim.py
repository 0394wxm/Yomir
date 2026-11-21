# -*- coding: utf-8 -*-
"""night69_sim.py — N69 Rule K 候选离线模拟＋收录判定＋组合真跑双口径
（机制照抄 night68_sim.py：lev / apply_one / run / idempotent，基线 = night68 真机 8165）。

变差>0 一律不收（任务书硬规则）。0 变差且 delta<0（有改善）才进组合；
delta==0（无益）或 exp 无目标字形（副产物改善）拒。全部候选单跑 → 0 变差门 →
收录组合 → 组合幂等验证 → 双口径（4000/8165）真跑（改写行数/改善/变差/avgDist/exact
前后 + ⑯ 偏科 shibu02 长句段与漢詩段（url /syubu/）分开）。
backend 上线移交下一夜（kundoku_rules.py 不在本夜允许清单）。
输出 eval/night69_sim.json / night69_sim.txt / night69_combo_changed_rows.json。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

# (kana, repl, guard, longer, tag)——guard=() は無条件（night68_sim は guard 必非空だったため
# run 側で guard 空を明示支持するよう拡張：guard が空なら白文を問わず適用）
KANA_CANDIDATES = {
    "hite":       {"kana": "ひて", "repl": "いて", "guard": (), "longer": (),
                   "tag": "ひて→いて（歴史的→現代仮名遣い；Rule A ふ→う 同型）"},
    "hete":       {"kana": "へて", "repl": "えて", "guard": (), "longer": (),
                   "tag": "へて→えて（同族）"},
    "hazu":       {"kana": "はず", "repl": "わず", "guard": (), "longer": (),
                   "tag": "はず→わず（同族：言はず→言わず）"},
    "hazaru":     {"kana": "はざる", "repl": "わざる", "guard": (), "longer": (),
                   "tag": "はざる→わざる（同族：能はざる→能わざる）"},
    "hezu":       {"kana": "へず", "repl": "えず", "guard": (), "longer": (),
                   "tag": "へず→えず（同族）"},
    "iyashikumo": {"kana": "いやしくも", "repl": "苟くも", "guard": (), "longer": (),
                   "tag": "いやしくも→苟くも（kana→漢字，N62 §9-1 型；exp 全写苟く系）"},
    "nanzo_kan":  {"kana": "なんぞ", "repl": "盍ぞ", "guard": ("盍",), "longer": (),
                   "tag": "なんぞ→盍ぞ（白文含盍；Xぞ族拆分）"},
    "nanzo_gei":  {"kana": "なんぞ", "repl": "奚ぞ", "guard": ("奚",), "longer": (),
                   "tag": "なんぞ→奚ぞ（白文含奚；奚=族名混用リスク）"},
    "nanzo_katsu": {"kana": "なんぞ", "repl": "曷ぞ", "guard": ("曷",), "longer": (),
                   "tag": "なんぞ→曷ぞ（白文含曷；曷んぞ/曷くに 混写リスク）"},
    "tomo":       {"kana": "とも", "repl": "と", "guard": (), "longer": (),
                   "tag": "とも→と（exp 全库 0 行含とも→目標一意）"},
    "gatame":     {"kana": "がため", "repl": "が為に", "guard": ("為",), "longer": (),
                   "tag": "がため→が為に（白文含為）【N68 R_gatame 预拒复核】"},
    "tsuhini":    {"kana": "つひに", "repl": "ついに", "guard": (), "longer": (),
                   "tag": "つひに→ついに（exp 目標字形なし——取证用，预期拒）"},
}
COMBO_ORDER = ["hite", "hete", "hazu", "hazaru", "hezu", "iyashikumo",
               "nanzo_kan", "nanzo_gei", "nanzo_katsu", "tomo", "gatame"]


def norm(s):
    return re.sub(r"\s+", "", s or "")


def lev(a, b):
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


def run(rows, kana_rules, keep_changed=False):
    better = worse = same = 0
    changed_entries = 0
    total_old = total_new = 0
    worse_detail = []
    changed_rows = []
    segs = {"s4000": [0, 0, 0], "s3908": [0, 0, 0], "s257": [0, 0, 0],
            "shibu02": [0, 0, 0], "kansi": [0, 0, 0]}
    for idx, r in enumerate(rows):
        hb = norm(r["hakubun"])
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        d0 = lev(got, exp)
        new = got
        nchg = 0
        for kana, repl, guard, longer in kana_rules:
            if guard and not any(g in hb for g in guard):
                continue
            new, n = apply_one(new, kana, repl, longer)
            nchg += n
        d1 = lev(new, exp)
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
                changed_rows.append({"id": r["id"], "old_dist": d0, "new_dist": d1,
                                     "old_text": got, "new_text": new, "expected": exp})
        if d1 < d0:
            better += 1
        elif d1 > d0:
            worse += 1
            worse_detail.append({"id": r["id"], "old": d0, "new": d1,
                                 "got": got[:120], "exp": exp[:120], "newtext": new[:120]})
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


def idempotent(rows, kana_rules):
    """night58/64/68 同款两遍法：第二遍结果与第一遍不同 → 非幂等。"""
    bad = 0
    for r in rows:
        hb = norm(r["hakubun"])
        got = norm(r["udkundoku_kakikudashi"])
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


def exact_count(rows, kana_rules):
    before = after = 0
    for r in rows:
        hb = norm(r["hakubun"])
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        new = got
        for kana, repl, guard, longer in kana_rules:
            if guard and not any(g in hb for g in guard):
                continue
            new, _ = apply_one(new, kana, repl, longer)
        before += got == exp
        after += new == exp
    return before, after


def main():
    doc = json.load(open(os.path.join(EV, "night68_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序" % i
    rows8 = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    doc4 = json.load(open(os.path.join(EV, "night68_results_4000.json"), encoding="utf-8"))
    rows4 = doc4["results"]
    assert [r["id"] for r in rows4] == [r["id"] for r in rows8[:4000]], "4000/8165 前 4000 行不同序"
    for a, b in zip(rows4, rows8[:4000]):
        assert norm(a["udkundoku_kakikudashi"]) == norm(b["udkundoku_kakikudashi"]), \
            "4000/8165 got 不一致: %s" % a["id"]

    out = {}
    lines = []

    def pr(s=""):
        lines.append(s)
        print(s, flush=True)

    pr("样本 8165 条 | 基线 avgDist %.3f" % (sum(lev(norm(r["udkundoku_kakikudashi"]),
       norm(r["expected_kakikudashi"])) for r in rows8) / len(rows8)))

    # ---- 单条 0 变差门 ----
    pr("\n== 单条 0 変差門 ==")
    accepted = []
    gate = {}
    for k in COMBO_ORDER + ["tsuhini"]:
        c = KANA_CANDIDATES[k]
        res = run(rows8, [(c["kana"], c["repl"], c["guard"], c["longer"])])
        gate[k] = {"tag": c["tag"], "changed": res["changed_entries"],
                   "better": res["better"], "worse": res["worse"],
                   "delta": res["delta"],
                   "worse_detail": res["worse_detail"][:6]}
        verdict = "収" if (res["worse"] == 0 and res["delta"] < 0) else (
            "拒（変差 %d）" % res["worse"] if res["worse"] else "拒（無益/無目標）")
        if verdict == "収":
            accepted.append(k)
        gate[k]["verdict"] = verdict
        pr("  %-12s 改写 %4d 行 better %4d worse %d delta %8.3f → %s | %s" % (
            k, res["changed_entries"], res["better"], res["worse"], res["delta"],
            verdict, c["tag"]))
        for wd in res["worse_detail"][:4]:
            pr("      変差行 %s %d→%d" % (wd["id"], wd["old"], wd["new"]))
    pr("収録候補: %s" % ",".join(accepted))

    # ---- 组合：收录候补全量（互斥 guard は白文で排他、顺序=COMBO_ORDER）----
    combo = [(KANA_CANDIDATES[k]["kana"], KANA_CANDIDATES[k]["repl"],
              KANA_CANDIDATES[k]["guard"], KANA_CANDIDATES[k]["longer"]) for k in accepted]
    pr("\n== 组合（%d 条）幂等验证 ==" % len(combo))
    bad = idempotent(rows8, combo)
    pr("  idempotent bad = %d（0 で冪等）" % bad)

    pr("\n== 组合双口径真跑 ==")
    res8 = run(rows8, combo, keep_changed=True)
    ex8 = exact_count(rows8, combo)
    res4 = run(rows4, combo)
    ex4 = exact_count(rows4, combo)
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

    out["gate"] = gate
    out["accepted"] = accepted
    out["idempotent_bad"] = bad
    out["combo_8165"] = {k: v for k, v in res8.items() if k != "changed_rows"}
    out["combo_4000"] = res4
    out["exact_8165"] = {"before": ex8[0], "after": ex8[1]}
    out["exact_4000"] = {"before": ex4[0], "after": ex4[1]}
    json.dump(out, open(os.path.join(EV, "night69_sim.json"), "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    json.dump(res8["changed_rows"], open(os.path.join(EV, "night69_combo_changed_rows.json"),
              "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night69_sim.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("\nwritten: eval/night69_sim.json / night69_sim.txt / night69_combo_changed_rows.json")


if __name__ == "__main__":
    main()
