# -*- coding: utf-8 -*-
"""night21_probe_pages.py — 探 keibu(論語) / syubu(漢詩) 页结构与链接（NIGHT21 细化）。"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
import urllib.request

for url in ("https://kanbun.info/keibu/rongo00.html",
            "https://kanbun.info/syubu/reki_kodai.html"):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=45) as r:
            h = r.read().decode("utf-8", errors="replace")
        print("===", url.rsplit("/", 1)[-1], "len", len(h))
        print("genbun01:", h.count("genbun01"), "yomi02:", h.count("yomi02"))
        links = re.findall(r'href="([^"]+\.html)"', h)
        rel = [l for l in links if ".." not in l and not l.startswith("http") and "#" not in l]
        print("rel links", len(rel), ":", " ".join(rel[:20]))
        abs_ = [l for l in links if "syubu" in l or "keibu" in l]
        print("section links:", " ".join(sorted(set(abs_))[:10]))
    except Exception as e:
        print("=== FAILED", url, repr(e))
