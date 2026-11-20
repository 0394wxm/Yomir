# -*- coding: utf-8 -*-
"""night43_dump_page.py — 打印 book.md 的某页段落（测量辅助）。用法: ... p012 p017"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, "eval", "import_pid_11892692", "book.md"), encoding="utf-8") as f:
    lines = f.read().splitlines()

for pg in sys.argv[1:]:
    tag = "## " + pg
    if tag not in lines:
        print("[%s] not found" % pg)
        continue
    i = lines.index(tag)
    j = i + 1
    while j < len(lines) and not lines[j].startswith("## p"):
        j += 1
    print("\n".join(lines[i:j]))
    print("=" * 40)
