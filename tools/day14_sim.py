# -*- coding: utf-8 -*-
"""day14_sim.py — D14 第五步：kana->kanji 候选的离线模拟（含护栏交叉表）。

对每个候选 (kana -> kanji) 做四种模拟：
  F 全替换          got.replace(kana, kanji)                 —— 无护栏
  G 白文护栏        hakubun 含 kanji（含异体）才替换          —— 语料外安全网
  G2 白文护栏+词界   同上，但要求 kana 前后不是假名（避免拆词）
  N 负例：不做任何改动（基线）

并打印交叉表：白文有无候选汉字 × got 有无候选假名。
若「白文无汉字 & got 有假名」= 0，则护栏在语料内零成本（与全替换等价）。

输出 eval/day14_sim.json。
"""
import json
import os
import re
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
sys.path.insert(0, ROOT)

KANA_RE = re.compile(r"[\u3041-\u309f\u30a0-\u30ff]")


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


# (标签, 假名, 汉字, 护栏可接受的写法（含异体字）)
CANDIDATES = [
    ("E1 すでに→既", "すでに", "既", ["既", "旣"]),
    ("E2 ただ→唯", "ただ", "唯", ["唯"]),
    ("E3 あに→豈", "あに", "豈", ["豈"]),
    ("E4 みな→皆", "みな", "皆", ["皆"]),
    ("E5 なかれ→勿", "なかれ", "勿", ["勿"]),
    ("E6 いずくんぞ→焉", "いずくんぞ", "焉", ["焉"]),
    ("E7 なお→猶", "なお", "猶", ["猶"]),
    ("E8 ごとし→如", "ごとし", "如", ["如"]),
]


def main():
    with open(os.path.join(EV, "day11_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]
    for r in rows:
        r["_got"] = norm(r["udkundoku_kakikudashi"])
        r["_exp"] = norm(r["expected_kakikudashi"])
        r["_base"] = lev(r["_got"], r["_exp"])
    base = sum(r["_base"] for r in rows) / len(rows)
    print("基线：%d 条 avgDist %.3f\n" % (len(rows), base), flush=True)

    results = []
    for label, kana, kanji, guard_forms in CANDIDATES:
        # 交叉表
        ct = {"hb_yes_got_yes": 0, "hb_yes_got_no": 0, "hb_no_got_yes": 0, "hb_no_got_no": 0}
        for r in rows:
            hb_has = any(g in norm(r["hakubun"]) for g in guard_forms)
            got_has = kana in r["_got"]
            ct[("hb_yes" if hb_has else "hb_no") + "_" + ("got_yes" if got_has else "got_no")] += 1

        def sim(fn, name):
            better = worse = same = changed = 0
            tot = 0
            worse_ids = []
            for r in rows:
                new = fn(r)
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
            print("  %-16s 改写 %3d | avg %6.3f (%+.3f) | 改善 %3d / 变差 %3d / 持平 %3d%s"
                  % (name, changed, avg, avg - base, better, worse, same,
                     ("  变差:%s" % ",".join(worse_ids[:5])) if worse else ""), flush=True)
            return {"name": name, "changed": changed, "avg": round(avg, 3),
                    "delta": round(avg - base, 3), "better": better, "worse": worse,
                    "same": same, "worse_ids": worse_ids[:20]}

        print("=== %s ===" % label, flush=True)
        print("  交叉表：白文有%s & 输出有%s = %d | 白文有 & 输出无 = %d | "
              "白文无 & 输出有 = %d | 都无 = %d"
              % (kanji, kana, ct["hb_yes_got_yes"], ct["hb_yes_got_no"],
                 ct["hb_no_got_yes"], ct["hb_no_got_no"]), flush=True)

        s_full = sim(lambda r, k=kana, y=kanji: r["_got"].replace(k, y), "F 全替换")

        def guarded(r, k=kana, y=kanji, g=guard_forms):
            if not any(x in norm(r["hakubun"]) for x in g):
                return r["_got"]
            return r["_got"].replace(k, y)

        s_guard = sim(guarded, "G 白文护栏")

        def guarded2(r, k=kana, y=kanji, g=guard_forms):
            # 额外要求：kana 左侧不是假名（避免把更长的假名词挖掉一块）
            if not any(x in norm(r["hakubun"]) for x in g):
                return r["_got"]
            out = []
            i = 0
            s = r["_got"]
            while True:
                j = s.find(k, i)
                if j < 0:
                    out.append(s[i:])
                    break
                prev_ch = s[j - 1] if j > 0 else ""
                if prev_ch and KANA_RE.match(prev_ch):
                    out.append(s[i:j + len(k)])
                else:
                    out.append(s[i:j] + y)
                i = j + len(k)
            return "".join(out)

        s_guard2 = sim(guarded2, "G2 护栏+词界")

        results.append({"label": label, "kana": kana, "kanji": kanji,
                        "guard_forms": guard_forms, "cross": ct,
                        "F": s_full, "G": s_guard, "G2": s_guard2})
        print(flush=True)

    with open(os.path.join(EV, "day14_sim.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n": len(rows), "base_avg": round(base, 3), "candidates": results},
                  f, ensure_ascii=False, indent=1)
    print("written: eval/day14_sim.json", flush=True)


if __name__ == "__main__":
    main()
