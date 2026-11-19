# -*- coding: utf-8 -*-
"""day17_combo.py — D17 第四步：只把「0 变差」的候选组合，逐条核对（不信任汇总）。

0 变差候选（来自 day17_sim.py）：
  また→亦た（白文含亦）    85 改写 / 0 变差
  いかん→如何（白文含何）  28 改写 / 0 变差
  べし→可し（白文含可）    49 改写 / 0 变差
  べく→可く（白文含可）     7 改写 / 0 变差

被拒绝（变差>0）：
  また→又（白文含又）  1 变差
  べき→可き（白文含可） 4 变差
  べから→可から（白文含可） 4 变差

本脚本：
  1. 组合四条，逐条重算 avgDist，打印改善/变差/持平与幂等性
  2. 打印全部变差条目（如果有）
  3. 语料外探针（现代和文不应被改）
  4. 白文护栏成本（白文无字却输出假名 → 必须 0 条被改）
输出 eval/day17_combo.json。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

# 与 day17_sim 相同定义，只保留 0 变差四条
RULE_F = [
    {"kana": "また", "repl": "亦た", "guard": ("亦",),
     "longer": ("またたく", "またがり", "またがる", "またぎ", "またぐ",
                "またたき", "またしても", "またと", "またの"),
     "tag": "また→亦た"},
    {"kana": "いかん", "repl": "如何", "guard": ("何",), "longer": (),
     "tag": "いかん→如何"},
    {"kana": "べし", "repl": "可し", "guard": ("可",), "longer": (),
     "tag": "べし→可し"},
    {"kana": "べく", "repl": "可く", "guard": ("可",), "longer": (),
     "tag": "べく→可く"},
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


def apply_rule(text, rule, hakubun):
    hb = norm(hakubun)
    if not any(g in hb for g in rule["guard"]):
        return text, 0
    kana, repl = rule["kana"], rule["repl"]
    longer = sorted(rule["longer"], key=len, reverse=True)
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


def apply_all(text, hakubun):
    total = 0
    for r in RULE_F:
        text, n = apply_rule(text, r, hakubun)
        total += n
    return text, total


def main():
    doc = json.load(open(os.path.join(EV, "day16_results_2000.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    print("=== Rule F 组合逐条核对（%d 条）===" % len(rows), flush=True)

    better = worse = same = 0
    changed = 0
    t_old = t_new = 0
    worse_detail = []
    per_rule = {r["tag"]: 0 for r in RULE_F}
    for r in rows:
        hb = norm(r["hakubun"])
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        d0 = lev(got, exp)
        new = got
        nchg = 0
        for rule in RULE_F:
            new, n = apply_rule(new, rule, hb)
            nchg += n
            per_rule[rule["tag"]] += n
        d1 = lev(new, exp)
        t_old += d0
        t_new += d1
        if nchg:
            changed += 1
        if d1 < d0:
            better += 1
        elif d1 > d0:
            worse += 1
            worse_detail.append({"id": r["id"], "old": d0, "new": d1,
                                 "exp": exp[:80], "got": got[:80], "newtext": new[:80]})
        else:
            same += 1

    n = len(rows)
    print("改写 %d 条 | avgDist %.3f -> %.3f (%+.3f) | 改善 %d / 变差 %d / 持平 %d"
          % (changed, t_old / n, t_new / n, (t_new - t_old) / n, better, worse, same),
          flush=True)
    print("各规则改写次数:", per_rule, flush=True)
    if worse_detail:
        print("\n!! 变差条目:", flush=True)
        for w in worse_detail:
            print("  %s  %d->%d" % (w["id"], w["old"], w["new"]), flush=True)
            print("     exp %s" % w["exp"], flush=True)
            print("     got %s" % w["got"], flush=True)
            print("     new %s" % w["newtext"], flush=True)
    else:
        print("变差 0 条 ✓", flush=True)

    # 幂等性
    nonidem = 0
    for r in rows[:400]:
        hb = norm(r["hakubun"])
        g = norm(r["udkundoku_kakikudashi"])
        a, _ = apply_all(g, hb)
        b, _ = apply_all(a, hb)
        if a != b:
            nonidem += 1
            if nonidem <= 3:
                print("  非幂等 %s: %r -> %r" % (r["id"], a[:60], b[:60]), flush=True)
    print("幂等性（前 400 条）: %s" % ("PASS" if nonidem == 0 else "FAIL %d" % nonidem),
          flush=True)

    # 语料外探针：现代和文/更长词
    probes = [
        ("また明日会いましょう", ""), ("またたく間に", ""), ("またがり", ""),
        ("またいとこ", ""), ("またしても失敗", ""), ("いかんせん", ""),
        ("いかんだ", ""), ("べき論", ""), ("べし", ""), ("べくして", ""),
        ("吾十有五而志于学", "吾十有五而志于学"),
        ("学而時習之", "学而時習之"),
    ]
    print("\n=== 语料外/护栏探针 ===", flush=True)
    probe_out = []
    for text, hb in probes:
        res, n = apply_all(text, hb)
        status = "不动" if res == text else "改动→%r" % res
        print("  %-22s 白文=%r  %s" % (text, hb[:10], status), flush=True)
        probe_out.append({"text": text, "hakubun": hb, "result": res, "changed": n})

    # 白文含字时必须改（正例）：输入是假名形态，白文有对应字 → 应改写
    pos = [("また", "亦"), ("いかん", "何"), ("べし", "可"), ("べく", "可")]
    print("\n=== 白文含字时必须改写（正例）===", flush=True)
    pos_out = []
    for kana_in, hb in pos:
        res, nc = apply_all(kana_in, hb)
        print("  %-8s 白文=%r -> %r (改写 %d)" % (kana_in, hb, res, nc), flush=True)
        pos_out.append({"in": kana_in, "hakubun": hb, "out": res, "n": nc})

    out = {
        "n": len(rows), "changed": changed,
        "avg_old": round(t_old / len(rows), 3), "avg_new": round(t_new / len(rows), 3),
        "delta": round((t_new - t_old) / len(rows), 3),
        "better": better, "worse": worse, "same": same,
        "worse_detail": worse_detail,
        "per_rule": per_rule,
        "idempotent_400": nonidem == 0,
        "probes": probe_out, "positives": pos_out,
        "rule_f": [{k: v for k, v in r.items() if k != "tag"} for r in RULE_F],
    }
    json.dump(out, open(os.path.join(EV, "day17_combo.json"), "w",
                        encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("\nwritten: eval/day17_combo.json", flush=True)


if __name__ == "__main__":
    main()
