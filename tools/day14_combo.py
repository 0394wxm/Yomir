# -*- coding: utf-8 -*-
"""day14_combo.py — D14 第六步：把 0 变差的候选合成一张表（一条规则）再模拟。

为什么合成：SHINJITAI_MAP 就是「一张映射表 = 一条规则」。若把 0 变差的
kana->kanji 对放进同一张表、每条都带白文护栏，就是 **一条** Rule E。

同时测试几个「不加护栏会变差」的对在白文护栏下是否安全（E5/E6/E8）。
输出 eval/day14_combo.json。
"""
import itertools
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")


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


# 条目：kana -> kanji, 白文护栏写法
PAIRS = {
    "E1": ("すでに", "既", ["既", "旣"]),
    "E2": ("ただ", "唯", ["唯"]),
    "E3": ("あに", "豈", ["豈"]),
    "E4": ("みな", "皆", ["皆"]),
    "E7": ("なお", "猶", ["猶"]),
    "E5": ("なかれ", "勿", ["勿"]),
    "E6": ("いずくんぞ", "焉", ["焉"]),
    "E8": ("ごとし", "如", ["如"]),
    "E9": ("また", "亦", ["亦"]),
}


def apply_table(text, hakubun, keys):
    hb = norm(hakubun)
    for k in keys:
        kana, kanji, guard = PAIRS[k]
        if not any(g in hb for g in guard):
            continue          # 白文没有这个汉字，这一条不动
        text = text.replace(kana, kanji)
    return text


def main():
    with open(os.path.join(EV, "day11_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]
    for r in rows:
        r["_got"] = norm(r["udkundoku_kakikudashi"])
        r["_exp"] = norm(r["expected_kakikudashi"])
        r["_base"] = lev(r["_got"], r["_exp"])
    base = sum(r["_base"] for r in rows) / len(rows)
    print("基线 avgDist %.3f（%d 条）\n" % (base, len(rows)), flush=True)

    def sim(keys, label):
        better = worse = same = changed = 0
        tot = 0
        worse_ids = []
        for r in rows:
            new = apply_table(r["_got"], r["hakubun"], keys)
            if new != r["_got"]:
                changed += 1
            d = lev(new, r["_exp"])
            tot += d
            if d < r["_base"]:
                better += 1
            elif d > r["_base"]:
                worse += 1
                worse_ids.append(r["id"])
            else:
                same += 1
        avg = tot / len(rows)
        print("  %-22s 改写 %3d | avg %6.3f (%+.3f) | 改善 %3d / 变差 %3d / 持平 %3d%s"
              % (label, changed, avg, avg - base, better, worse, same,
                 ("  worse=%s" % ",".join(worse_ids[:4])) if worse else ""), flush=True)
        return {"keys": list(keys), "label": label, "changed": changed,
                "avg": round(avg, 3), "delta": round(avg - base, 3),
                "better": better, "worse": worse, "same": same,
                "worse_ids": worse_ids[:20]}

    res = []
    print("=== 单条（复核） ===", flush=True)
    for k in PAIRS:
        res.append(sim([k], k + " " + PAIRS[k][0] + "→" + PAIRS[k][1]))

    print("\n=== 组合（只含 0 变差条目） ===", flush=True)
    combos = [
        (["E4"], "E4"),
        (["E4", "E1"], "E4+E1"),
        (["E4", "E1", "E7"], "E4+E1+E7"),
        (["E4", "E1", "E7", "E3"], "E4+E1+E7+E3"),
        (["E4", "E1", "E7", "E3", "E2"], "E4+E1+E7+E3+E2"),
        (["E4", "E1", "E7", "E3", "E2", "E9"], "…+E9 また→亦"),
    ]
    for keys, label in combos:
        res.append(sim(keys, label))

    print("\n=== 加护栏后是否救得回变差条目 ===", flush=True)
    for k in ["E5", "E6", "E8", "E9"]:
        res.append(sim([k], k + "（仅白文护栏）"))

    # 最后：全集（含所有）
    allk = list(PAIRS.keys())
    res.append(sim(allk, "全部 9 条（对照，预期有变差）"))

    with open(os.path.join(EV, "day14_combo.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n": len(rows), "base_avg": round(base, 3), "runs": res},
                  f, ensure_ascii=False, indent=1)
    print("\nwritten: eval/day14_combo.json", flush=True)


if __name__ == "__main__":
    main()
