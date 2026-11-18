# -*- coding: utf-8 -*-
"""night22_grep_sodashite.py — 找 而して 的产生点与规则层位置。"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS = ("style_fix", "而して")
SKIP_DIRS = {".git", "node_modules", "dist", "target", "frontend", "docs", "eval",
             "src-tauri", "__pycache__", "build", "spec", ".venv"}

for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fn in filenames:
        if not fn.endswith(".py"):
            continue
        p = os.path.join(dirpath, fn)
        try:
            lines = open(p, encoding="utf-8").read().splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for i, l in enumerate(lines):
            if any(k in l for k in KEYS):
                print("%s:%d: %s" % (os.path.relpath(p, ROOT), i + 1, l.rstrip()[:120]))
