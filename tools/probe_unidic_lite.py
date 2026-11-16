# -*- coding: utf-8 -*-
# Probe: unidic_lite MeCab output column layout (compatibility check for udkundoku's QKANA usage)
import sys, os, unidic_lite
sys.stdout.reconfigure(encoding="utf-8")
from MeCab import Tagger

d = unidic_lite.DICDIR.replace("\\", "/")
t = Tagger("-r %s/mecabrc -d %s" % (d, d))

for text in sys.argv[1:] or ["顧左右而言他", "到着", "甚"]:
    print("=== input:", text)
    r = t.parse(text)
    for line in r.splitlines():
        if "\t" not in line:
            print("META:", line)
            continue
        surf, rest = line.split("\t", 1)
        cols = rest.split(",")
        print("surface=%s cols=%d" % (surf, len(cols)))
        for i, c in enumerate(cols):
            print("   [%02d] %s" % (i, c))
