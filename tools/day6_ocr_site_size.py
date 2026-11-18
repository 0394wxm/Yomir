# -*- coding: utf-8 -*-
"""day6_ocr_site_size.py — OCR site-packages 各包体积（决定是否随壳打包 OCR 依赖）。"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")


def main():
    site = os.environ.get("KANBUN_OCR_SITE", r"D:\dlkotenocr-lite\site-packages")
    print("site:", site, "exists:", os.path.isdir(site))
    if not os.path.isdir(site):
        return 1
    rows = []
    for name in sorted(os.listdir(site)):
        p = os.path.join(site, name)
        if not os.path.isdir(p):
            continue
        tot = 0
        n = 0
        for dp, _, fs in os.walk(p):
            for f in fs:
                try:
                    tot += os.path.getsize(os.path.join(dp, f))
                    n += 1
                except OSError:
                    pass
        if tot > 1024 * 1024:
            rows.append((tot, name, n))
    for tot, name, n in sorted(rows, reverse=True)[:15]:
        print("  %-28s %5d files %8.1f MB" % (name, n, tot / 1048576.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
