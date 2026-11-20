# -*- coding: utf-8 -*-
"""night49_gt_diff.py — 对比 Night44 与 Night49 的 GT 页输出，确认排序是否动了。

CER 不变可能是「排序没动」也可能是「动了但 CER 不敏感」。必须区分。
按框坐标配对，报告：
  - 行集合是否相同
  - 输出序列是否相同（顺序）
  - 逐页列出顺序变化
  - 检查 GT 页里是否存在割注对（A_strict 口径）

用法: python -X utf8 tools/night49_gt_diff.py
产出: eval/night49_gt_diff.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

A = os.path.join(ROOT, "eval", "night44_gt_lines.json")
B = os.path.join(ROOT, "eval", "night49_gt_lines.json")
OUT = os.path.join(ROOT, "eval", "night49_gt_diff.json")


def key(b):
    return (b["x"], b["y"], b["w"], b["h"])


def main():
    a = json.load(open(A, encoding="utf-8"))
    b = json.load(open(B, encoding="utf-8"))
    ra = {r["file"]: r for r in a["results"]}
    rb = {r["file"]: r for r in b["results"]}

    rows = []
    n_order_changed = 0
    n_set_changed = 0
    for f in sorted(set(ra) & set(rb)):
        la, lb = ra[f]["lines"], rb[f]["lines"]
        ka = [key(x) for x in la]
        kb = [key(x) for x in lb]
        set_same = sorted(ka) == sorted(kb)
        seq_same = ka == kb
        if not set_same:
            n_set_changed += 1
        if not seq_same:
            n_order_changed += 1
        # 找第一个差异位置
        first = None
        for i in range(min(len(ka), len(kb))):
            if ka[i] != kb[i]:
                first = i
                break
        rec = {"file": f, "n_a": len(la), "n_b": len(lb),
               "set_same": set_same, "seq_same": seq_same,
               "first_diff": first}
        if not seq_same and set_same:
            # 列出 a 中位置 first 之后的局部
            rec["a_slice"] = [
                {"pos": i, "box": ka[i],
                 "text": la[i]["text"][:30]}
                for i in range(max(0, (first or 0) - 2),
                               min(len(la), (first or 0) + 5))]
            rec["b_slice"] = [
                {"pos": i, "box": kb[i],
                 "text": lb[i]["text"][:30]}
                for i in range(max(0, (first or 0) - 2),
                               min(len(lb), (first or 0) + 5))]
        rows.append(rec)

    print("== Night44 vs Night49 GT 输出 ==")
    print("  GT 页: %d" % len(rows))
    print("  行集合不同的页: %d" % n_set_changed)
    print("  输出顺序不同的页: %d" % n_order_changed)
    for r in rows:
        flag = "ORDER-CHANGED" if not r["seq_same"] else "same"
        print("  %-28s n=%2d/%2d  %s  first_diff=%s"
              % (r["file"], r["n_a"], r["n_b"], flag, r["first_diff"]))
        if not r["seq_same"] and r.get("a_slice"):
            print("     改前:")
            for x in r["a_slice"]:
                print("       %2d %r" % (x["pos"], x["text"]))
            print("     改后:")
            for x in r["b_slice"]:
                print("       %2d %r" % (x["pos"], x["text"]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"rows": rows, "order_changed": n_order_changed,
                   "set_changed": n_set_changed}, f,
                  ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_gt_diff.json")


if __name__ == "__main__":
    main()
