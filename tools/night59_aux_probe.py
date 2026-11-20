# -*- coding: utf-8 -*-
"""night59_aux_probe.py — N59：定位 udkundoku AUX 表本体与助動詞/必要 相关联键。只读诊断。"""
import importlib.util
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

import udkundoku  # noqa: E402  仅用于定位包目录

pkg_dir = os.path.dirname(udkundoku.__file__)
src_path = os.path.join(pkg_dir, "udkundoku.py")
src = io.open(src_path, encoding="utf-8", errors="replace").read()
lines = src.splitlines()
out_lines = ["udkundoku 子模块: " + src_path]
for i, l in enumerate(lines, 1):
    if "AUX" in l:
        out_lines.append("%5d: %s" % (i, l))

out_lines.append("")
m = re.search(r"from\s+(\S+)\s+import[^\n]*AUX", src)
out_lines.append("AUX import 来源: %s" % (m.group(0).strip() if m else "（无 from-import）"))

# 直接 import AUX 来源模块
if m:
    target = m.group(1)
    out_lines.append("来源模块: %s" % target)
    try:
        mod = importlib.import_module(target)
        aux = getattr(mod, "AUX", None)
        out_lines.append("来源文件: %s" % getattr(mod, "__file__", "?"))
        if aux is None:
            out_lines.append("该模块无 AUX 属性；模块级名: %s"
                             % [x for x in dir(mod) if not x.startswith("_")][:30])
        else:
            keys = list(aux.keys())
            out_lines.append("AUX 键总数: %d" % len(keys))
            nec = sorted(k for k in keys if ",助動詞," in k)
            out_lines.append("助動詞类键 %d 个:" % len(nec))
            for k in nec:
                out_lines.append("  %s -> %r" % (k, aux[k]))
            out_lines.append("")
            out_lines.append("xpos=v,助動詞,必要 的键: %s"
                             % [k for k in keys if ",v,助動詞,必要,*" in k])
            out_lines.append("含「應」的键: %s" % [k for k in keys if "應" in k])
            out_lines.append("含「応」的键: %s" % [k for k in keys if "応" in k])
    except Exception as e:
        out_lines.append("import AUX 来源失败: %r" % (e,))

txt = "\n".join(out_lines)
io.open(os.path.join(EV, "night59_aux_probe.txt"), "w", encoding="utf-8",
        newline="\n").write(txt + "\n")
print(txt, flush=True)
