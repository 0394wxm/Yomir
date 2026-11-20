# -*- coding: utf-8 -*-
"""night58_probe_forms.py — N58 解剖补充：只/於/須/晚/晩/遙 的 exp 侧表层形态 + got 侧碎片。

目的：在离线模拟前把 kana→kanji 候选的 repl 词形定准（N14 教训：词形按 expected 真实形态）。
只读，输出 eval/night58_probe_forms.txt。
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

TARGETS = ["只", "於", "須", "晚", "晩", "遙", "遥", "舊", "旧", "曉", "暁", "醉", "酔", "縱", "縦", "靑", "青", "處", "処"]


def norm(s):
    return re.sub(r"\s+", "", s or "")


def main():
    doc = json.load(open(os.path.join(EV, "night57_results_3000.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    rows_new = rows[2000:]
    lines = []
    for t in TARGETS:
        for scope_name, rs in (("新增", rows_new), ("全3000", rows)):
            frag = collections.Counter()
            form = collections.Counter()
            exp_cnt = got_cnt = 0
            for r in rs:
                got = norm(r["udkundoku_kakikudashi"])
                exp = norm(r["expected_kakikudashi"])
                exp_cnt += exp.count(t)
                got_cnt += got.count(t)
                if t not in exp:
                    continue
                sm = SequenceMatcher(None, got, exp, autojunk=False)
                for op, i1, i2, j1, j2 in sm.get_opcodes():
                    if op in ("replace", "insert") and t in exp[j1:j2]:
                        g_frag = got[i1:i2]
                        if g_frag:
                            frag[g_frag] += 1
                for m in re.finditer(re.escape(t), exp):
                    form[exp[max(0, m.start() - 2):m.start() + 3]] += 1
            lines.append("=== %s（%s）exp %d / got %d ===" % (t, scope_name, exp_cnt, got_cnt))
            lines.append("  exp 形态: " + " | ".join("%r×%d" % kv for kv in form.most_common(10)))
            lines.append("  got 碎片: " + " | ".join("%r×%d" % kv for kv in frag.most_common(10)))
    txt = "\n".join(lines)
    open(os.path.join(EV, "night58_probe_forms.txt"), "w", encoding="utf-8",
         newline="\n").write(txt + "\n")
    print(txt, flush=True)


if __name__ == "__main__":
    main()
