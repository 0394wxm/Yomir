# -*- coding: utf-8 -*-
"""day16_probe_kokyo.py — 列出 kokyo00 索引页的实际链接。"""
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}


def main():
    u = "https://kanbun.info/keibu/kokyo00.html"
    t = urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                              timeout=35).read().decode("utf-8", "replace")
    print("len", len(t), flush=True)
    links = sorted(set(re.findall(r'href="([^"]+)"', t)))
    for h in links:
        print(" ", h, flush=True)


if __name__ == "__main__":
    main()
