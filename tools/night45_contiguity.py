# -*- coding: utf-8 -*-
"""night45_contiguity.py — 列连续性指标（NIGHT45 独立质量度量）。

为什么需要它：最初的「头注错位」度量与原型（P1 头注归列）同源，
「重排后违规=0」是循环论证。本脚本用**与原型无关**的指标：

  列连续性（column contiguity）
    1. 列定义 = 生产代码 `_cluster_order` 的同一算法（x 重叠 ≥0.4 的传递闭包，
       按右缘 x 降序）。列定义必须与生产一致，否则测的是工具自己的构造。
    2. 理想阅读顺序里同一列应当连续出现（竖排逐列读完再换列）。
    3. 度量 excess = 列序列段数(runs) − 列数。理想 0；每被别的列打断一次 +1。

对比三种顺序：
  A 生产顺序（cluster，已存档 filter=ON 输出）
  B P1 头注归列（已废弃的 Night45 原型，保留作否证证据）
  C 纯列序（恒 0，上界参照）

**结论（本次运行）**：A 在 659 列上零打断（43/43 页每列连续），B 反而
48 处打断、31 页变差 → P1 废弃。列连续性对 A 是构造性质（`_cluster_order`
以列单元整体输出），因此本指标只能用来**否证**会切开列的重排，不能用来
证明 A 优于别的顺序；正向证据见 night45_maincol_order.py 的 I5。

产出: eval/night45_contiguity.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import MAIN_COL_OVERLAP  # noqa: E402
from tools.night45_cluster_proto import order_v1  # noqa: E402

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night45_contiguity.json")


def ov_x(a, b):
    lo = max(a["x"], b["x"])
    hi = min(a["x"] + a["w"], b["x"] + b["w"])
    return max(0, hi - lo) / max(1, min(a["w"], b["w"]))


def build_columns(boxes):
    """列定义 = `_cluster_order` 的竖排分支（x 重叠传递闭包），右→左排序。"""
    cols = []
    for i in sorted(range(len(boxes)), key=lambda i: -(boxes[i]["x"] + boxes[i]["w"])):
        b = boxes[i]
        for c in cols:
            if any(ov_x(b, boxes[j]) >= MAIN_COL_OVERLAP for j in c):
                c.append(i)
                break
        else:
            cols.append([i])
    cols.sort(key=lambda c: -max(boxes[i]["x"] + boxes[i]["w"] for i in c))
    return cols


def runs_of(seq):
    if not seq:
        return 0
    r = 1
    for k in range(1, len(seq)):
        if seq[k] != seq[k - 1]:
            r += 1
    return r


def main():
    pages = []
    for fn in sorted(os.listdir(FULL)):
        if fn.endswith(".json"):
            with open(os.path.join(FULL, fn), encoding="utf-8") as f:
                pages.append(json.load(f))

    rows = []
    tot_a = tot_c = tot_cols = 0
    for p in pages:
        boxes = [dict(b, index=i) for i, b in enumerate(p["line_boxes"])]
        if len(boxes) < 4:
            continue
        cols = build_columns(boxes)
        if len(cols) < 2:
            continue
        cid = {}
        for k, c in enumerate(cols):
            for i in c:
                cid[i] = k

        runs_a = runs_of([cid[i] for i in order_v1(boxes)])
        runs_c = len(cols)  # 纯列序：每列恰好一段

        n = len(cols)
        tot_a += runs_a - n
        tot_c += runs_c - n
        tot_cols += n
        rows.append({"page": p["page"], "n": len(boxes), "n_cols": n,
                     "excess_A": runs_a - n, "excess_C": runs_c - n})

    print("== 列连续性（runs − n_cols；0 = 每列连续）==")
    print("pages=%d  列合计=%d" % (len(rows), tot_cols))
    print("A 生产 cluster   打断合计=%d" % tot_a)
    print("C 纯列序(上界)   打断合计=%d" % tot_c)
    print("A 完美页数: %d / %d"
          % (sum(1 for r in rows if r["excess_A"] == 0), len(rows)))
    bad = [r["page"] for r in rows if r["excess_A"] > 0]
    print("A 有打断的页: %s" % (bad or "无"))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"total_cols": tot_cols, "excess_A": tot_a,
                   "excess_C": tot_c, "pages": rows}, f,
                  ensure_ascii=False, indent=1)
    print("\n[written] eval/night45_contiguity.json")


if __name__ == "__main__":
    main()
