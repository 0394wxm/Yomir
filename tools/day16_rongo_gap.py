# -*- coding: utf-8 -*-
"""day16_rongo_gap.py — 查論語部网站章节数 vs 仓内 golden_rongo_full 覆盖。

只读：联网抓 20 个篇索引页，统计站上章节 id，与仓内已有 id 求差集。
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}
CHAPTER_RX = re.compile(r'href="(?:\.\./keibu/)?(rongo(\d{2})(\d{2}))\.html"')


def main():
    have = {x["id"].split("-")[0] for x in
            json.load(open(os.path.join(ROOT, "eval", "golden_rongo_full.json"),
                           encoding="utf-8"))}
    allc = set()
    for p in range(1, 21):
        u = "https://kanbun.info/keibu/rongo%02d.html" % p
        try:
            t = urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                                       timeout=25).read().decode("utf-8", "replace")
        except Exception as e:
            print("[FAIL] pian %02d %r" % (p, e), flush=True)
            continue
        n0 = len(allc)
        for m in CHAPTER_RX.finditer(t):
            if int(m.group(2)) == p:
                allc.add(m.group(1))
        print("[IDX] pian %02d  +%d" % (p, len(allc) - n0), flush=True)
        time.sleep(0.2)
    print("\nsite chapters %d | have %d | missing %d"
          % (len(allc), len(have), len(allc - have)), flush=True)
    print("missing sample:", sorted(allc - have)[:40], flush=True)


if __name__ == "__main__":
    main()
