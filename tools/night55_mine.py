# -*- coding: utf-8 -*-
"""night55_mine.py — N55 第一步：在 day17 真机基线（Rule F 已上线）上挖 Rule G 候选。

Night 22/D17 方法论第一步「解剖」：
  A. 当前字符 delta（exp-got 汉字，delta≥8）
  B. 目标字（D17 §14 遗留：為/不/所/相/与，加 又 复核）在 expected 里的表层形态
     与引擎实际输出的假名碎片 —— 用 difflib 对 (got, exp) 逐条对齐，
     收集「exp 侧含目标字、got 侧被替换文本」的片段。
只读，输出 eval/night55_mine.json。
"""
import collections
import json
import os
import re
import sys
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

TARGETS = ["為", "不", "所", "相", "与", "又"]
SHIPPED = {"皆", "既", "旣", "猶", "豈", "唯", "亦", "何", "可"}  # D14/F 已上线护栏字


def norm(s):
    return re.sub(r"\s+", "", s or "")


def is_kanji(c):
    return "\u3400" <= c <= "\u9fff"


def main():
    doc = json.load(open(os.path.join(EV, "day17_results_2000.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    print("样本 %d 条（day17 真机基线，Rule F 已上线）" % len(rows), flush=True)

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
            cand.append({"char": c, "exp": e, "got": g, "delta": e - g})
    cand.sort(key=lambda x: -x["delta"])
    print("\n=== A. 当前字符 delta（exp>got，delta≥8）top 25 ===", flush=True)
    for r in cand[:25]:
        mark = "（G 目标）" if r["char"] in TARGETS else ""
        print("  %-3s exp %4d got %4d Δ %5d %s" % (r["char"], r["exp"], r["got"],
                                                   r["delta"], mark), flush=True)

    # B. 目标字的引擎假名碎片（got 侧被替换片段）
    out_targets = []
    for t in TARGETS:
        frag = collections.Counter()          # got 侧替换片段
        form = collections.Counter()          # exp 侧表层形态（目标字±2 字）
        n_rows_hit = 0
        for r in rows:
            got = norm(r["udkundoku_kakikudashi"])
            exp = norm(r["expected_kakikudashi"])
            if t not in exp:
                continue
            sm = SequenceMatcher(None, got, exp, autojunk=False)
            row_frag = []
            for op, i1, i2, j1, j2 in sm.get_opcodes():
                if op in ("replace", "insert") and t in exp[j1:j2]:
                    g_frag = got[i1:i2]
                    if g_frag:
                        row_frag.append(g_frag)
            if row_frag:
                n_rows_hit += 1
                frag.update(row_frag)
            for m in re.finditer(re.escape(t), exp):
                form[exp[max(0, m.start() - 1):m.start() + 3]] += 1
        out_targets.append({
            "char": t, "exp": exp_c.get(t, 0), "got": got_c.get(t, 0),
            "rows_with_replace": n_rows_hit,
            "top_got_frags": frag.most_common(20),
            "top_exp_forms": form.most_common(16),
        })
        print("\n=== B. %s（exp %d / got %d，有替换碎片行 %d）===" % (
            t, exp_c.get(t, 0), got_c.get(t, 0), n_rows_hit), flush=True)
        print("  got 侧片段 top:", " | ".join("%r×%d" % (k, v) for k, v in frag.most_common(12)),
              flush=True)
        print("  exp 形态 top:", " | ".join("%r×%d" % (k, v) for k, v in form.most_common(10)),
              flush=True)

    out = {"n": len(rows), "chars": cand[:40], "targets": out_targets}
    json.dump(out, open(os.path.join(EV, "night55_mine.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    print("\nwritten: eval/night55_mine.json", flush=True)


if __name__ == "__main__":
    main()
