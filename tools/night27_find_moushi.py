# -*- coding: utf-8 -*-
"""night27_find_moushi.py — 从站点首页/已知页找 孟子 部的 URL 形态。"""
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


# 首页导航里找 孟子
home = fetch("https://kanbun.info/")
hits = re.findall(r'href="([^"]+)"[^>]*>[^<]*孟子', home)
print("home 孟子 links:", hits)
# 兜底：全部含 moushi/mouji/mose 的链接
guess = [u for u in re.findall(r'href="([^"]+)"', home)
         if re.search(r"mou?sh?i|mousu|mose|sise", u, re.I)]
print("home guess:", guess[:10])

# 从論語篇页的侧栏/导航找経部其它书目
rongo = fetch("https://kanbun.info/keibu/rongo01.html")
sec = re.findall(r'<a href="(\.\./keibu/[a-z0-9_]+\.html)"[^>]*>([^<]{1,30})</a>', rongo)
print("\nrongo01 侧栏链接（前 30）:")
for u, t in sec[:30]:
    print("  ", u, "|", t)
