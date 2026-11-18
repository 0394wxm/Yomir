# -*- coding: utf-8 -*-
"""night23_probe_rongo_links.py — 論語索引全部链接 + 章节页翻页形态。"""
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


idx = fetch("https://kanbun.info/keibu/rongo01.html")
links = []
for m in re.finditer(r'href="([^"]*rongo[^"]*\.html)"', idx):
    u = m.group(1)
    if u not in links:
        links.append(u)
print("=== all %d unique rongo links ===" % len(links))
for u in links:
    print("  ", u)

page = fetch("https://kanbun.info/keibu/rongo0101.html")
print("\n=== rongo0101 内部链接（找翻页/相邻章）===")
inner = []
for m in re.finditer(r'href="([^"]*rongo[^"]*\.html)"', page):
    u = m.group(1)
    if u not in inner:
        inner.append(u)
print(inner[:20])
