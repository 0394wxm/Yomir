# -*- coding: utf-8 -*-
"""night58_mine.py — N58 第一步「解剖」：golden_3000 新增 1000 条（詩経/漢詩短句）上挖 Rule H 候选。

方法论 = Night 22/N55：
  A. 新增 1000 条的字符 delta（exp-got 汉字计数），与全部 3000 对照；
  B. 新增 1000 内 delta 高的目标字：difflib 逐条对齐收集 got 侧被替换片段 + exp 侧表层形态；
  C. 新增 1000 分档（≤20 / 21-40 / …）复核 N57 构成警告。
不重复挖 N55 已挖过的：E 护栏字（皆/既/旣/猶/豈/唯）、F（亦/何/可=べし/べく）、
G（又/所以/所謂/相）、D（之）、已拒绝（為/不/与/べき/べから/ために 系）。
只读，输出 eval/night58_mine.json。
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

# 已被现有规则覆盖（护栏字）或已定性的目标——不再作为 Rule H 挖掘对象
ALREADY = set("皆既旣猶豈唯亦何可之又所以謂相為不与惠恵盡尽對対竊窃雞鶏陷陥")
# D14/D17/N55 报告里逐条定性「不可做/已拒绝」的字（如再进 top 也要给出「已定性」标注）
REJECTED = set("勿焉如若莫")

THRESH_DELTA = 5  # 新增 1000 条里 exp-got 计数差 >= 5 的字进 top 榜


def norm(s):
    return re.sub(r"\s+", "", s or "")


def is_kanji(c):
    return "\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf"


def main():
    doc = json.load(open(os.path.join(EV, "night57_results_3000.json"), encoding="utf-8"))
    rows_all = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    rows_new = rows_all[2000:]          # golden_3000 新增段（31 parallel_extra + 詩経/漢詩）
    rows_old = rows_all[:2000]
    print("全库有效 %d 条（error %d 条除外）| 新增段 %d / 前 2000 %d" % (
        len(rows_all), 3000 - len(rows_all), len(rows_new), len(rows_old)), flush=True)

    def charcount(rs):
        e, g = collections.Counter(), collections.Counter()
        for r in rs:
            e.update(norm(r["expected_kakikudashi"]))
            g.update(norm(r["udkundoku_kakikudashi"]))
        return e, g

    exp_n, got_n = charcount(rows_new)
    exp_a, got_a = charcount(rows_all)

    # ---- A. 字符 delta：新增 1000 为主，对照全 3000 ----
    cand = []
    for c in set(exp_n) | set(got_n):
        if not is_kanji(c):
            continue
        e_n, g_n = exp_n.get(c, 0), got_n.get(c, 0)
        if e_n >= THRESH_DELTA and e_n > g_n:
            cand.append({"char": c, "exp_new": e_n, "got_new": g_n,
                         "delta_new": e_n - g_n,
                         "exp_all": exp_a.get(c, 0), "got_all": got_a.get(c, 0)})
    cand.sort(key=lambda x: -x["delta_new"])
    lines = []
    lines.append("=== A. 新增 1000 条字符 delta（exp_new>=5 且 exp>got）===")
    for r in cand[:40]:
        tag = ""
        if r["char"] in ALREADY:
            tag = "【已覆盖】"
        elif r["char"] in REJECTED:
            tag = "【已拒绝/不可做】"
        lines.append("  %-2s 新增 exp %4d got %4d Δ %5d | 全3000 exp %4d got %4d %s" % (
            r["char"], r["exp_new"], r["got_new"], r["delta_new"],
            r["exp_all"], r["got_all"], tag))

    # ---- B. 目标字：got 侧替换片段 + exp 侧表层形态（只统计新增段，difflib 对齐）----
    targets = [r["char"] for r in cand[:12]
               if r["char"] not in ALREADY][:10]
    out_targets = []
    for t in targets:
        frag = collections.Counter()
        form = collections.Counter()
        n_rows_hit = 0
        for r in rows_new:
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
            "char": t, "exp_new": exp_n.get(t, 0), "got_new": got_n.get(t, 0),
            "rows_with_replace": n_rows_hit,
            "top_got_frags": frag.most_common(20),
            "top_exp_forms": form.most_common(16),
        })
        lines.append("\n=== B. %s（新增 exp %d / got %d，有替换碎片行 %d）===" % (
            t, exp_n.get(t, 0), got_n.get(t, 0), n_rows_hit))
        lines.append("  got 侧片段 top: " +
                     " | ".join("%r×%d" % kv for kv in frag.most_common(12)))
        lines.append("  exp 形态 top: " +
                     " | ".join("%r×%d" % kv for kv in form.most_common(10)))

    # ---- C. 新增 1000 分档复核 ----
    buckets = collections.Counter()
    dist_buckets = collections.defaultdict(list)
    for r in rows_new:
        hb = norm(r["hakubun"])
        L = len(hb)
        b = "<=20" if L <= 20 else ("21-40" if L <= 40 else ("41-60" if L <= 60 else ">60"))
        buckets[b] += 1
        exp = norm(r["expected_kakikudashi"])
        got = norm(r["udkundoku_kakikudashi"])
        d = lev(got, exp)
        dist_buckets[b].append(d)
    lines.append("\n=== C. 新增 %d 条分档（白文长度 / avgDist）===" % len(rows_new))
    for b in ("<=20", "21-40", "41-60", ">60"):
        ds = dist_buckets[b]
        if ds:
            lines.append("  %5s %5d 条  avgDist %.3f" % (b, buckets[b], sum(ds) / len(ds)))

    out = {"n_new": len(rows_new), "n_all": len(rows_all),
           "chars": cand, "targets": out_targets,
           "buckets": {b: {"n": buckets[b],
                           "avgdist": round(sum(v) / len(v), 3) if v else None}
                       for b, v in dist_buckets.items()}}
    json.dump(out, open(os.path.join(EV, "night58_mine.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    txt = "\n".join(lines)
    open(os.path.join(EV, "night58_mine.txt"), "w", encoding="utf-8",
         newline="\n").write(txt + "\n")
    print(txt, flush=True)
    print("\nwritten: eval/night58_mine.json / night58_mine.txt", flush=True)


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


if __name__ == "__main__":
    main()
