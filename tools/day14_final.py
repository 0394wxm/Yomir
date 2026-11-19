# -*- coding: utf-8 -*-
"""day14_final.py — D14 第七步：候选规则的逐条核对 + 幂等 + 语料外安全网。

D11 的教训：汇总数字可能被实现 bug 骗过，必须逐条核对。
本脚本不信任任何汇总，直接从 1000 条原始结果重算：

  1. 逐条打印「改善/变差」明细，变差必须为空；
  2. 幂等：apply(apply(x)) == apply(x)；
  3. 语料外安全：白文没有对应汉字的现代和文/汉文句子，一个假名都不许动；
  4. 与既有规则叠加的顺序检查（Rule D 的 これ→之 不受影响）。

输出 eval/day14_final.json。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
sys.path.insert(0, ROOT)

# ---- 待上线的表（与 kundoku_rules.E 表保持一致） ----
E_TABLE = [
    ("みな", "皆", ("皆",)),
    ("すでに", "既", ("既", "旣")),
    ("なお", "猶", ("猶",)),
    ("あに", "豈", ("豈",)),
    ("ただ", "唯", ("唯",)),
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
    """Rule E：假名→汉字（kanbun.info 慣用表記），白文护栏。"""
    if not hakubun:
        return text
    hb = norm(hakubun)
    for kana, kanji, guard in E_TABLE:
        if any(g in hb for g in guard):
            text = text.replace(kana, kanji)
    return text


def main():
    with open(os.path.join(EV, "day11_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]

    better, worse, same, changed = 0, 0, 0, 0
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
            better_rows.append({"id": r["id"], "base": bd, "new": nd,
                                "got": got[:80], "new_s": new[:80], "exp": exp[:80]})
        elif nd > bd:
            worse += 1
            worse_rows.append({"id": r["id"], "base": bd, "new": nd,
                               "got": got[:120], "new_s": new[:120], "exp": exp[:120],
                               "hakubun": norm(r["hakubun"])[:80]})
        else:
            same += 1

    base = base_tot / len(rows)
    newavg = new_tot / len(rows)
    print("=== 逐条核对（%d 条） ===" % len(rows), flush=True)
    print("改写 %d | avgDist %.3f -> %.3f (%+.3f) | 改善 %d / 变差 %d / 持平 %d"
          % (changed, base, newavg, newavg - base, better, worse, same), flush=True)
    if worse_rows:
        print("\n!! 变差明细（必须为空）：", flush=True)
        for w in worse_rows:
            print("  %s %d->%d" % (w["id"], w["base"], w["new"]), flush=True)
            print("    白文: %s" % w["hakubun"], flush=True)
            print("    got : %s" % w["got"], flush=True)
            print("    new : %s" % w["new_s"], flush=True)
            print("    exp : %s" % w["exp"], flush=True)
    else:
        print("\n变差 0 条（逐条核对通过）", flush=True)

    print("\n=== 改善明细（前 12 条） ===", flush=True)
    for b in better_rows[:12]:
        print("  %-14s %2d->%2d" % (b["id"], b["base"], b["new"]), flush=True)

    # ---- 幂等 ----
    nonidem = 0
    for r in rows:
        got = norm(r["udkundoku_kakikudashi"])
        once = style_e(got, r["hakubun"])
        twice = style_e(once, r["hakubun"])
        if once != twice:
            nonidem += 1
    print("\n幂等：%d/%d 条二次应用无变化%s"
          % (len(rows) - nonidem, len(rows), "" if not nonidem else "  !! 非幂等"), flush=True)

    # ---- 语料外安全网 ----
    outside = [
        ("みんなで行く", "みんなで行く"),
        ("すでに終わった", "すでに終わった"),
        ("なお、そうする", "なお、そうする"),
        ("あに図らんや", "あに図らんや"),
        ("ただいま", "ただいま"),
        ("吾十有五而志于学", "吾十有五而志于学"),   # 白文无这五个汉字
        ("これを見よ", "これを見よ"),               # Rule D 的护栏也一并验证
    ]
    print("\n=== 语料外安全网（白文无对应汉字 → 必须一字不动） ===", flush=True)
    ok = True
    for hakubun, text in outside:
        out = style_e(text, hakubun)
        flag = "OK " if out == text else "!! "
        if out != text:
            ok = False
        print("  %s%s -> %s" % (flag, text, out), flush=True)

    # ---- 与 Rule D 叠加 ----
    print("\n=== 与既有规则叠加（Rule D 不受影响） ===", flush=True)
    from backend.kundoku_rules import style_fix_with_hakubun
    probe = "これを見る"
    d_only = style_fix_with_hakubun(probe, "此之見")
    print("  Rule D: %r -> %r" % (probe, d_only), flush=True)
    probe2 = "皆すでに之を知る"
    print("  叠加  : %r -> %r" % (probe2, style_e(style_fix_with_hakubun(probe2, "皆既之知"), "皆既之知")),
          flush=True)

    out = {"n": len(rows), "base_avg": round(base, 3), "new_avg": round(newavg, 3),
           "delta": round(newavg - base, 3), "changed": changed,
           "better": better, "worse": worse, "same": same,
           "worse_rows": worse_rows, "better_rows": better_rows,
           "idempotent": nonidem == 0, "outside_safe": ok,
           "table": [{"kana": k, "kanji": y, "guard": list(g)} for k, y, g in E_TABLE]}
    with open(os.path.join(EV, "day14_final.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nwritten: eval/day14_final.json", flush=True)


if __name__ == "__main__":
    main()
