# -*- coding: utf-8 -*-
"""day16_scrape_classics.py — 补抓 大学(daigaku) + 孝経(kokyo) 章节成对文本。

页面结构与故事部一致（genbun01 + yomi02）。带缓存、重试、限速。
产物 eval/day16_classics.json。
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
PAIR_RX = re.compile(r'<div class="genbun01">(.*?)</div>\s*<div class="yomi02">(.*?)</div>', re.S)
COUNTER_RX = re.compile(r"^\d{2,3}\s*（?\d{0,2}-?\d{0,2}）?")
LINK_RX = re.compile(r'href="([a-z0-9_]+\.html)"')


def get(u, tries=3, timeout=35):
    last = None
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                                          timeout=timeout).read().decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(1.5 + i * 2)
    print("[FAIL] %-40s %r" % (u.rsplit("/", 1)[-1], last), flush=True)
    return ""


def strip_white(s):
    s = re.sub(r"〔[^〕]*〕", "", s)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"^\d{2,3}(（\d{2}-\d{2}）)?", "", s)
    return s.strip()


def strip_yomi(s):
    s = RT_RX.sub("", s)
    s = RP_RX.sub("", s)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    return re.sub(r"[\r\n\t]+", "", s).strip()


def scrape_index(prefix, link_prefix=None):
    idx = "https://kanbun.info/keibu/%s.html" % prefix
    lp = link_prefix or prefix
    t = get(idx)
    if not t:
        return []
    subs = sorted({h for h in LINK_RX.findall(t)
                   if h.startswith(lp) and h != prefix + ".html"})
    print("=== %s 章节页 %d 个 ===" % (prefix, len(subs)), flush=True)
    out = []
    for h in subs:
        u = "https://kanbun.info/keibu/" + h
        page = get(u)
        if not page:
            continue
        pairs = PAIR_RX.findall(page)
        n = 0
        pid = h[:-5]
        for i, (g, y) in enumerate(pairs, start=1):
            hb, yk = strip_white(g), strip_yomi(y)
            if not hb or not yk or "（" in hb or "）" in hb:
                continue
            out.append({"id": "%s-%d" % (pid, i), "source_url": u,
                        "hakubun": hb, "expected_kakikudashi": yk, "work": prefix})
            n += 1
        print("  %-22s pairs %2d -> kept %2d" % (h, len(pairs), n), flush=True)
        time.sleep(0.4)
    return out


def main():
    out = []
    for p, lp in (("daigaku00", "daigaku"), ("kokyo00", "kokyo")):
        out += scrape_index(p, lp)
    print("\n小计 %d 条" % len(out), flush=True)
    p = os.path.join(ROOT, "eval", "day16_classics.json")
    json.dump(out, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", p, flush=True)


if __name__ == "__main__":
    main()
