# -*- coding: utf-8 -*-
"""day14_inspect.py — D14 第四步：把候选词在真实句子里看一遍。

不猜，逐条打印 got / exp 对照片段，用来判断：
  * 假名串 X 在 got 里对应 expected 的什么（1:1 还是多对一）；
  * 白文里是否有对应的汉字（这是护栏的依据）。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def main():
    with open(os.path.join(EV, "day11_results_1000.json"), encoding="utf-8") as f:
        rows = json.load(f)["results"]
    rows = [r for r in rows if r.get("udkundoku_kakikudashi") is not None]

    probes = sys.argv[1:] or ["すでに", "ただ", "あに", "みな", "なかれ", "いずくんぞ"]
    for probe in probes:
        print("\n" + "=" * 78, flush=True)
        print("=== %s ===" % probe, flush=True)
        hits = 0
        for r in rows:
            got = norm(r["udkundoku_kakikudashi"])
            exp = norm(r["expected_kakikudashi"])
            if probe not in got:
                continue
            hits += 1
            if hits > 6:
                continue
            gi = got.find(probe)
            # 找 exp 里对应的位置：用较长上下文定位
            print("\n[%s] 白文: %s" % (r["id"], norm(r["hakubun"])[:60]), flush=True)
            print("  got: ...%s..." % got[max(0, gi - 18):gi + 24], flush=True)
            # 打印 exp 全文（短句才截断）
            print("  exp: %s" % (exp[:120] + ("..." if len(exp) > 120 else "")), flush=True)
            print("  白文含候选汉字:", flush=True)
            for ch in "皆既唯豈勿毋焉如":
                if ch in norm(r["hakubun"]):
                    print("    - %s" % ch, flush=True)
        print("\n(共 %d 条含 %s)" % (hits, probe), flush=True)


if __name__ == "__main__":
    main()
