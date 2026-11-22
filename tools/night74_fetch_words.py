# -*- coding: utf-8 -*-
"""night74_fetch_words.py — N74 ③ 补抓器：抓任意词形（基础形/参考形）到缓存。

读取 eval/night74_dict_cache/_extra_words.txt（UTF-8，一行一词），
逐词抓 www.weblio.jp/content/<word>，存为 x_<word>.txt（限速 0.7s）。
用法: python -I tools/night74_fetch_words.py
"""
import os
import ssl
import sys
import time
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
CACHE = os.path.join(ROOT, "eval", "night74_dict_cache")

# 复用主抓取器的提取逻辑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from night74_fetch_dict import fetch_one  # noqa: E402


def main():
    src = os.path.join(CACHE, "_extra_words.txt")
    with open(src, "r", encoding="utf-8") as f:
        words = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    for w in words:
        path = os.path.join(CACHE, "x_" + urllib.parse.quote(w.strip()) + ".txt")
        if os.path.exists(path):
            print("skip", urllib.parse.quote(w.strip()))
            continue
        status, url, nbytes, region = fetch_one(w)
        with open(path, "w", encoding="utf-8") as f:
            f.write("# URL %s\n# word %s\n# status %s bytes=%d\n\n" % (url, w, status, nbytes))
            f.write(region[:4500] if region else "(no region)")
        print("fetched", urllib.parse.quote(w.strip()), status, flush=True)
        time.sleep(0.7)


if __name__ == "__main__":
    main()
