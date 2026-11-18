# -*- coding: utf-8 -*-
"""day6_show_fetch.py — 打印 App.tsx 里所有 fetch 调用，供改成 API 前缀。"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "frontend", "src", "App.tsx")
s = io.open(p, encoding="utf-8").read()
for i, line in enumerate(s.split("\n"), 1):
    if "fetch(" in line:
        print("%4d | %s" % (i, line.strip()))
