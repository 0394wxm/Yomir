# -*- coding: utf-8 -*-
"""night25_align_sodashite.py v2 — 字符级对齐，双向看 而/して/にして 的对应。

方向 A：got 的每个「而して」（3 字符）→ expected 侧逐字映射后归类。
方向 B：expected 的每个「にして」→ got 侧对应片段归类。
"""
import difflib
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(s):
    return re.sub(r"\s+", "", s)


def load(name):
    with open(os.path.join(ROOT, "eval", name), encoding="utf-8") as f:
        return json.load(f)["results"]


def char_map(got, exp):
    """got 索引 → exp 索引（equal 块内一一对应），否则 None。"""
    sm = difflib.SequenceMatcher(a=got, b=exp, autojunk=False)
    m = [None] * len(got)
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == "equal":
            for k in range(a2 - a1):
                m[a1 + k] = b1 + k
    return m


def dir_a(rows, label):
    cat = Counter()
    samples = []
    for r in rows:
        got = norm(r.get("udkundoku_kakikudashi") or "")
        exp = norm(r["expected_kakikudashi"])
        m = char_map(got, exp)
        for mt in re.finditer("而して", got):
            i = mt.start()
            seg = "".join(exp[m[j]] if (m[j] is not None and j < len(m)) else "·" for j in range(i, i + 3))
            if seg == "而して":
                cat["保留(而して)"] += 1
            elif seg == "···":
                cat["删除"] += 1
            elif seg.replace("·", "") == "して":
                cat["→して(而被删)"] += 1
            elif seg.replace("·", "") == "にして":
                cat["→にして"] += 1
            else:
                cat["其它:%s" % seg] += 1
            if len(samples) < 10:
                samples.append((r["id"], got[max(0, i - 8):i + 9], seg))
    print("--- 方向A %s：got 而して %d 处 → expected 侧 ---" % (label, sum(cat.values())))
    for k, v in cat.most_common():
        print("    %-16s %3d" % (k, v))
    for id_, ctx, seg in samples[:6]:
        print("    %-12s …%s…  exp侧=%r" % (id_, ctx, seg))
    return cat


def dir_b(rows, label):
    cat = Counter()
    samples = []
    for r in rows:
        got = norm(r.get("udkundoku_kakikudashi") or "")
        exp = norm(r["expected_kakikudashi"])
        m = char_map(got, exp)
        rev = {}
        for gi, ei in enumerate(m):
            if ei is not None:
                rev[ei] = gi
        for mt in re.finditer("にして", exp):
            j = mt.start()
            gseg = "".join(got[rev[j + k]] if (j + k) in rev else "·" for k in range(3))
            if gseg == "にして":
                cat["保留(にして,不可能)"] += 1
            elif gseg == "···":
                cat["got无对应(插入)"] += 1
            elif gseg.replace("·", "") == "して":
                cat["got=して"] += 1
            elif gseg.replace("·", "") == "而して":
                cat["got=而して"] += 1
            else:
                cat["got=%s" % gseg] += 1
            if len(samples) < 10:
                # 找 got 上下文
                gidx = rev.get(j)
                ctx = got[max(0, gidx - 8):gidx + 9] if gidx is not None else "(无)"
                samples.append((r["id"], ctx, gseg))
    print("--- 方向B %s：expected にして %d 处 ← got 侧 ---" % (label, sum(cat.values())))
    for k, v in cat.most_common():
        print("    %-16s %3d" % (k, v))
    for id_, ctx, seg in samples[:8]:
        print("    %-12s got …%s…  exp=にして(got侧=%r)" % (id_, ctx, seg))
    return cat


def main():
    koji = load("night22_results_full.json")
    rongo = load("night23_results_rongo.json")
    for rows, label in ((koji, "故事名言500"), (rongo, "論語117")):
        dir_a(rows, label)
        dir_b(rows, label)
        print()


if __name__ == "__main__":
    main()
