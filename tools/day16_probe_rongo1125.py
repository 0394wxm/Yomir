# -*- coding: utf-8 -*-
"""day16_probe_rongo1125.py — 查 rongo1125 页面的成对结构与过滤原因。"""
import html as html_mod
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}
PAIR_RX = re.compile(r'<div class="genbun01">(.*?)</div>\s*<div class="yomi0([23])">(.*?)</div>', re.S)
TAG_RX = re.compile(r"<[^>]+>")
RT_RX = re.compile(r"<rt>.*?</rt>", re.S)
RP_RX = re.compile(r"<rp>.*?</rp>", re.S)


def main():
    u = "https://kanbun.info/keibu/rongo1125.html"
    t = urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                              timeout=35).read().decode("utf-8", "replace")
    print("len", len(t), flush=True)
    print("genbun01 count:", t.count('class="genbun01"'), flush=True)
    for m in re.finditer(r'class="(genbun\d\d|yomi\d\d)"', t):
        print("  class", m.group(1), flush=True)
    pairs = PAIR_RX.findall(t)
    print("pairs:", len(pairs), flush=True)
    for g, yv, y in pairs:
        hb = re.sub(r"\s+", "", html_mod.unescape(TAG_RX.sub("", g)))
        yk = re.sub(r"[\r\n\t]+", "", html_mod.unescape(TAG_RX.sub("", RT_RX.sub("", RP_RX.sub("", y)))))
        print("  yomi%s | hb=%r | has_paren=%s" % (yv, hb[:60], ("（" in hb or "）" in hb)), flush=True)
        print("           yk=%r" % yk[:60], flush=True)


if __name__ == "__main__":
    main()
