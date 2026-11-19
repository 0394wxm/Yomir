# -*- coding: utf-8 -*-
"""day16_scrape_left.py — 补抓全站未入语料的页面（8 个故事页 + その他栏目）。

只读站点事实文本，不改任何 expected。产物 eval/day16_scraped.json。
"""
import html as html_mod
import json
import os
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}

TAG_RX = re.compile(r"<[^>]+>")
RT_RX = re.compile(r"<rt>.*?</rt>", re.S)
RP_RX = re.compile(r"<rp>.*?</rp>", re.S)
PAIR_RX = re.compile(r'<div class="genbun01">(.*?)</div>\s*<div class="yomi0[23]">(.*?)</div>', re.S)
COUNTER_RX = re.compile(r"^\d{3}（\d{2}-\d{2}）")
LINK_RX = re.compile(r'href="\.\./(?:koji|keibu|miscellaneous)/([a-z0-9_]+)\.html"')

MISS = ["ichigo", "ichiyorai", "itteiji", "kenkon", "kenni", "kotoge", "ryuryu", "yokuoyogu"]


def fetch(u, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                                  timeout=timeout).read().decode("utf-8", "replace")


def strip_white(s):
    s = re.sub(r"〔[^〕]*〕", "", s)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    s = re.sub(r"\s+", "", s)
    s = COUNTER_RX.sub("", s)
    return s.strip()


def strip_yomi(s):
    s = RT_RX.sub("", s)
    s = RP_RX.sub("", s)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    return re.sub(r"[\r\n\t]+", "", s).strip()


def scrape(url, prefix, out):
    try:
        page = fetch(url)
    except Exception as e:
        print("[FAIL] %-24s %r" % (url.rsplit("/", 1)[-1], e), flush=True)
        return 0
    pairs = PAIR_RX.findall(page)
    n = 0
    for i, (g, y) in enumerate(pairs, start=1):
        hb, yk = strip_white(g), strip_yomi(y)
        if not hb or not yk or "（" in hb or "）" in hb:
            continue
        out.append({"id": "%s-%d" % (prefix, i), "source_url": url,
                    "hakubun": hb, "expected_kakikudashi": yk})
        n += 1
    print("[PAGE] %-24s pairs %2d -> kept %2d" % (url.rsplit("/", 1)[-1], len(pairs), n),
          flush=True)
    return n


def main():
    out = []
    print("=== 8 个漏抓故事页 ===", flush=True)
    for pid in MISS:
        scrape("https://kanbun.info/koji/%s.html" % pid, pid, out)
        time.sleep(0.3)

    print("\n=== その他栏目 ===", flush=True)
    try:
        idx = fetch("https://kanbun.info/miscellaneous/miscellaneous.html")
        sub = sorted(set(LINK_RX.findall(idx)))
        print("links:", sub, flush=True)
    except Exception as e:
        print("[FAIL] miscellaneous index %r" % e, flush=True)
        sub = []
    for pid in sub:
        scrape("https://kanbun.info/miscellaneous/%s.html" % pid, "misc_" + pid, out)
        time.sleep(0.3)

    print("\n小计 %d 条" % len(out), flush=True)
    p = os.path.join(ROOT, "eval", "day16_scraped.json")
    json.dump(out, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", p, flush=True)


if __name__ == "__main__":
    main()
