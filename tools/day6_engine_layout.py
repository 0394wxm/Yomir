# -*- coding: utf-8 -*-
"""day6_engine_layout.py — 看清 udkundoku/unidic2ud 的目录结构，决定打包策略。"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")


def main():
    import udkundoku
    import unidic2ud

    for name, mod in (("udkundoku", udkundoku), ("unidic2ud", unidic2ud)):
        p = os.path.dirname(os.path.abspath(mod.__file__))
        print("=== %s -> %s" % (name, p))
        for dp, dns, fs in os.walk(p):
            rel = os.path.relpath(dp, p)
            depth = 0 if rel == "." else rel.count(os.sep) + 1
            if depth > 2:
                dns[:] = []
                continue
            tot = sum(os.path.getsize(os.path.join(dp, f)) for f in fs
                      if os.path.exists(os.path.join(dp, f)))
            big = [(f, round(os.path.getsize(os.path.join(dp, f)) / 1048576.0, 1))
                   for f in fs if os.path.getsize(os.path.join(dp, f)) > 3 * 1048576]
            print("  %-46s %4d files %8.1f MB %s"
                  % (rel, len(fs), tot / 1048576.0, big if big else ""))
        print()


if __name__ == "__main__":
    main()
