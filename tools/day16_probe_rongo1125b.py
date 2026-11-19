# -*- coding: utf-8 -*-
"""day16_probe_rongo1125b.py — 看 rongo1125 原始 genbun01 内容（长章，可能内含多段）。"""
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}


def main():
    u = "https://kanbun.info/keibu/rongo1125.html"
    t = urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                              timeout=35).read().decode("utf-8", "replace")
    m = re.search(r'<div class="genbun01">(.*?)</div>', t, re.S)
    print("RAW genbun01:\n", m.group(1)[:2500] if m else "none", flush=True)
    m2 = re.search(r'<div class="yomi03">(.*?)</div>', t, re.S)
    if m2:
        raw = m2.group(1)
        print("\nRAW yomi03 (first 800 chars):\n", raw[:800], flush=True)


if __name__ == "__main__":
    main()
