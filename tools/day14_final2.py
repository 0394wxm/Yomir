# -*- coding: utf-8 -*-
"""day14_final2.py — D14 第八步：按真实词形定表，逐条核对 + 幂等 + 语料外安全网。

day14_shape2.py 的结论（词形按 expected 统计，不是裸汉字替换）：
    みな   → 皆      (-0.058, 26 改善/0 变差)
    すでに → 既に    (-0.049, 23/0)
    なお   → 猶お    (-0.021, 20/0)
    あに   → 豈に    (-0.010, 10/0)
    ただ   → 唯だ    (-0.017, 16/0)

并加**词界护栏**：目标假名后面紧跟假名时不替换（保护 みなす/なおす/ただいま）。

本脚本做最终定案：逐条核对（变差必须 0）、幂等、语料外安全网。
输出 eval/day14_final2.json。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
sys.path.insert(0, ROOT)

KANA = re.compile(r"[\u3041-\u309f\u30a0-\u30ff]")

E_TABLE = [
    ("みな", "皆", ("皆",)),
    ("すでに", "既に", ("既", "旣")),
    ("なお", "猶お", ("猶",)),
    ("あに", "豈に", ("豈",)),
    ("ただ", "唯だ", ("唯",)),
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


def style_e(text, hakubun):
    if not hakubun:
        return text
    hb = norm(hakubun)
    for kana, repl, guard in E_TABLE:
        if not any(g in hb for g in guard):
            continue
        out = []
        i = 0
        n = len(kana)
        while True:
            j = text.find(kana, i)
            if j < 0:
                out.append(text[i:])
                break
            nxt = text[j + n] if j + n < len(text) else ""
            if nxt and KANA.match(nxt):
                out.append(text[i:j + n])       # 词界护栏：不动
            else:
                out.append(text[i:j] + repl)
            i = j + n
        text = "".join(out)
    return text


def main():
    with open(os.path.join(EV, "day11_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]

    better = worse = same = changed = 0
    base_tot = new_tot = 0
    worse_rows, better_rows = [], []
    for r in rows:
        got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        new = style_e(got, r["hakubun"])
        bd, nd = lev(got, exp), lev(new, exp)
        base_tot += bd
        new_tot += nd
        if new != got:
            changed += 1
        if nd < bd:
            better += 1
            better_rows.append({"id": r["id"], "base": bd, "new": nd})
        elif nd > bd:
            worse += 1
            worse_rows.append({"id": r["id"], "base": bd, "new": nd,
                               "got": got[:120], "new_s": new[:120], "exp": exp[:120],
                               "hakubun": norm(r["hakubun"])[:80]})
        else:
            same += 1

    base = base_tot / len(rows)
    newavg = new_tot / len(rows)
    print("=== 最终定案逐条核对（%d 条） ===" % len(rows), flush=True)
    print("改写 %d | avgDist %.3f -> %.3f (%+.3f) | 改善 %d / 变差 %d / 持平 %d"
          % (changed, base, newavg, newavg - base, better, worse, same), flush=True)
    if worse_rows:
        print("\n!! 变差明细（必须为空）：", flush=True)
        for w in worse_rows:
            print("  %s %d->%d  白文:%s" % (w["id"], w["base"], w["new"], w["hakubun"]), flush=True)
            print("    got: %s" % w["got"], flush=True)
            print("    new: %s" % w["new_s"], flush=True)
            print("    exp: %s" % w["exp"], flush=True)
    else:
        print("\n变差 0 条（逐条核对通过）", flush=True)

    nonidem = 0
    for r in rows:
        got = norm(r["udkundoku_kakikudashi"])
        once = style_e(got, r["hakubun"])
        if style_e(once, r["hakubun"]) != once:
            nonidem += 1
    print("幂等：%d/%d%s" % (len(rows) - nonidem, len(rows),
                             "" if not nonidem else "  !! 非幂等"), flush=True)

    outside = [
        ("みんなで行く", "みんなで行く"),
        ("すでに終わった", "すでに終わった"),
        ("なお、そうする", "なお、そうする"),
        ("あに図らんや", "あに図らんや"),
        ("ただいま", "ただいま"),
        ("之をみなす", "之をみなす"),
        ("なおす", "なおす"),
        ("吾十有五而志于学", "吾十有五而志于学"),
    ]
    print("\n=== 语料外/词界安全网 ===", flush=True)
    ok = True
    for hb, text in outside:
        out = style_e(text, hb)
        flag = "OK " if out == text else "!! "
        if out != text:
            ok = False
        print("  %s%-16s -> %s" % (flag, text, out), flush=True)

    print("\n=== 词界护栏的反例（白文有皆但词是みなす） ===", flush=True)
    out = style_e("之をみなす", "皆")
    print("  %r -> %r  %s" % ("之をみなす", out, "OK" if out == "之をみなす" else "!!"), flush=True)

    out = {"n": len(rows), "base_avg": round(base, 3), "new_avg": round(newavg, 3),
           "delta": round(newavg - base, 3), "changed": changed, "better": better,
           "worse": worse, "same": same, "worse_rows": worse_rows,
           "idempotent": nonidem == 0, "outside_safe": ok,
           "table": [{"kana": k, "repl": y, "guard": list(g)} for k, y, g in E_TABLE]}
    with open(os.path.join(EV, "day14_final2.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nwritten: eval/day14_final2.json", flush=True)


if __name__ == "__main__":
    main()
