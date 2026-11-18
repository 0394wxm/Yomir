# -*- coding: utf-8 -*-
"""grep_repo.py — 在仓库源码里搜关键词，打印 文件:行号:内容。"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

kws = sys.argv[1:]
SKIP = {".git", "node_modules", "__pycache__", "dist", "ocr_runtime", ".venv"}
EXTS = (".py", ".ts", ".tsx", ".js", ".bat", ".md")
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP]
    for fn in filenames:
        if not fn.endswith(EXTS):
            continue
        p = os.path.join(dirpath, fn)
        try:
            lines = io.open(p, encoding="utf-8", errors="ignore").read().split("\n")
        except Exception:
            continue
        for i, ln in enumerate(lines, 1):
            if any(k in ln for k in kws):
                rel = os.path.relpath(p, ROOT)
                print("%s:%d: %s" % (rel, i, ln.strip()[:150]))
