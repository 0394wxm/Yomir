# -*- coding: utf-8 -*-
"""day16_probe_misc.py — 探「その他」栏目（大学/孝経/中庸等）是否可抓成对文本。"""
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
        print("[FAIL] %-46s %r" % (u, e), flush=True)
        return ""


def main():
    t = get("https://kanbun.info/miscellaneous/miscellaneous.html")
    print("len", len(t), flush=True)
    for m in re.finditer(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', t, re.S):
        href = m.group(1)
        txt = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if href.endswith(".html"):
            print("  %-40s %s" % (href, txt), flush=True)

    print("\n=== 试探 keibu/ 下 大学 孝経 中庸 ===", flush=True)
    for pid in ("daigaku", "kokyo", "chuyo", "daigaku00", "kokyo00", "chuyo00"):
        for base in ("keibu", "miscellaneous"):
            u = "https://kanbun.info/%s/%s.html" % (base, pid)
            t2 = get(u)
            if t2:
                import re as _r
                n = len(_r.findall(r'<div class="genbun01">', t2))
                print("  HIT %-46s len %5d genbun01 %d" % (u, len(t2), n), flush=True)


if __name__ == "__main__":
    main()
