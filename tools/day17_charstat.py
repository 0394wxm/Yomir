# -*- coding: utf-8 -*-
"""day17_charstat.py — D17 第一步：在 2000 条上重做字符级解剖。

沿用 D14 的两个角度，但语料换成 day16_results_2000.json（Rule E 之后、2000 条）：
  A. expected 多出来的汉字（exp - got），排除 D14 已上线的 5 个字
  B. D14 遗留候选 可/為/亦/不/如/若 的逐字上下文与 1:1 对应检查

只读，输出 eval/day17_charstat.json。
"""
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

SHIPPED_E = {"皆", "既", "旣", "猶", "豈", "唯"}
LEGACY = ["可", "為", "亦", "不", "如", "若", "与", "莫", "無", "非"]


def norm(s):
    return re.sub(r"\s+", "", s or "")


def is_kanji(c):
    return "\u3400" <= c <= "\u9fff"


def main():
    doc = json.load(open(os.path.join(EV, "day16_results_2000.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    print("样本 %d 条" % len(rows), flush=True)

    exp_c, got_c = collections.Counter(), collections.Counter()
    for r in rows:
        exp_c.update(norm(r["expected_kakikudashi"]))
        got_c.update(norm(r["udkundoku_kakikudashi"]))

    cand = []
    for c in set(exp_c) | set(got_c):
        if not is_kanji(c):
            continue
        e, g = exp_c.get(c, 0), got_c.get(c, 0)
        if e >= 8 and e > g:
            cand.append({"char": c, "exp": e, "got": g, "delta": e - g,
                         "shipped_E": c in SHIPPED_E})
    cand.sort(key=lambda x: -x["delta"])

    print("\n=== A. 汉字 expected>got（delta≥8）top 30 ===", flush=True)
    print("  %-4s %6s %6s %7s  %s" % ("字", "exp", "got", "delta", "D14已上线"), flush=True)
    for r in cand[:30]:
        print("  %-4s %6d %6d %7d  %s"
              % (r["char"], r["exp"], r["got"], r["delta"],
                 "★" if r["shipped_E"] else ""), flush=True)

    print("\n=== B. D14 遗留候选逐个 ===", flush=True)
    legacy_rows = []
    for c in LEGACY:
        e, g = exp_c.get(c, 0), got_c.get(c, 0)
        # 上下文：expected 里该字左右各一字
        ctx = collections.Counter()
        for r in rows:
            exp = norm(r["expected_kakikudashi"])
            for i, ch in enumerate(exp):
                if ch == c:
                    ctx[exp[max(0, i - 1):i + 2]] += 1
        # got 里该字的上下文
        gctx = collections.Counter()
        for r in rows:
            got = norm(r["udkundoku_kakikudashi"])
            for i, ch in enumerate(got):
                if ch == c:
                    gctx[got[max(0, i - 1):i + 2]] += 1
        legacy_rows.append({"char": c, "exp": e, "got": g, "delta": e - g,
                            "exp_ctx": ctx.most_common(8),
                            "got_ctx": gctx.most_common(8)})
        print("  %-3s exp %4d | got %4d | Δ %+5d" % (c, e, g, e - g), flush=True)
        print("      exp ctx: %s" % ", ".join("%r×%d" % k for k in ctx.most_common(6)),
              flush=True)
        print("      got ctx: %s" % ", ".join("%r×%d" % k for k in gctx.most_common(6)),
              flush=True)

    out = {"n": len(rows), "candidates": cand[:60], "legacy": legacy_rows}
    json.dump(out, open(os.path.join(EV, "day17_charstat.json"), "w",
                        encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("\nwritten: eval/day17_charstat.json", flush=True)


if __name__ == "__main__":
    main()
