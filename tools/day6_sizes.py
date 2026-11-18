# -*- coding: utf-8 -*-
"""day6_sizes.py — 汇总 D6 打包体积的前后对比（写报告用，全部来自实测）。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def size_of(path):
    tot = n = 0
    for dp, _, fs in os.walk(path):
        for f in fs:
            try:
                tot += os.path.getsize(os.path.join(dp, f))
                n += 1
            except OSError:
                pass
    return n, tot / 1048576.0


def group_top(root):
    agg = {}
    for dp, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root)
            parts = rel.split(os.sep)
            key = os.sep.join(parts[:3]) if parts[0] == "_internal" and len(parts) > 2 else parts[0]
            try:
                agg[key] = agg.get(key, 0) + os.path.getsize(p)
            except OSError:
                pass
    return agg


out = {}
b = os.path.join(ROOT, "dist", "kanbun-sidecar")
if os.path.isdir(b):
    n, mb = size_of(b)
    out["bundle_files"] = n
    out["bundle_mb"] = round(mb, 1)
    top = group_top(b)
    out["top20_mb"] = {k: round(v / 1048576.0, 1)
                       for k, v in sorted(top.items(), key=lambda kv: -kv[1])[:20]}

t = os.path.join(ROOT, "frontend", "src-tauri", "target", "release")
exe = os.path.join(t, "kanbun-kakikudashi.exe")
if os.path.isfile(exe):
    out["tauri_exe_mb"] = round(os.path.getsize(exe) / 1048576.0, 2)

s = os.path.join(ROOT, "frontend", "src-tauri", "sidecar")
if os.path.isdir(s):
    n2, mb2 = size_of(s)
    out["staged_files"] = n2
    out["staged_mb"] = round(mb2, 1)

# 旧版（946.8MB）的构成，来自 REPORT_DAY6 草稿与 day6 探测时的记录
out["v1_notes"] = {"total_mb": 946.8, "torch_cpu_dll_mb": 295.2,
                   "qkana_part_mb": 30.0}

print(json.dumps(out, ensure_ascii=False, indent=2))
with open(os.path.join(ROOT, "eval", "day6_sizes.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\nwritten eval/day6_sizes.json")
