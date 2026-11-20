# -*- coding: utf-8 -*-
"""night50_cmp_hash.py — 比对两份 eval/ sha256 快照（N50 验证 A 用）。

用法: python -X utf8 tools/night50_cmp_hash.py before.json after.json
退出码: 0 = 完全一致；1 = 有差异（列出差异文件）
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")


def main():
    if len(sys.argv) < 3:
        raise SystemExit("usage: night50_cmp_hash.py before.json after.json")
    a = json.load(open(sys.argv[1], encoding="utf-8"))["sha256"]
    b = json.load(open(sys.argv[2], encoding="utf-8"))["sha256"]
    keys = sorted(set(a) | set(b))
    changed, missing, added = [], [], []
    for k in keys:
        av, bv = a.get(k), b.get(k)
        if av is None and bv is not None:
            added.append(k)
        elif av is not None and bv is None:
            missing.append(k)
        elif av != bv:
            changed.append(k)
    print("快照 A: %d 文件；快照 B: %d 文件；并集 %d"
          % (len(a), len(b), len(keys)))
    print("  sha256 变化: %d" % len(changed))
    for k in changed:
        print("    %s" % k)
    print("  A 有 B 无: %d %s" % (len(missing), missing[:5]))
    print("  B 有 A 无: %d %s" % (len(added), added[:5]))
    if changed or missing or added:
        print("\nverdict: DIFF")
        sys.exit(1)
    print("\nverdict: IDENTICAL")


if __name__ == "__main__":
    main()
