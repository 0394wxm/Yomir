# -*- coding: utf-8 -*-
"""night25_joint_shift.py — して/而して/にして 链条错位的联合交叉表 + 上下文切分检验。

对 got 里每个 して 系出现处（而して/して/にして），取 exp 侧映射片段，
交叉表：got形态 × exp形态；再按 got 前置字符分层看能否切分。
"""
import difflib
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(s):
    return re.sub(r"\s+", "", s)


def load(name):
    with open(os.path.join(ROOT, "eval", name), encoding="utf-8") as f:
        return json.load(f)["results"]


def char_map(got, exp):
    sm = difflib.SequenceMatcher(a=got, b=exp, autojunk=False)
    m = [None] * len(got)
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == "equal":
            for k in range(a2 - a1):
                m[a1 + k] = b1 + k
    return m


def got_forms(got):
    """返回 [(start_of_shite, form)]，form ∈ 而して/して/にして；して 系不去重重叠。"""
    out = []
    for m in re.finditer("にして", got):
        out.append((m.start() + 1, "にして"))
    used = {s for s, _ in out}
    for m in re.finditer("して", got):
        i = m.start()
        if i in used or (i - 1) in used:
            continue  # 已被 にして 覆盖
        form = "而して" if i > 0 and got[i - 1] == "而" else "して"
        out.append((i, form))
    return out


def prev_class(got, i):
    prev = got[i - 1] if i > 0 else "BOS"
    if prev == "BOS":
        return "BOS"
    if prev == "而":
        return "而"
    if re.match(r"[ぁ-ゖァ-ヺ]", prev):
        return "kana:" + prev
    if "\u3400" <= prev <= "\u9fff":
        return "kanji"
    return "punct:" + prev


def main():
    koji = load("night22_results_full.json")
    rongo = load("night23_results_rongo.json")

    joint = defaultdict(Counter)  # (got_form, exp_form) -> Counter(prev_class)
    for rows in (koji, rongo):
        for r in rows:
            got = norm(r.get("udkundoku_kakikudashi") or "")
            exp = norm(r["expected_kakikudashi"])
            m = char_map(got, exp)
            for i, form in got_forms(got):
                # exp 侧：し/て 两字（i 对应 し）
                e0, e1 = m[i], m[i + 1] if i + 1 < len(m) else None
                if e0 is None or e1 is None or e1 != e0 + 1:
                    exp_form = "删除/散"
                else:
                    with_n = e0 > 0 and exp[e0 - 1] == "に" and m[i - 1] != e0 - 1
                    if with_n:
                        exp_form = "にして"
                    elif exp[e0:e0 + 2] == "して":
                        exp_form = "して"
                    else:
                        exp_form = "其它:%s" % exp[max(0, e0 - 2):e0 + 3]
                joint[(form, exp_form)][prev_class(got, i)] += 1

    print("=== 交叉表（got形态 × exp形态），括号内为前置字符分布 ===")
    for (gf, ef), c in sorted(joint.items(), key=lambda kv: -sum(kv[1].values())):
        print("  got %-6s -> exp %-14s : %3d   %s" % (gf, ef, sum(c.values()), dict(c.most_common(6))))


if __name__ == "__main__":
    main()
