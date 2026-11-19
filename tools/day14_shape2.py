# -*- coding: utf-8 -*-
"""day14_shape2.py — D14 修正步 2：按 expected 的真实词形做变体模拟。

day14_shape.py 的结论（期望词形，不是「汉字裸替」）：
    既 后接「に」20/25  → すでに → **既に**
    猶 后接「お」29/33  → なお   → **猶お**
    豈 后接「に」10/10  → あに   → **豈に**
    唯 后接「だ」16/17  → ただ   → **唯だ**
    皆 裸 31/36         → みな   → **皆**（少数是 皆な）

同时对每个变体测「词界护栏」：目标假名后面紧跟假名时不替换
（保护 みなす / なおす / ただいま / すでにず 这类更长的词）。

输出 eval/day14_shape2.json。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

KANA = re.compile(r"[\u3041-\u309f\u30a0-\u30ff]")

COMBOS = [
    # (kana, 汉字, 变体替换串, 白文护栏写法)
    ("みな", "皆", "皆", ("皆",)),
    ("みな", "皆", "皆な", ("皆",)),
    ("すでに", "既", "既", ("既", "旣")),
    ("すでに", "既", "既に", ("既", "旣")),
    ("なお", "猶", "猶", ("猶",)),
    ("なお", "猶", "猶お", ("猶",)),
    ("あに", "豈", "豈", ("豈",)),
    ("あに", "豈", "豈に", ("豈",)),
    ("ただ", "唯", "唯", ("唯",)),
    ("ただ", "唯", "唯だ", ("唯",)),
]


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


def replace_guarded(text, kana, repl, boundary):
    """把 kana 换成 repl；boundary=True 时要求后继不是假名（词界护栏）。"""
    out = []
    i = 0
    n = len(kana)
    while True:
        j = text.find(kana, i)
        if j < 0:
            out.append(text[i:])
            break
        nxt = text[j + n] if j + n < len(text) else ""
        if boundary and nxt and KANA.match(nxt):
            out.append(text[i:j + n])
        else:
            out.append(text[i:j] + repl)
        i = j + n
    return "".join(out)


def main():
    with open(os.path.join(EV, "day11_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]
    for r in rows:
        r["_got"] = norm(r["udkundoku_kakikudashi"])
        r["_exp"] = norm(r["expected_kakikudashi"])
        r["_hb"] = norm(r["hakubun"])
        r["_base"] = lev(r["_got"], r["_exp"])
    base = sum(r["_base"] for r in rows) / len(rows)
    print("基线 avgDist %.3f\n" % base, flush=True)

    def sim(kana, repl, guard_forms, boundary):
        better = worse = same = changed = 0
        tot = 0
        worse_ids = []
        for r in rows:
            if not any(g in r["_hb"] for g in guard_forms):
                new = r["_got"]
            else:
                new = replace_guarded(r["_got"], kana, repl, boundary)
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
        print("  %s->%-5s %s | 改写 %3d | avg %6.3f (%+.3f) | 改善 %3d / 变差 %3d%s"
              % (kana, repl, "词界" if boundary else "    ", changed, avg, avg - base,
                 better, worse, ("  worse=%s" % ",".join(worse_ids[:4])) if worse else ""),
              flush=True)
        return {"kana": kana, "repl": repl, "boundary": boundary, "changed": changed,
                "avg": round(avg, 3), "delta": round(avg - base, 3),
                "better": better, "worse": worse, "worse_ids": worse_ids[:20]}

    print("=== 变体模拟（白文护栏固定开启） ===", flush=True)
    out = []
    for kana, kanji, repl, guard in COMBOS:
        out.append(sim(kana, repl, guard, False))
    print("\n=== 同上 + 词界护栏 ===", flush=True)
    for kana, kanji, repl, guard in COMBOS:
        out.append(sim(kana, repl, guard, True))

    with open(os.path.join(EV, "day14_shape2.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"base_avg": round(base, 3), "variants": out}, f, ensure_ascii=False, indent=1)
    print("\nwritten: eval/day14_shape2.json", flush=True)


if __name__ == "__main__":
    main()
