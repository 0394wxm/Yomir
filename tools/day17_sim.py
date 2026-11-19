# -*- coding: utf-8 -*-
"""day17_sim.py — D17 第三步：离线模拟候选改写（逐条算 avgDist 变化）。

对每个候选（假名串 → 词形，白文护栏字），在 2000 条上逐条：
  - 白文不含护栏字 → 不动
  - 白文含护栏字 且 输出含假名 → 替换
算：改写条数、平均距离变化、改善/变差条数。

支持多个候选叠加（按清单顺序）。输出 eval/day17_sim.json。
"""
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

# 候选：{kana, repl, guard(白文字), longer(更长词,命中则跳过), tag}
CANDIDATES = {
    "mata_also": {"kana": "また", "repl": "亦た", "guard": ("亦",),
                  "longer": ("またたく", "またがり", "またがる", "またぎ", "またぐ",
                             "またたき", "またしても", "またと", "またの"),
                  "tag": "また→亦た（白文含亦）"},
    "mata_mata": {"kana": "また", "repl": "又", "guard": ("又",),
                  "longer": ("またたく", "またがり", "またがる", "またぎ", "またぐ",
                             "またたき", "またしても", "またと", "またの"),
                  "tag": "また→又（白文含又）"},
    "ikani": {"kana": "いかん", "repl": "如何", "guard": ("何",), "longer": (),
              "tag": "いかん→如何（白文含何）"},
    "beki": {"kana": "べき", "repl": "可き", "guard": ("可",), "longer": (),
             "tag": "べき→可き（白文含可）"},
    "beshi": {"kana": "べし", "repl": "可し", "guard": ("可",), "longer": (),
              "tag": "べし→可し（白文含可）"},
    "bekara": {"kana": "べから", "repl": "可から", "guard": ("可",), "longer": (),
               "tag": "べから→可から（白文含可）"},
    "beku": {"kana": "べく", "repl": "可く", "guard": ("可",), "longer": (),
             "tag": "べく→可く（白文含可）"},
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


def apply_one(text, kana, repl, longer, guard_hb):
    """单条改写：白文护栏在调用方判断；这里只做词界。"""
    if not guard_hb:
        return text, 0
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


def run_combo(rows, keys):
    """返回 (改写数, 新avg, 改善, 变差, 持平, 逐条变化)"""
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
            has = any(g in hb for g in c["guard"])
            new, n = apply_one(new, c["kana"], c["repl"], c["longer"], has)
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
                           "exp": exp[:60], "got": got[:60], "newtext": new[:60]})
        else:
            same += 1
    n = len(rows)
    return {"entries": n, "changed_entries": changed_entries,
            "avg_old": round(total_old / n, 3), "avg_new": round(total_new / n, 3),
            "delta": round((total_new - total_old) / n, 3),
            "better": better, "worse": worse, "same": same, "worse_detail": detail[:20]}


def main():
    doc = json.load(open(os.path.join(EV, "day16_results_2000.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    print("样本 %d 条，基线 avgDist %.3f"
          % (len(rows), sum(lev(norm(r["udkundoku_kakikudashi"]),
                                norm(r["expected_kakikudashi"])) for r in rows) / len(rows)),
          flush=True)

    out = {}
    print("\n=== 单条候选 ===", flush=True)
    print("%-24s %6s %8s %8s %8s %7s %7s" % ("候选", "改写条", "avg旧", "avg新", "Δ",
                                             "改善", "变差"), flush=True)
    for k in CANDIDATES:
        s = run_combo(rows, [k])
        out[k] = s
        print("%-24s %6d %8.3f %8.3f %+8.3f %7d %7d"
              % (CANDIDATES[k]["tag"][:24], s["changed_entries"], s["avg_old"],
                 s["avg_new"], s["delta"], s["better"], s["worse"]), flush=True)

    print("\n=== 组合（逐条叠加）===", flush=True)
    combos = [
        ["ikani"],
        ["ikani", "beki"],
        ["ikani", "beki", "beshi"],
        ["ikani", "beki", "beshi", "bekara"],
        ["ikani", "beki", "beshi", "bekara", "beku"],
        ["mata_also"],
        ["mata_mata"],
        ["mata_also", "mata_mata"],
        ["ikani", "beki", "beshi", "bekara", "beku", "mata_also", "mata_mata"],
    ]
    for c in combos:
        s = run_combo(rows, c)
        out["+".join(c)] = s
        print("%-52s 改写 %4d | Δ %+7.3f | 改善 %4d / 变差 %3d"
              % ("+".join(c)[:52], s["changed_entries"], s["delta"], s["better"], s["worse"]),
              flush=True)

    json.dump(out, open(os.path.join(EV, "day17_sim.json"), "w",
                        encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("\nwritten: eval/day17_sim.json", flush=True)


if __name__ == "__main__":
    main()
