# -*- coding: utf-8 -*-
"""scan_roadmap.py — 在 ROADMAP.md 里定位 D4/D6/D7/D8 与「2.4s」相关条目。"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

t = io.open(os.path.join(ROOT, "ROADMAP.md"), encoding="utf-8").read()
lines = t.split("\n")
for i, ln in enumerate(lines):
    if any(k in ln for k in ("2.4", "缓存", "cached", "progress", "進捗", "sidecar", "Tauri")):
        print("%4d | %s" % (i + 1, ln))
