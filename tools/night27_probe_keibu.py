# -*- coding: utf-8 -*-
"""night27_probe_keibu.py — 探 kanbun.info 経部索引（找 孟子 页形态）。"""
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}
req = urllib.request.Request("https://kanbun.info/keibu/keibu.html", headers=UA)
page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")

links = []
for m in re.finditer(r'href="([^"]+\.html)"', page):
    u = m.group(1)
    if u not in links:
        links.append(u)
print("unique links:", len(links))
for u in links[:40]:
    print("  ", u)
