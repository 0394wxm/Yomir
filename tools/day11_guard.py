# -*- coding: utf-8 -*-
"""day11_guard.py — 为 Rule D（これ→之）设计护栏：找语料外的反例风险。

问题：现代日语/和文中「これ」是真指示代词（「これを見よ」），
不能改成「之」。本脚本：
  1. 用历史文档/经典句构造「必須保留 これ」的测试集
  2. 检查各候选护栏在这些句子上是否保留
  3. 找语料内「これ」与 expected「之」的对齐证据（是否 1:1）
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
sys.path.insert(0, ROOT)


def norm(s):
    return re.sub(r"\s+", "", s or "")


# 语料外的「これ必须保留」候选（真指示代词 / 熟语）
KEEP_CASES = [
    ("これを見よ", "命令形，真指示代词"),
    ("これを以て", "汉文训读固定套语，规范写法两可"),
    ("これに由りて", "同上"),
    ("これより後", "时间副词"),
    ("これぞ", "强调指示"),
    ("これこそ", "强调指示"),
]


def main():
    with open(os.path.join(EV, "day10_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]

    # 1. 语料内 1:1 对齐检验：输出 これ 数 == expected 之 数 的条目占比
    same = diff = 0
    diff_examples = []
    for r in rows:
        g, e = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        if g.count("これ") == e.count("之"):
            same += 1
        elif g.count("これ") or e.count("之"):
            diff += 1
            if len(diff_examples) < 8:
                diff_examples.append((r["id"], g.count("これ"), e.count("之")))
    tot = same + diff
    print("1) 输出これ数 == expected之数 的条目：%d / %d（%.1f%%）"
          % (same, tot, 100.0 * same / tot if tot else 0))
    print("   不一致但涉及这两者的条目：%d" % diff)
    for x in diff_examples:
        print("      [%s] これ×%d vs 之×%d" % x)

    # 2. 语料内是否有「これ」在 expected 里被写成别的（不是 之，也不是 これ）
    print("\n2) 找 expected 里对应位置不是「之」的样本（语义漂移风险）：")
    from backend.main import app
    from fastapi.testclient import TestClient
    n_show = 0
    with TestClient(app) as client:
        for r in rows:
            g, e = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
            if "これ" not in g:
                continue
            replaced = g.replace("これ", "之")
            # 替换后是否与 expected 更接近但不完全一致：看替换是否正好落在对齐位置
            if replaced != e and n_show < 3:
                n_show += 1
                print("   [%s]" % r["id"])
                print("     got: %s" % g[:100])
                print("     new: %s" % replaced[:100])
                print("     exp: %s" % e[:100])

    # 3. 护栏方案的实际效果（在语料外句子上）
    print("\n3) 护栏在语料外句子上的表现：")
    guards = {
        "G0 无护栏": lambda t: t.replace("これ", "之"),
        "G1 排除「これを見/これを見よ」": lambda t: re.sub(
            r"これ(?=を見)", "\u0000", t).replace("これ", "之").replace("\u0000", "これ"),
        "G2 排除「これより」": lambda t: re.sub(
            r"これ(?=より)", "\u0000", t).replace("これ", "之").replace("\u0000", "これ"),
        "G3 排除「以て」前": lambda t: re.sub(
            r"これ(?=を以て)", "\u0000", t).replace("これ", "之").replace("\u0000", "これ"),
    }
    for name, fn in guards.items():
        print("   %s:" % name)
        for s, note in KEEP_CASES:
            print("      %-12s -> %-12s  %s" % (s, fn(s), note))


if __name__ == "__main__":
    main()
