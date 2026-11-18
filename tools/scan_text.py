# -*- coding: utf-8 -*-
"""scan_text.py — 在指定文件里搜关键词并打印上下文。"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

path = sys.argv[1]
kws = sys.argv[2:]
t = io.open(os.path.join(ROOT, path), encoding="utf-8").read()
lines = t.split("\n")
for i, ln in enumerate(lines):
    if any(k in ln for k in kws):
        print("%4d | %s" % (i + 1, ln))
