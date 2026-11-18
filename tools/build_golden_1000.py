# -*- coding: utf-8 -*-
"""
build_golden_1000.py — 把评测集扩到 1000 条（Night 26，ROADMAP「更大评测集 500-1000」）。

安全约束：**不动 eval/golden.json**（它是 D2 验收门的比对基准）。
流程：备份 golden.json 字节 → 用 build_golden.main()（GOLDEN_TOTAL=1000）生成
→ 产物挪到 eval/golden_1000.json → 原样恢复 golden.json。
顺带报告新旧前 500 条 id 的替换情况（DAY9 §9 教训：重跑会换条目）。
"""
import importlib
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
GOLDEN = os.path.join(ROOT, "eval", "golden.json")
G1000 = os.path.join(ROOT, "eval", "golden_1000.json")


def main():
    with open(GOLDEN, "rb") as f:
        orig = f.read()
    orig_ids = [x["id"] for x in json.loads(orig.decode("utf-8"))]

    os.environ["GOLDEN_TOTAL"] = "1000"
    bg = importlib.import_module("build_golden")
    importlib.reload(bg)
    bg.main()  # 覆写 eval/golden.json（随后恢复）

    with open(GOLDEN, "rb") as f:
        new = f.read()
    new_doc = json.loads(new.decode("utf-8"))
    new_ids = [x["id"] for x in new_doc]

    # 恢复原 golden.json（字节级）
    with open(GOLDEN, "wb") as f:
        f.write(orig)

    # 产物落 golden_1000.json
    with open(G1000, "w", encoding="utf-8", newline="\n") as f:
        json.dump(new_doc, f, ensure_ascii=False, indent=2)

    # 对账
    old_set = set(orig_ids[:500])
    first500_new = set(new_ids[:500])
    dropped = sorted(old_set - first500_new)
    added = sorted(first500_new - old_set)
    print("=== 对账 ===")
    print("原 golden %d 条；新抓 %d 条" % (len(orig_ids), len(new_doc)))
    print("新集前 500 与原 500 的 id 差异：减少 %d / 新增 %d" % (len(dropped), len(added)))
    if dropped:
        print("  减少:", dropped)
        print("  新增:", added)
    # expected 是否原样（前 500 交集）
    old_exp = {x["id"]: x["expected_kakikudashi"] for x in json.loads(orig.decode("utf-8"))}
    diff = [i for i in (old_set & first500_new)
            if next(x for x in new_doc if x["id"] == i)["expected_kakikudashi"] != old_exp[i]]
    print("交集内 expected 被改动的条数：%d" % len(diff))
    print("written:", G1000)


if __name__ == "__main__":
    main()
