# -*- coding: utf-8 -*-
"""night21_probe_rongo01b.py — 論語页 href/class 全量探针（NIGHT21）。"""
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

url = "https://kanbun.info/keibu/rongo01.html"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=45) as r:
    h = r.read().decode("utf-8", errors="replace")
print("len", len(h))
hrefs = re.findall(r'href="([^"]+)"', h)
own = [x for x in hrefs if x.endswith(".html") and ".." not in x and not x.startswith("http")]
print("own html links:", " ".join(sorted(set(own))[:25]))
classes = sorted(set(re.findall(r'class="(\w+)"', h)))
print("classes:", " ".join(classes))
print("has ron:", "ron" in h, "| genbun:", "genbun" in h, "| yomi:", "yomi" in h)
