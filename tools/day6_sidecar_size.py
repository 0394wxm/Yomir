# -*- coding: utf-8 -*-
"""day6_sidecar_size.py — 统计 PyInstaller 产物体积与头部大文件（找误收集的 torch 等）。"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")


def main(root="dist/kanbun-sidecar"):
    if not os.path.isdir(root):
        print("不存在:", root)
        return 1
    tot = n = 0
    sizes = []
    for dp, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(dp, f)
            try:
                s = os.path.getsize(p)
            except OSError:
                continue
            tot += s
            n += 1
            sizes.append((s, os.path.relpath(p, root)))
    print("%s: %d files, %.1f MB" % (root, n, tot / 1048576.0))
    print("\n最大的 20 个:")
    for s, p in sorted(sizes, reverse=True)[:20]:
        print("  %8.1f MB  %s" % (s / 1048576.0, p))

    # 按顶层目录聚合
    agg = {}
    for s, p in sizes:
        top = p.split(os.sep)[0] if os.sep in p else "(root)"
        agg[top] = agg.get(top, 0) + s
    print("\n按顶层聚合:")
    for k, v in sorted(agg.items(), key=lambda kv: -kv[1])[:20]:
        print("  %-40s %8.1f MB" % (k, v / 1048576.0))
    return 0


if __name__ == "__main__":
    sys.exit(main(*(sys.argv[1:] or [])))
