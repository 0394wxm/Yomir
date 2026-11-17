# -*- coding: utf-8 -*-
"""night21_probe_rongo01.py — 論語内容页结构探针（NIGHT21）。"""
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

url = "https://kanbun.info/keibu/rongo01.html"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=45) as r:
    h = r.read().decode("utf-8", errors="replace")
print("rongo01 len", len(h), "genbun01:", h.count("genbun01"), "yomi02:", h.count("yomi02"))
pairs = re.findall(r'<div class="genbun01">(.*?)</div>\s*<div class="yomi02">(.*?)</div>', h, re.S)
print("pairs:", len(pairs))
for gb, ym in pairs[:3]:
    s1 = re.sub(r"<[^>]+>", "", gb)[:40]
    s2 = re.sub(r"<[^>]+>", "", ym)[:40]
    print("  白文:", s1)
    print("  書下:", s2)
