# -*- coding: utf-8 -*-
"""night24_punct_sim.py — Night 24：punct 前置「而して」的细分实验（Night 22 §6.2 顺延）。

数据：eval/night22_results_full.json（当前生产线 500 条）。
问题：punct 前置 50 处里 42 处多余、8 处需要。表面信号能否切分？
候选假设：前置标点种类（、 vs 。 vs 其它）与 want 的关系。
只做离线模拟；数据不支持就不上线（如实写负结果）。
"""
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(s):
    return re.sub(r"\s+", "", s)


def lev(a, b):
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def main():
    with open(os.path.join(ROOT, "eval", "night22_results_full.json"), encoding="utf-8") as f:
        results = json.load(f)["results"]

    # 1) punct 前置的而して：按具体标点种类分组
    rows = []
    for r in results:
        out = r["udkundoku_kakikudashi"]
        want = "而して" in r["expected_kakikudashi"]
        for m in re.finditer("而して", out):
            i = m.start()
            prev = out[i - 1] if i > 0 else ""
            if prev and not re.match(r"[ぁ-ゖァ-ヺ]", prev) and not ("\u3400" <= prev <= "\u9fff"):
                rows.append({"id": r["id"], "prev": prev, "want": want,
                             "out": out, "exp": r["expected_kakikudashi"],
                             "start": i, "end": i + 3})
    print("=== punct 前置而して：%d 处 ===" % len(rows))
    cnt = Counter((r["prev"], r["want"]) for r in rows)
    for (prev, want), n in sorted(cnt.items()):
        print("  prev=%r want=%-5s %3d" % (prev, want, n))

    # 2) 按前置标点种类模拟删除
    def sim(pred, label):
        imp = wor = fla = 0
        touched_keep = 0
        det = []
        for r in results:
            out, exp = r["udkundoku_kakikudashi"], r["expected_kakikudashi"]
            new = []
            i = 0
            changed = False
            while i < len(out):
                if out.startswith("而して", i) and pred(out, i):
                    new.append("")
                    i += 3
                    changed = True
                    continue
                new.append(out[i])
                i += 1
            if not changed:
                continue
            new = "".join(new)
            d_o = lev(norm(out), norm(exp))
            d_n = lev(norm(new), norm(exp))
            if "而して" in r["expected_kakikudashi"] and new != out:
                touched_keep += 1
            det.append((r["id"], d_o, d_n, out[max(0, out.find("而して") - 1):out.find("而して") + 5]))
            if d_n < d_o:
                imp += 1
            elif d_n > d_o:
                wor += 1
            else:
                fla += 1
        tot = sum(d_o - d_n for _i, d_o, d_n, _s in det)
        print("\n=== %s ===" % label)
        print("  触及 %d 条（keep %d）改善 %d / 变差 %d / 持平 %d，dist 总降 %d" % (len(det), touched_keep, imp, wor, fla, tot))
        for id_, d_o, d_n, s in sorted(det, key=lambda t: t[2] - t[1])[:6]:
            if d_n < d_o:
                print("    改善 %-12s %+d ctx=%r" % (id_, d_o - d_n, s))
        for id_, d_o, d_n, s in sorted(det, key=lambda t: t[1] - t[2], reverse=True)[:6]:
            if d_n > d_o:
                print("    变差 %-12s %+d ctx=%r" % (id_, d_n - d_o, s))
        return det

    # R4a：前置是「、」才删
    sim(lambda o, i: i > 0 and o[i - 1] == "、", "R4a 前置「、」删")
    # R4b：前置是「。」才删
    sim(lambda o, i: i > 0 and o[i - 1] == "。", "R4b 前置「。」删")
    # R4c：前置是任意标点删（= R0 的 punct 部分，对照）
    sim(lambda o, i: i > 0 and not re.match(r"[ぁ-ゖァ-ヺ]", o[i - 1]) and not ("\u3400" <= o[i - 1] <= "\u9fff"),
        "R4c 前置任意标点删（对照）")

    # 2.5) expected 在这些位置写的是什么：抽样看 unwanted \n-prev 位置的 expected 片段
    print("\n=== unwanted \\n-prev 处的 expected 对照（抽样 10 条）===")
    shown = 0
    for r in results:
        out = r["udkundoku_kakikudashi"]
        if "而して" in r["expected_kakikudashi"]:
            continue
        for m in re.finditer("而して", out):
            i = m.start()
            if i > 0 and out[i - 1] == "\n":
                before = out[max(0, i - 12):i].replace("\n", "/")
                print("  %-12s OUT …%s【而して】%s…" % (r["id"], before, out[m.end():m.end() + 6]))
                shown += 1
                break
        if shown >= 10:
            break

    # 3) R5 替换实验：\n而して → \nして（不删字，只去「而」）
    def sim_replace(label, repl):
        imp = wor = fla = 0
        touched_keep = 0
        for r in results:
            out, exp = r["udkundoku_kakikudashi"], r["expected_kakikudashi"]
            new = out.replace("\n而して", "\n" + repl).replace("、而して", "、" + repl)
            if new == out:
                continue
            if "而して" in exp and repl == "して":
                pass
            d_o = lev(norm(out), norm(exp))
            d_n = lev(norm(new), norm(exp))
            if "而して" in exp:
                touched_keep += 1
            if d_n < d_o:
                imp += 1
            elif d_n > d_o:
                wor += 1
            else:
                fla += 1
        print("\n=== %s ===" % label)
        print("  改写条数含 keep %d：改善 %d / 变差 %d / 持平 %d" % (touched_keep, imp, wor, fla))

    sim_replace("R5a \\n而して→\\nして（keep 条目也改——预期会坏）", "して")
    # 只对 unwanted（无法运行时判 want，模拟里用 expected 判——上线不可行，仅量化上限）
    better_del = better_rep = 0
    for r in results:
        out, exp = r["udkundoku_kakikudashi"], r["expected_kakikudashi"]
        if "而して" in exp:
            continue
        base = lev(norm(out), norm(exp))
        d_del = lev(norm(out.replace("\n而して", "\n").replace("、而して", "、")), norm(exp))
        d_rep = lev(norm(out.replace("\n而して", "\nして").replace("、而して", "、して")), norm(exp))
        if d_del < base:
            better_del += 1
        if d_rep < base:
            better_rep += 1
    print("\n=== unwanted 条目：删除 vs 替换为して 的受益条数（want 不可运行时判，上限参照）===")
    print("  受益（删而して）：%d 条；受益（换して）：%d 条" % (better_del, better_rep))

    # 4) keep 的 8 条的上下文长样（为什么需要而して）
    print("\n=== keep 8 条的而して上下文（-6..+6）===")
    seen = set()
    for r in results:
        if "而して" not in r["expected_kakikudashi"]:
            continue
        out = r["udkundoku_kakikudashi"]
        for m in re.finditer("而して", out):
            key = r["id"]
            if key in seen:
                break
            seen.add(key)
            s = max(0, m.start() - 6)
            print("  %-12s …%s…" % (r["id"], out[s:m.end() + 6].replace("\n", "/")))


if __name__ == "__main__":
    main()
