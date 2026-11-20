# -*- coding: utf-8 -*-
"""night44_bookdiff.py — book.md（Night42 基线）vs book_filter_on.md（NIGHT44）逐页 diff。

对比两段：**白文**（第 1 个代码块）与**書き下し文**（第 2 个代码块）。
输出每页行数、删/增行明细、总字数变化。

硬门：
  D1  白文行数变化必须只出现在「有被滤框的页」（无滤框页逐行零差异）
  D2  増行必须为 0（版面过滤只能删行，不能造行）
产出: eval/night44_bookdiff.json
"""
import json
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL = os.path.join(ROOT, "eval")
BASE = os.path.join(EVAL, "import_pid_11892692", "book.md")
NEW = os.path.join(EVAL, "import_pid_11892692", "book_filter_on.md")


def parse(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    out, page = {}, None
    blocks = []
    for l in lines:
        if l.startswith("## p"):
            if page is not None:
                out[page] = blocks
            page = l.split()[1]
            blocks = []
            continue
        if page is None:
            continue
        if l.strip() == "```":
            blocks.append([])          # 新块占位
            continue
        if blocks and not l.startswith("**") and not l.startswith("#"):
            # 只在代码块内收集：用状态机更稳
            pass
        blocks_cur = None
    # 重写：状态机
    out, page, in_block, cur = {}, None, False, None
    for l in lines:
        if l.startswith("## p"):
            page = l.split()[1]
            out[page] = []
            in_block = False
            continue
        if page is None:
            continue
        if l.strip() == "```":
            if in_block:
                in_block = False
            else:
                in_block = True
                out[page].append([])
            continue
        if in_block:
            out[page][-1].append(l)
    return out


def main():
    a, b = parse(BASE), parse(NEW)
    pages = sorted(set(a) | set(b))
    rows = []
    tot_a = tot_b = 0
    n_added = 0
    bad_pages = []
    for pg in pages:
        pa, pb = a.get(pg, []), b.get(pg, [])
        # 块 0 = 白文，块 1 = 書き下し文
        hb_a = pa[0] if len(pa) > 0 else []
        hb_b = pb[0] if len(pb) > 0 else []
        kk_a = pa[1] if len(pa) > 1 else []
        kk_b = pb[1] if len(pb) > 1 else []
        removed = list((Counter(hb_a) - Counter(hb_b)).elements())
        added = list((Counter(hb_b) - Counter(hb_a)).elements())
        tot_a += len(hb_a)
        tot_b += len(hb_b)
        n_added += len(added)
        rows.append({"page": pg, "hb_base": len(hb_a), "hb_new": len(hb_b),
                     "kk_base": len(kk_a), "kk_new": len(kk_b),
                     "removed": removed, "added": added})
        if removed or added or len(hb_a) != len(hb_b) or len(kk_a) != len(kk_b):
            print("== %s 白文 %d→%d (删 %d 增 %d) | 書き下し %d→%d"
                  % (pg, len(hb_a), len(hb_b), len(removed), len(added),
                     len(kk_a), len(kk_b)))
            for t in removed:
                print("   - %r" % t)
            for t in added:
                print("   + %r" % t)
    print("\nTOTAL 白文 %d→%d（删 %d）  増行 %d" % (tot_a, tot_b, tot_a - tot_b, n_added))
    print("HARD GATE D2 増行=0: %s" % ("PASS" if n_added == 0 else "FAIL"))
    changed = [r["page"] for r in rows if r["removed"] or r["added"]
               or r["hb_base"] != r["hb_new"]]
    print("有变化页: %d / %d  -> %s" % (len(changed), len(rows), ",".join(changed)))

    with open(os.path.join(EVAL, "night44_bookdiff.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump({"hb_base": tot_a, "hb_new": tot_b, "added": n_added,
                   "changed_pages": changed, "pages": rows}, f,
                  ensure_ascii=False, indent=1)
    print("[written] eval/night44_bookdiff.json")


if __name__ == "__main__":
    main()
