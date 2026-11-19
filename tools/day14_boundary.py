# -*- coding: utf-8 -*-
"""day14_boundary.py — D14 修正步 3：词界护栏要「读到下一个假名串的边界」而不是见假名就挡。

问题（测试抓出）：`皆すでになおあにただ` 里 すでに 后面紧跟 な（なお 的 な），
朴素的「后接假名就挡」把 すでに 也挡掉了——相邻的两个词互相干扰。

正确判据：看目标假名之后的**假名连续段**是否是「一个已知的更长词」。
不含词表时，退一步用更保守的判据：
  - 只有当后接假名段**长度 >= 2** 且在语料里从未作为独立词出现时才挡；
  - 实际上「みなす」「なおす」「ただいま」「みんな」这些更长词都是**固定清单**，
    用清单判据最准确，不靠猜。

方案：显式登记「更长词」清单（数据来源：D14 的 got 邻接统计 + 常识词），
词界护栏 = 命中清单才挡。这样 すでに 后接 な 不会被误挡。

同时验证：清单判据与「长度>=2」判据在 1000 条上的差异。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

# 需要保护（不替换）的更长词：以候选假名开头，但不是该副词
LONGER_WORDS = {
    "みな": ("みなす", "みなれた", "みなれる", "みなし", "みなもと", "みなぎる", "みなみ"),
    "すでに": ("すでにして",),
    "なお": ("なおす", "なおさ", "なおし", "なおく", "なおざり"),
    "あに": ("あにす",),
    "ただ": ("ただいま", "ただす", "ただし", "ただちに", "ただならぬ"),
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


E_TABLE = [
    ("みな", "皆", ("皆",)),
    ("すでに", "既に", ("既", "旣")),
    ("なお", "猶お", ("猶",)),
    ("あに", "豈に", ("豈",)),
    ("ただ", "唯だ", ("唯",)),
]


def replace_lexicon(text, kana, repl):
    """命中 LONGER_WORDS 里的词就不替换；否则替换。"""
    longer = LONGER_WORDS.get(kana, ())
    out = []
    i = 0
    n = len(kana)
    while True:
        j = text.find(kana, i)
        if j < 0:
            out.append(text[i:])
            break
        tail = text[j:]
        # 找最长的命中（避免 みなす 先被 みな 吃掉）
        hit = None
        for w in sorted(longer, key=len, reverse=True):
            if tail.startswith(w):
                hit = w
                break
        if hit:
            out.append(text[i:j + len(hit)])
            i = j + len(hit)
        else:
            out.append(text[i:j] + repl)
            i = j + n
    return "".join(out)


def style_e(text, hakubun):
    hb = norm(hakubun) if hakubun else ""
    for kana, repl, guard in E_TABLE:
        if hb and not any(g in hb for g in guard):
            continue
        text = replace_lexicon(text, kana, repl)
    return text


def main():
    with open(os.path.join(EV, "day11_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]

    better = worse = same = changed = 0
    base_tot = new_tot = 0
    worse_rows = []
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
        elif nd > bd:
            worse += 1
            worse_rows.append({"id": r["id"], "base": bd, "new": nd,
                               "got": got[:120], "new_s": new[:120], "exp": exp[:120],
                               "hakubun": norm(r["hakubun"])[:80]})
        else:
            same += 1

    base = base_tot / len(rows)
    newavg = new_tot / len(rows)
    print("=== 清单词界护栏 逐条核对 ===", flush=True)
    print("改写 %d | avgDist %.3f -> %.3f (%+.3f) | 改善 %d / 变差 %d / 持平 %d"
          % (changed, base, newavg, newavg - base, better, worse, same), flush=True)
    for w in worse_rows:
        print("  !! %s %d->%d" % (w["id"], w["base"], w["new"]), flush=True)

    nonidem = 0
    for r in rows:
        got = norm(r["udkundoku_kakikudashi"])
        once = style_e(got, r["hakubun"])
        if style_e(once, r["hakubun"]) != once:
            nonidem += 1
            if nonidem <= 3:
                print("  非幂等: %s %r -> %r -> %r"
                      % (r["id"], got[:60], once[:60], style_e(once, r["hakubun"])[:60]),
                      flush=True)
    print("幂等：%d/%d%s" % (len(rows) - nonidem, len(rows),
                             "" if not nonidem else "  !! 非幂等"), flush=True)

    probes = [
        ("みんなで行く", "みんなで行く"), ("すでに終わった", "すでに終わった"),
        ("なお、そうする", "なお、そうする"), ("あに図らんや", "あに図らんや"),
        ("ただいま", "ただいま"), ("之をみなす", "之をみなす"),
        ("なおす", "なおす"), ("吾十有五而志于学", "吾十有五而志于学"),
        ("皆すでになおあにただ", "皆すでになおあにただ"),   # 无白文对应字
    ]
    print("\n=== 语料外/词界安全网 ===", flush=True)
    ok = True
    for hb, text in probes:
        out = style_e(text, hb)
        if out != text:
            ok = False
        print("  %s%-16s -> %s" % ("OK " if out == text else "!! ", text, out), flush=True)

    # 白文含五字时的完整替换（这就是 idempotence 失败的用例）
    print("\n=== 白文含五字：应该全部替换 ===", flush=True)
    full = style_e("皆すでになおあにただ", "皆既猶豈唯")
    print("  %r" % full, flush=True)
    full2 = style_e(full, "皆既猶豈唯")
    print("  二次: %r  %s" % (full2, "OK" if full2 == full else "!! 非幂等"), flush=True)

    with open(os.path.join(EV, "day14_boundary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"base_avg": round(base, 3), "new_avg": round(newavg, 3),
                   "delta": round(newavg - base, 3), "changed": changed,
                   "better": better, "worse": worse, "same": same,
                   "worse_rows": worse_rows, "idempotent": nonidem == 0,
                   "outside_safe": ok, "longer_words": LONGER_WORDS,
                   "full_probe": full},
                  f, ensure_ascii=False, indent=1)
    print("\nwritten: eval/day14_boundary.json", flush=True)


if __name__ == "__main__":
    main()
