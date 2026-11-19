# -*- coding: utf-8 -*-
"""day16_recap_gap.py — 平行语料里被「每页 10 对」上限截断的页面，实际还有多少对？

只读诊断：对 corpus 中正好 10 行的页面重新取页面（优先用 %TEMP%\\kanbun_cache），
统计全页 PAIR_RX 命中数，并判断多出来的成对文本是否构成「新唯一白文」。
"""
import collections
import html as html_mod
import json
import os
import re
import sys
import tempfile
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(tempfile.gettempdir(), "kanbun_cache")
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}

TAG_RX = re.compile(r"<[^>]+>")
RT_RX = re.compile(r"<rt>.*?</rt>", re.S)
RP_RX = re.compile(r"<rp>.*?</rp>", re.S)
PAIR_RX = re.compile(r'<div class="genbun01">(.*?)</div>\s*<div class="yomi02">(.*?)</div>', re.S)


def cache_path(url):
    key = re.sub(r"[^a-z0-9]+", "_", url.lower())
    return os.path.join(CACHE, key[-120:] + ".html")


def get(url):
    cp = cache_path(url)
    if os.path.exists(cp) and os.path.getsize(cp) > 500:
        return open(cp, encoding="utf-8", errors="replace").read(), "cache"
    txt = urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                 timeout=30).read().decode("utf-8", "replace")
    os.makedirs(CACHE, exist_ok=True)
    open(cp, "w", encoding="utf-8", newline="\n").write(txt)
    return txt, "net"


def strip_white(s):
    s = re.sub(r"〔[^〕]*〕", "", s)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    return re.sub(r"\s+", "", s).strip()


def strip_yomi(s):
    s = RT_RX.sub("", s)
    s = RP_RX.sub("", s)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    return re.sub(r"[\r\n\t]+", "", s).strip()


def main():
    par = json.load(open(os.path.join(ROOT, "eval", "kanbun_parallel.json"), encoding="utf-8"))
    g1 = json.load(open(os.path.join(ROOT, "eval", "golden_1000.json"), encoding="utf-8"))
    seen = {x["hakubun"].strip() for x in g1}
    seen |= {x["hakubun"].strip() for x in par}

    per_page = collections.Counter(x["source_url"] for x in par)
    capped = [u for u, n in per_page.items() if n >= 10]
    print("capped pages:", len(capped), flush=True)

    extra_rows = 0
    extra_new = 0
    for u in capped:
        try:
            page, src = get(u)
        except Exception as e:
            print("[FAIL] %-50s %r" % (u.rsplit("/", 1)[-1], e), flush=True)
            continue
        pairs = PAIR_RX.findall(page)
        have = per_page[u]
        added = 0
        newu = 0
        for genbun, yomi in pairs:
            hb = strip_white(genbun)
            yk = strip_yomi(yomi)
            if not hb or not yk or "（" in hb or "）" in hb:
                continue
            if hb in seen:
                continue
            seen.add(hb)
            newu += 1
        extra_rows += max(0, len(pairs) - have)
        extra_new += newu
        print("%-46s rows %2d | page pairs %2d | +new %2d (%s)"
              % (u.rsplit("/", 1)[-1], have, len(pairs), newu, src), flush=True)

    print("\n潜在额外行 %d | 潜在额外新唯一 %d" % (extra_rows, extra_new), flush=True)


if __name__ == "__main__":
    main()
