# -*- coding: utf-8 -*-
"""night43_verify_book.py — 验证「book.md 重处理零错滤正文行」（NIGHT43 验收项）。

对 6 个配对页（p005/p012/p017/p019/p020/p033）：
  1. 从 night43_pair.json（**已开版面过滤**的产品流输出）取每页行文本；
  2. 从 eval/import_pid_11892692/book.md（Night42 旧输出，**未过滤**）取同页白文行；
  3. 求「旧有 → 新无」= 被删行集合，逐个核对是否在 noise 白名单（=合法滤除）。
硬门：被删行中不在 noise 白名单的正文行必须为 0。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL = os.path.join(ROOT, "eval")


def book_lines():
    """取 book.md 每页的**白文段**（第一段 ``` 代码块）；書き下し文段不参与对比。"""
    with open(os.path.join(EVAL, "import_pid_11892692", "book.md"), encoding="utf-8") as f:
        lines = f.read().splitlines()
    out, page, in_block, seen_block = {}, None, False, False
    for l in lines:
        if l.startswith("## p"):
            page = l.split()[1]
            out[page] = []
            in_block = False
            seen_block = False
            continue
        if page is None:
            continue
        if l.strip() == "```":
            if not seen_block:
                in_block = not in_block
                if not in_block:
                    seen_block = True   # 白文段结束
            continue
        if in_block and not seen_block:
            out[page].append(l)
    return out


def main():
    with open(os.path.join(EVAL, "night43_pair.json"), encoding="utf-8") as f:
        pair = {p["page"]: p for p in json.load(f)["pages"]}
    with open(os.path.join(EVAL, "night43_labels.json"), encoding="utf-8") as f:
        labels = json.load(f)
    old = book_lines()

    total_removed = total_wrong = total_kept = 0
    for pg in sorted(pair):
        new_texts = [p["text"] for p in pair[pg]["pairs"]]
        old_texts = old.get(pg, [])
        noise = set(labels.get(pg, {}).get("noise", []))
        # 多重集差：old - new（按计数）
        from collections import Counter
        removed = list((Counter(old_texts) - Counter(new_texts)).elements())
        added = list((Counter(new_texts) - Counter(old_texts)).elements())
        wrong = [t for t in removed if t not in noise]
        total_removed += len(removed)
        total_wrong += len(wrong)
        total_kept += len(new_texts)
        print("== %s old=%d new=%d removed=%d (noise-ok=%d WRONG=%d) added=%d"
              % (pg, len(old_texts), len(new_texts), len(removed),
                 len(removed) - len(wrong), len(wrong), len(added)))
        for t in removed:
            mark = "OK  " if t in noise else "WRONG"
            print("   %s %r" % (mark, t))
        if added:
            print("   [added rows — 过滤不可能新增行，说明识别有随机性/行序差异]")
            for t in added[:10]:
                print("     + %r" % (t,))

    print("\nTOTAL: removed=%d wrong=%d kept=%d" % (total_removed, total_wrong, total_kept))
    print("HARD GATE 错滤正文行 = %d（必须 0）: %s" % (total_wrong, "PASS" if total_wrong == 0 else "FAIL"))


if __name__ == "__main__":
    main()
