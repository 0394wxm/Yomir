# -*- coding: utf-8 -*-
"""night55_sim.py — N55 第二/三步：Rule G 候选离线模拟（基线 = day17 真机归档，F 已上线）。

候选来自 night55_mine.py 的解剖结果 + D17 §14 遗留（また→又 / べき / べから 复核）。
逐条真算 Levenshtein；变差>0 的候选一律不上线（任务书硬规则）。
输出 eval/night55_sim.json。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

MATA_LONGER = ("またたく", "またがり", "またがる", "またぎ", "またぐ",
               "またたき", "またしても", "またと", "またの")

CANDIDATES = {
    "mata_mata":  {"kana": "また", "repl": "又", "guard": ("又",), "longer": MATA_LONGER,
                   "tag": "また→又（白文含又）【D17遗留#1】"},
    "yuen":       {"kana": "ゆゑん", "repl": "所以", "guard": ("所以",), "longer": (),
                   "tag": "ゆゑん→所以（白文含所以）"},
    "ihayuru":    {"kana": "いはゆる", "repl": "所謂", "guard": ("所謂",), "longer": (),
                   "tag": "いはゆる→所謂（白文含所謂）"},
    "tagaini":    {"kana": "たがいに", "repl": "相", "guard": ("相",), "longer": (),
                   "tag": "たがいに→相（白文含相）"},
    "tameni":     {"kana": "ために", "repl": "為に", "guard": ("為",), "longer": (),
                   "tag": "ために→為に（白文含為）"},
    "beki":       {"kana": "べき", "repl": "可き", "guard": ("可",), "longer": (),
                   "tag": "べき→可き（白文含可）【D17遗留#3 复核】"},
    "bekara":     {"kana": "べから", "repl": "可から", "guard": ("可",), "longer": (),
                   "tag": "べから→可から（白文含可）【D17遗留#3 复核】"},
}


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


def run(rows, keys):
    better = worse = same = 0
    changed_entries = 0
    total_old = total_new = 0
    detail = []
    for r in rows:
        hb = norm(r["hakubun"])
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        d0 = lev(got, exp)
        new = got
        nchg = 0
        for k in keys:
            c = CANDIDATES[k]
            if hb and not any(g in hb for g in c["guard"]):
                continue
            new, n = apply_one(new, c["kana"], c["repl"], c["longer"])
            nchg += n
        d1 = lev(new, exp)
        total_old += d0
        total_new += d1
        if nchg:
            changed_entries += 1
        if d1 < d0:
            better += 1
        elif d1 > d0:
            worse += 1
            detail.append({"id": r["id"], "old": d0, "new": d1,
                           "got": got[:120], "exp": exp[:120], "newtext": new[:120]})
        else:
            same += 1
    n = len(rows)
    return {"entries": n, "changed_entries": changed_entries,
            "avg_old": round(total_old / n, 3), "avg_new": round(total_new / n, 3),
            "delta": round((total_new - total_old) / n, 3),
            "better": better, "worse": worse, "same": same, "worse_detail": detail[:30]}


def main():
    doc = json.load(open(os.path.join(EV, "day17_results_2000.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    base = sum(lev(norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"]))
               for r in rows) / len(rows)
    print("样本 %d 条 | 基线（F 已上线真机）avgDist %.3f" % (len(rows), base), flush=True)

    # expected 假名残留计数（预测变差方向）
    print("\n=== exp 假名残留（候选 kana 在 expected 里自身出现的次数）===", flush=True)
    for k, c in CANDIDATES.items():
        n = sum(norm(r["expected_kakikudashi"]).count(c["kana"]) for r in rows)
        print("  %-10s exp 里自身出现 %d 次" % (c["kana"], n), flush=True)

    out = {}
    print("\n=== 单条候选 ===", flush=True)
    print("%-34s %6s %8s %8s %8s %7s %7s" % ("候选", "改写条", "avg旧", "avg新", "Δ",
                                             "改善", "变差"), flush=True)
    for k in CANDIDATES:
        s = run(rows, [k])
        out[k] = s
        print("%-34s %6d %8.3f %8.3f %+8.3f %7d %7d"
              % (CANDIDATES[k]["tag"][:34], s["changed_entries"], s["avg_old"],
                 s["avg_new"], s["delta"], s["better"], s["worse"]), flush=True)
        if s["worse"]:
            for d in s["worse_detail"]:
                print("    !! 变差 %s %d->%d" % (d["id"], d["old"], d["new"]), flush=True)

    print("\n=== 组合（只含 0 变差候选按 live 链顺序：F 已在线上）===", flush=True)
    zero = [k for k in CANDIDATES if out[k]["worse"] == 0 and out[k]["changed_entries"] > 0]
    combos = [["mata_mata", "yuen", "ihayuru", "tagaini", "tameni"],
              [k for k in ("mata_mata", "yuen", "ihayuru", "tagaini") if k in zero] +
              (["tameni"] if "tameni" in zero else []),
              zero]
    for c in combos:
        s = run(rows, c)
        out["+".join(c)] = s
        print("%-46s 改写 %4d | Δ %+7.3f | 改善 %4d / 变差 %3d"
              % ("+".join(c)[:46], s["changed_entries"], s["delta"], s["better"], s["worse"]),
              flush=True)
        if s["worse"]:
            for d in s["worse_detail"][:6]:
                print("    !! 变差 %s %d->%d" % (d["id"], d["old"], d["new"]), flush=True)

    json.dump(out, open(os.path.join(EV, "night55_sim.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    print("\nwritten: eval/night55_sim.json", flush=True)


if __name__ == "__main__":
    main()
