# -*- coding: utf-8 -*-
"""show_one_result.py — 打印某条评测在两份结果文件里的输出对比。
用法: python -X utf8 tools/show_one_result.py <id> <fileA.json> <fileB.json>
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(p):
    full = p if os.path.isabs(p) else os.path.join(ROOT, p)
    with open(full, encoding="utf-8") as f:
        return {r["id"]: r for r in json.load(f)["results"]}


def main():
    rid, a, b = sys.argv[1], sys.argv[2], sys.argv[3]
    for name, d in (("A:" + a, load(a)), ("B:" + b, load(b))):
        r = d.get(rid)
        if r is None:
            print(name, "missing", rid)
            continue
        print(name, "dist=", r.get("edit_distance"))
        print("  got:", r.get("udkundoku_kakikudashi_norm") or r.get("udkundoku_kakikudashi", ""))
        print("  exp:", r.get("expected_kakikudashi", ""))


if __name__ == "__main__":
    main()
