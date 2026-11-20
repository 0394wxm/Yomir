# -*- coding: utf-8 -*-
"""night50_hash_eval.py — 记录 eval/ 下所有已跟踪文件的 sha256（N50 验证 A 用）。

用途：验证「无路径 pytest 不收集 tools/test_ocr*.py」时，
比对运行前后 eval/ 是否被改写。输出到 stdout，可直接重定向落盘。

用法: python -X utf8 tools/night50_hash_eval.py [out.json]
"""
import hashlib
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tracked_eval_files():
    p = subprocess.run(["git", "ls-files", "eval"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8")
    return [x for x in p.stdout.splitlines() if x.strip()]


def main():
    rows = {}
    for rel in tracked_eval_files():
        ab = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.isfile(ab):
            rows[rel] = None
            continue
        h = hashlib.sha256()
        with open(ab, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 16), b""):
                h.update(chunk)
        rows[rel] = h.hexdigest()
    out = {"n": len(rows), "sha256": rows}
    dst = sys.argv[1] if len(sys.argv) > 1 else None
    if dst:
        with open(dst, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
        print("[written] %s (%d files)" % (dst, len(rows)))
    else:
        print(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
