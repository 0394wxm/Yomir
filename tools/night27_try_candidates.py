# -*- coding: utf-8 -*-
"""night27_try_candidates.py — 候选 URL 试探 + 首页全链接分类。"""
import re
import sys
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


home = fetch("https://kanbun.info/")
hrefs = []
for m in re.finditer(r'href="([^"]+\.html)"', home):
    u = m.group(1)
    if u not in hrefs:
        hrefs.append(u)
keibu = [u for u in hrefs if "keibu" in u or "kanbu" in u]
print("home hrefs total:", len(hrefs), " keibu-ish:", keibu[:20])

candidates = [
    "https://kanbun.info/keibu/moushi01.html",
    "https://kanbun.info/keibu/mouji01.html",
    "https://kanbun.info/keibu/mousi01.html",
    "https://kanbun.info/koji/koji00moushi.html",
    "https://kanbun.info/koji/koji00mou.html",
]
for u in candidates:
    try:
        t = fetch(u)
        title = re.search(r"<title>([^<]+)</title>", t)
        print("OK  %s  %s" % (u, title.group(1) if title else "(no title)"))
    except urllib.error.HTTPError as e:
        print("404 %s" % u)
    except Exception as e:
        print("ERR %s %r" % (u, e))
