# -*- coding: utf-8 -*-
"""day11_kore2.py — 「これ→之」的语义安全性与护栏验证。

要回答三个问题：
  1. 语料里 expected 是否真的从不写「これ」（若有，全替换会误伤）
  2. 经典句（pytest/验收门锁着的那些）替换后是否被破坏
  3. 替换会不会误伤「これ」作为真指示代词的现代用法（如「これを見よ」）
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


def main():
    with open(os.path.join(EV, "day10_results_1000.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["results"] if r.get("udkundoku_kakikudashi")]

    # 1. expected 里有「これ」吗
    has_kore = [r for r in rows if "これ" in norm(r["expected_kakikudashi"])]
    print("1) expected 含「これ」的条目：%d" % len(has_kore))
    for r in has_kore[:10]:
        print("   [%s] exp: %s" % (r["id"], norm(r["expected_kakikudashi"])[:100]))

    # expected 里「之」出现次数总计
    tot_shi = sum(norm(r["expected_kakikudashi"]).count("之") for r in rows)
    tot_kore_out = sum(norm(r["udkundoku_kakikudashi"]).count("これ") for r in rows)
    print("\n   语料统计：expected 里「之」共 %d 处；引擎输出里「これ」共 %d 处"
          % (tot_shi, tot_kore_out))

    # 2. 经典句
    print("\n2) 经典句 / 关键句替换测试：")
    cases = [
        "王顧左右而言他",
        "宋人有耕田者。",
        "梁惠王曰",
        "楚人有鬻楯與矛者。",
        "直匍匐而歸耳。",
        "子曰、德不孤、必有鄰。",
        "学而時習之",
        "之を" + "これ",
    ]
    from backend.main import app  # noqa
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        for c in cases[:7]:
            r = client.post("/api/kundoku", json={"text": c})
            if r.status_code != 200:
                print("   [%s] HTTP %d" % (c, r.status_code))
                continue
            kk = r.json().get("kakikudashi", "")
            after = kk.replace("これ", "之")
            flag = "  <== 替换生效" if after != kk else ""
            print("   [%s]\n      got : %s\n      repl: %s%s"
                  % (c, norm(kk)[:80], norm(after)[:80], flag))

    # 3. 现代日语「これ」误伤分析：输出里「これ」后面跟什么
    print("\n3) 输出里「これ」的右邻字符分布（判断护栏是否必要）：")
    import collections
    right = collections.Counter()
    for r in rows:
        g = norm(r["udkundoku_kakikudashi"])
        for m in re.finditer("これ", g):
            j = m.end()
            right[g[j] if j < len(g) else "<END>"] += 1
    for ch, n in right.most_common(20):
        print("   %r %d" % (ch, n))


if __name__ == "__main__":
    main()
