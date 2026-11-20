# -*- coding: utf-8 -*-
"""night55_boundary.py — N55 第四步：Rule G 写进 backend 之后的逐条核对（离线，调真函数）。

与 night55_sim.py 的模拟必须逐位一致（136 条改写 / 21.116→20.916 / 127 改善 0 变差）；
外加幂等、F×G 叠加、旧入口、语料外探针。输出 eval/night55_boundary.json。
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
    from backend.kundoku_rules import (style_kana_to_kanji_g, style_fix_with_hakubun,
                                       style_fix, G_KANA_TO_KANJI, G_LONGER_WORDS,
                                       F_KANA_TO_KANJI, F_LONGER_WORDS, E_LONGER_WORDS)

    print("=== 表结构 ===", flush=True)
    print("Rule E %d 条, Rule F %d 条, Rule G %d 条" % (
        5, len(F_KANA_TO_KANJI), len(G_KANA_TO_KANJI)), flush=True)
    for kana, repl, guard in G_KANA_TO_KANJI:
        print("  G: %-8s -> %-4s guard=%s longer=%s"
              % (kana, repl, guard, G_LONGER_WORDS.get(kana)), flush=True)
    # また 长词表共享断言
    assert G_LONGER_WORDS["また"] is F_LONGER_WORDS["また"], "また 长词表应共享同一常量"
    assert G_LONGER_WORDS["また"] is not E_LONGER_WORDS.get("また", G_LONGER_WORDS["また"]) \
        or "また" not in E_LONGER_WORDS, "E 不该有 また"
    print("  また 长词表 F/G 共享同一常量 ✓", flush=True)

    doc = json.load(open(os.path.join(EV, "day17_results_2000.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]

    better = worse = same = changed = 0
    t_old = t_new = 0
    worse_detail = []
    per_rule = {"また→又": 0, "ゆゑん→所以": 0, "いはゆる→所謂": 0, "たがいに→相": 0}
    for r in rows:
        hb = r["hakubun"]
        got = norm(r["udkundoku_kakikudashi"])   # day17 真机输出 = F 之后的当前基线
        exp = norm(r["expected_kakikudashi"])
        d0 = lev(got, exp)
        new = style_kana_to_kanji_g(got, hb)
        d1 = lev(new, exp)
        t_old += d0
        t_new += d1
        if new != got:
            changed += 1
            for kana, repl, _ in G_KANA_TO_KANJI:
                if repl in new and repl not in got:
                    per_rule["%s→%s" % (kana, repl)] += 1
        if d1 < d0:
            better += 1
        elif d1 > d0:
            worse += 1
            worse_detail.append({"id": r["id"], "old": d0, "new": d1})
        else:
            same += 1

    n = len(rows)
    print("\n=== 真函数逐条核对（2000 条，G 挂在 F 后）===", flush=True)
    print("改写 %d 条 | avgDist %.3f -> %.3f (%+.3f) | 改善 %d / 变差 %d / 持平 %d"
          % (changed, t_old / n, t_new / n, (t_new - t_old) / n, better, worse, same),
          flush=True)
    print("各规则改写条数（按替换字首次出现口径）:", per_rule, flush=True)
    if worse_detail:
        print("!! 变差:", worse_detail[:10], flush=True)
    else:
        print("变差 0 条 ✓ 与模拟一致", flush=True)

    nonidem = 0
    for r in rows:
        hb = r["hakubun"]
        g = norm(r["udkundoku_kakikudashi"])
        a = style_kana_to_kanji_g(g, hb)
        b = style_kana_to_kanji_g(a, hb)
        if a != b:
            nonidem += 1
            if nonidem <= 3:
                print("  非幂等 %s: %r -> %r" % (r["id"], a[:60], b[:60]), flush=True)
    print("幂等: %d/%d %s" % (n - nonidem, n, "PASS" if nonidem == 0 else "FAIL"), flush=True)

    # F × G 叠加 / 词界 / 分工
    print("\n=== Rule F × G 叠加测试 ===", flush=True)
    cases = [
        ("またも亦たすでに", "亦既", "亦たも亦たすでに→全链 亦たも亦た既に（G 不该再动）"),
        ("みなまたいかんべしべく", "亦何可又", "白文含亦/何/可/又：亦た 先吃掉 また，G 的 又 规则不再命中"),
        ("また思いを寄す", "又", "白文只含又 → G 改 また→又； longer 词またがる 等不误伤"),
        ("またがる境界", "又", "またがる 是 longer 词 → 不动"),
        ("そのゆゑんは", "所以", "ゆゑん→所以"),
        ("いはゆる聖人", "所謂", "いはゆる→所謂"),
        ("たがいに守望", "相助", "たがいに→相"),
        ("ゆゑん", "無所", "白文不含所以 → 不动（护栏）"),
    ]
    for text, hb, note in cases:
        out = style_kana_to_kanji_g(text, hb)
        full = style_fix_with_hakubun(text, hb)
        print("  %-20s 白文=%-8r G→%-16r 全链→%r   # %s"
              % (text, hb[:8], out, full, note), flush=True)

    legacy = style_fix("みなまたいかんゆゑんたがいに")
    print("\n旧 style_fix('みなまたいかんゆゑんたがいに') = %r（应不动，E/F/G 都是白文规则）" % legacy,
          flush=True)

    # 语料外探针：真实语义「白文=用户输入」。现代和文不含 又/所以/所謂/相 → 护栏挡住
    probes = [("また明日会いましょう", "また明日会いましょう"),
              ("またたく間に", "またたく間に"), ("またがり", "またがり"),
              ("またの機会", "またの機会"), ("またとない", "またとない"),
              ("ゆゑん深し", "ゆゑん深し"), ("いはゆる古典", "いはゆる古典"),
              ("たがいに手を携う", "たがいに手を携う"), ("吾十有五而志于学", "吾十有五而志于学")]
    print("\n=== 语料外探针（白文=输入本身，模拟真实调用）===", flush=True)
    probe_out = []
    for t, hb in probes:
        res = style_kana_to_kanji_g(t, hb)
        print("  %-22s -> %-22s %s" % (t, res, "不动" if res == t else "!!改动"), flush=True)
        probe_out.append({"in": t, "hakubun": hb, "out": res, "changed": res != t})

    print("\n=== 空白文（纯函数语义：只做词界护栏，与 E/F 一致）===", flush=True)
    empty_out = []
    for t in ("また", "ゆゑん", "たがいに", "またがる"):
        res = style_kana_to_kanji_g(t, "")
        print("  %-10s -> %r" % (t, res), flush=True)
        empty_out.append({"in": t, "out": res})

    out = {
        "n": n, "changed": changed,
        "avg_old": round(t_old / n, 3), "avg_new": round(t_new / n, 3),
        "delta": round((t_new - t_old) / n, 3),
        "better": better, "worse": worse, "same": same,
        "per_rule": per_rule,
        "worse_detail": worse_detail, "idempotent": nonidem == 0,
        "probes": probe_out, "probes_empty_hakubun": empty_out,
    }
    json.dump(out, open(os.path.join(EV, "night55_boundary.json"), "w",
                        encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("\nwritten: eval/night55_boundary.json", flush=True)


if __name__ == "__main__":
    main()
