# -*- coding: utf-8 -*-
"""night23_probe_rongo_chapter.py — 看 rongo0101.html 的成对结构。"""
import re
import sys
import urllib.request
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}
req = urllib.request.Request("https://kanbun.info/keibu/rongo0101.html", headers=UA)
page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")

print("div classes:", dict(Counter(re.findall(r'<div class="([^"]+)"', page))))
print("section classes:", dict(Counter(re.findall(r'<section class="([^"]+)"', page))))
print("ruby/rt/rp:", len(re.findall(r"<ruby>", page)), len(re.findall(r"<rt>", page)),
      len(re.findall(r"<rp>", page)))

for cls in ("genbun01", "yomi02", "honbun01", "honbun02", "shomemei", "imige"):
    n = page.count(cls)
    print("%-10s count=%d" % (cls, n))

i = page.find("genbun01")
print("\n--- raw html from first genbun01 ---")
print(page[i - 30:i + 1200] if i >= 0 else "NO genbun01")
