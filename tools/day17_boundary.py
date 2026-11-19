# -*- coding: utf-8 -*-
"""day17_boundary.py — D17 第五步：Rule F 写进 backend 之后的逐条核对（离线，调真函数）。

与 day17_combo.py 的模拟结果必须逐位一致；不一致说明实现与模拟有偏差。
外加：与 Rule E 的叠加兼容、旧入口不受影响。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
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


def main():
    from backend.kundoku_rules import (style_kana_to_kanji_f, style_fix_with_hakubun,
                                       style_fix, F_KANA_TO_KANJI, E_KANA_TO_KANJI)

    print("=== 表结构 ===", flush=True)
    print("Rule E %d 条, Rule F %d 条" % (len(E_KANA_TO_KANJI), len(F_KANA_TO_KANJI)),
          flush=True)
    for kana, repl, guard in F_KANA_TO_KANJI:
        print("  F: %-6s -> %-5s guard=%s" % (kana, repl, guard), flush=True)

    doc = json.load(open(os.path.join(EV, "day16_results_2000.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]

    # 逐条：把 Rule E 后的输出（= day16 结果）过 Rule F 函数
    better = worse = same = 0
    changed = 0
    t_old = t_new = 0
    worse_detail = []
    for r in rows:
        hb = r["hakubun"]
        got = norm(r["udkundoku_kakikudashi"])   # 这是 Rule E 之后的真机输出
        exp = norm(r["expected_kakikudashi"])
        d0 = lev(got, exp)
        new = style_kana_to_kanji_f(got, hb)
        d1 = lev(new, exp)
        t_old += d0
        t_new += d1
        if new != got:
            changed += 1
        if d1 < d0:
            better += 1
        elif d1 > d0:
            worse += 1
            worse_detail.append({"id": r["id"], "old": d0, "new": d1})
        else:
            same += 1

    n = len(rows)
    print("\n=== 真函数逐条核对（2000 条）===", flush=True)
    print("改写 %d 条 | avgDist %.3f -> %.3f (%+.3f) | 改善 %d / 变差 %d / 持平 %d"
          % (changed, t_old / n, t_new / n, (t_new - t_old) / n, better, worse, same),
          flush=True)
    if worse_detail:
        print("!! 变差:", worse_detail[:10], flush=True)
    else:
        print("变差 0 条 ✓ 与模拟一致", flush=True)

    # 幂等
    nonidem = 0
    for r in rows:
        hb = r["hakubun"]
        g = norm(r["udkundoku_kakikudashi"])
        a = style_kana_to_kanji_f(g, hb)
        b = style_kana_to_kanji_f(a, hb)
        if a != b:
            nonidem += 1
            if nonidem <= 3:
                print("  非幂等 %s: %r -> %r" % (r["id"], a[:60], b[:60]), flush=True)
    print("幂等: %d/%d %s" % (n - nonidem, n, "PASS" if nonidem == 0 else "FAIL"),
          flush=True)

    # Rule E / F 叠加不互破
    print("\n=== Rule E × F 叠加测试 ===", flush=True)
    cases = [
        ("皆すでになおあにただ", "皆すでになおあにただ"),
        ("みなまたいかんべしべく", "亦何可可"),
        ("またも亦たすでに", "亦既"),
        ("いかんせん", ""),
        ("また明日", ""),
    ]
    for text, hb in cases:
        out = style_kana_to_kanji_f(text, hb)
        full = style_fix_with_hakubun(text, hb)
        print("  %-24s 白文=%-16r F→%-24r 全链→%r" % (text, hb[:8], out, full), flush=True)

    # 旧入口不受影响
    legacy = style_fix("みなまたいかん")
    print("\n旧 style_fix('みなまたいかん') = %r（应不动，无白文规则）" % legacy, flush=True)

    # 语料外探针：真实语义是「白文=用户输入」。现代和文输入里不含 亦/何/可，
    # 白文护栏会挡住；同时空白文按 Rule E 既有语义只做词界护栏（单独列出）。
    probes = [("また明日会いましょう", "また明日会いましょう"),
              ("またたく間に", "またたく間に"), ("またがり", "またがり"),
              ("またいとこ", "またいとこ"), ("またしても", "またしても"),
              ("またとない", "またとない"), ("またの機会", "またの機会"),
              ("いかんせん", "いかんせん"), ("いかんだ", "いかんだ"),
              ("べき論", "べき論"), ("べし", "べし"), ("べくして", "べくして"),
              ("吾十有五而志于学", "吾十有五而志于学")]
    print("\n=== 语料外探针（白文=输入本身，模拟真实调用）===", flush=True)
    probe_out = []
    for t, hb in probes:
        res = style_kana_to_kanji_f(t, hb)
        print("  %-22s -> %-22s %s" % (t, res, "不动" if res == t else "!!改动"),
              flush=True)
        probe_out.append({"in": t, "hakubun": hb, "out": res, "changed": res != t})

    print("\n=== 空白文（纯函数语义：只做词界护栏，与 Rule E 一致）===", flush=True)
    empty_out = []
    for t in ("また明日", "べし", "いかんだ"):
        res = style_kana_to_kanji_f(t, "")
        print("  %-14s -> %r" % (t, res), flush=True)
        empty_out.append({"in": t, "out": res})

    out = {
        "n": n, "changed": changed,
        "avg_old": round(t_old / n, 3), "avg_new": round(t_new / n, 3),
        "delta": round((t_new - t_old) / n, 3),
        "better": better, "worse": worse, "same": same,
        "worse_detail": worse_detail, "idempotent": nonidem == 0,
        "probes": probe_out, "probes_empty_hakubun": empty_out,
    }
    json.dump(out, open(os.path.join(EV, "day17_boundary.json"), "w",
                        encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("\nwritten: eval/day17_boundary.json", flush=True)


if __name__ == "__main__":
    main()
