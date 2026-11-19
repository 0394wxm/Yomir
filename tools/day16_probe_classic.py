# -*- coding: utf-8 -*-
"""day16_probe_classic.py — 大学/孝経章节页结构探测（genbun01 + yomi?? 是否成对）。"""
import collections
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}


def get(u):
    try:
        return urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                                      timeout=25).read().decode("utf-8", "replace")
    except Exception as e:
        print("[FAIL] %-40s %r" % (u.rsplit("/", 1)[-1], e), flush=True)
        return ""


def main():
    for u in ("https://kanbun.info/keibu/daigaku02.html",
              "https://kanbun.info/keibu/daigaku00a.html",
              "https://kanbun.info/keibu/kokyo01.html"):
        t = get(u)
        if not t:
            continue
        c = collections.Counter(re.findall(r'class="([a-z0-9_]+)"', t))
        print("=== %-28s len %5d ===" % (u.rsplit("/", 1)[-1], len(t)), flush=True)
        print("  classes:", [(k, v) for k, v in c.most_common(10)], flush=True)
        for cls in ("genbun01", "genbun02", "yomi02", "yomi03", "yomi01"):
            print("  %-9s %d" % (cls, len(re.findall(r'class="%s"' % cls, t))), flush=True)
        m = re.search(r'<div class="genbun0?1">(.{0,300})', t, re.S)
        if m:
            print("  sample:", re.sub(r"\s+", " ", m.group(1))[:280], flush=True)
        m2 = re.search(r'<div class="yomi0?\d">(.{0,300})', t, re.S)
        if m2:
            print("  yomi  :", re.sub(r"<[^>]+>", "", m2.group(1))[:200], flush=True)


if __name__ == "__main__":
    main()
