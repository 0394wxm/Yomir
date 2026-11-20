# -*- coding: utf-8 -*-
"""night49_warichu_order.py — 割注在阅读顺序里是怎么被排的（首个实测）。

Night48 发现 94% 的窄框是双行割注。这引出一个**生产代码层面的问题**：
`_cluster_order` 的列聚类用 `overlap_x = inter / max(1, min(w_a, w_b))`，
窄框（w=18）完全落在主栏（w=54）的 x 范围内时比值 = 1.0 → **割注会被并进
主栏列**，然后整列按 y 排序。

理论推断：割注是「插在正文流中间」的，按 y 排序后应该得到
「上方正文 → 割注（右半→左半）→ 下方正文」= **正确**的阅读顺序。
但这从来没被验证过。本脚本实测。

检验项（每页）：
  Q1 割注对的两半是否落在**同一个列单元**里？
  Q2 若是，两半在列内的相对顺序是否「右半先、左半后」？
  Q3 割注对是否**连续**（中间不夹别的框）？
  Q4 割注对前面是否有正文、后面是否有正文（即是否插在流中间）？

同时统计反例（右左颠倒 / 被拆到不同列 / 不连续），逐条列出。

只测量，不改代码。
产出: eval/night49_warichu_order.json
用法: python -X utf8 tools/night49_warichu_order.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import (  # noqa: E402
    _main_group, _median, judge_headnote_strip, judge_layout, main_column_keys,
)

OFF = os.path.join(ROOT, "eval", "night44_full", "filter_off")
OUT = os.path.join(ROOT, "eval", "night49_warichu_order.json")


def ov(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def overlap_x(a, b):
    inter = ov(a["x"], a["x"] + a["w"], b["x"], b["x"] + b["w"])
    return inter / max(1, min(a["w"], b["w"]))


def cluster_order(boxes):
    """复刻 backend/ocr_engine.py 的 _cluster_order（縦書き路径），不依赖引擎。

    返回 (order_idx, units)，units 是 [[box,...], ...] 按输出顺序。
    """
    vert = [b for b in boxes if b["h"] >= b["w"]]
    units = []
    for b in sorted(vert, key=lambda t: -(t["x"] + t["w"])):
        placed = False
        for u in units:
            if overlap_x(u["box"], b) >= 0.4:
                u["items"].append(b)
                u["box"] = {
                    "x": min(u["box"]["x"], b["x"]),
                    "y": min(u["box"]["y"], b["y"]),
                    "w": max(u["box"]["x"] + u["box"]["w"],
                             b["x"] + b["w"]) - min(u["box"]["x"], b["x"]),
                    "h": max(u["box"]["y"] + u["box"]["h"],
                             b["y"] + b["h"]) - min(u["box"]["y"], b["y"]),
                }
                placed = True
                break
        if not placed:
            units.append({"box": dict(b), "items": [b]})
    for u in units:
        u["items"] = sorted(u["items"], key=lambda t: t["y"])
    units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
    return [u["items"] for u in units]


def find_pairs(thin, wmed):
    """返回 [(a, b)]，a 为右半（x 更大），b 为左半。"""
    used = set()
    pairs = []
    for a in sorted(thin, key=lambda t: -(t["x"] + t["w"])):
        if id(a) in used:
            continue
        for b in thin:
            if b is a or id(b) in used:
                continue
            if ov(a["x"], a["x"] + a["w"], b["x"], b["x"] + b["w"]) > 0:
                continue
            gap = min(abs(a["x"] - (b["x"] + b["w"])),
                      abs(b["x"] - (a["x"] + a["w"])))
            if gap > 1.2 * wmed:
                continue
            yo = ov(a["y"], a["y"] + a["h"], b["y"], b["y"] + b["h"])
            if yo < 0.7 * min(a["h"], b["h"]):
                continue
            if a["w"] + b["w"] + gap > 1.35 * wmed:
                continue
            if a["x"] < b["x"]:
                a, b = b, a
            used.add(id(a))
            used.add(id(b))
            pairs.append((a, b))
            break
    return pairs


def main():
    pages = []
    for fn in sorted(os.listdir(OFF)):
        if fn.endswith(".json"):
            pages.append(json.load(open(os.path.join(OFF, fn), encoding="utf-8")))

    tot_pairs = 0
    q1_same_col = 0
    q2_right_first = 0
    q3_contiguous = 0
    q4_has_above = 0
    q4_has_below = 0
    problems = []
    detail = []

    for q in pages:
        bx = [dict(b) for b in q["line_boxes"]]
        if len(bx) < 4:
            continue
        _mi, jd = judge_layout(bx)
        ki = [i for i, (b, r) in enumerate(jd) if r is None]
        kp = [bx[i] for i in ki]
        vt = [b for b in kp if b["h"] >= b["w"]]
        if not vt:
            continue
        hm = max(b["h"] for b in vt)
        _m3, mn = _main_group([dict(b) for b in kp])
        if not mn:
            continue
        bt = _median([b["y"] for b in mn])
        st = judge_headnote_strip(kp, body_top=bt, h_max=hm)
        skk = {(b["x"], b["y"], b["w"], b["h"]) for b in st}
        wmed = _median([b["w"] for b in mn])
        if wmed <= 0:
            continue
        # 生产口径的框（保留 + 参与排序），带 index 便于追踪
        kept = []
        for i in ki:
            b = bx[i]
            if (b["x"], b["y"], b["w"], b["h"]) in skk:
                continue
            kept.append(dict(b, index=i))
        thin = [b for b in kept if b["w"] / float(wmed) < 0.6]
        pairs = find_pairs(thin, wmed)
        if not pairs:
            continue
        units = cluster_order([dict(b) for b in kept])
        # 建立 box -> (unit_no, pos) 映射（用 index 作键）
        pos = {}
        for ui, items in enumerate(units):
            for pi, b in enumerate(items):
                pos[b["index"]] = (ui, pi, len(items))

        for a, b in pairs:
            tot_pairs += 1
            ka, kb = a["index"], b["index"]
            if ka not in pos or kb not in pos:
                problems.append({"page": q["page"], "why": "missing_in_order",
                                 "a": a["x"], "b": b["x"]})
                continue
            ua, pa, na = pos[ka]
            ub, pb, nb = pos[kb]
            same = (ua == ub)
            if same:
                q1_same_col += 1
            right_first = same and pa < pb
            if right_first:
                q2_right_first += 1
            contig = same and abs(pa - pb) == 1
            if contig:
                q3_contiguous += 1
            above = same and pa > 0
            below = same and max(pa, pb) < na - 1
            if above:
                q4_has_above += 1
            if below:
                q4_has_below += 1
            rec = {"page": q["page"],
                   "a": {"x": a["x"], "y": a["y"], "w": a["w"], "h": a["h"],
                         "text": q["lines"][ka][:30]},
                   "b": {"x": b["x"], "y": b["y"], "w": b["w"], "h": b["h"],
                         "text": q["lines"][kb][:30]},
                   "same_col": same, "right_first": right_first,
                   "contiguous": contig, "has_above": above, "has_below": below,
                   "unit_size": na}
            detail.append(rec)
            if not (same and right_first and contig):
                problems.append(rec)

    print("== 割注对在阅读顺序里的实测（%d 对）==" % tot_pairs)
    print("  Q1 两半在同一列单元:      %d / %d (%.1f%%)"
          % (q1_same_col, tot_pairs, 100.0 * q1_same_col / max(1, tot_pairs)))
    print("  Q2 右半先于左半:          %d / %d (%.1f%%)"
          % (q2_right_first, tot_pairs, 100.0 * q2_right_first / max(1, tot_pairs)))
    print("  Q3 两半连续（不夹别的框）: %d / %d (%.1f%%)"
          % (q3_contiguous, tot_pairs, 100.0 * q3_contiguous / max(1, tot_pairs)))
    print("  Q4 前面有正文:            %d / %d" % (q4_has_above, tot_pairs))
    print("  Q4 后面有正文:            %d / %d" % (q4_has_below, tot_pairs))

    print("\n== 不合「同列+右先+连续」的对：%d ==" % len(problems))
    for p in problems[:40]:
        if "why" in p:
            print("  %s %s a.x=%s b.x=%s" % (p["page"], p["why"], p["a"], p["b"]))
        else:
            print("  %s same=%d rightfirst=%d contig=%d unitsize=%d"
                  % (p["page"], p["same_col"], p["right_first"],
                     p["contiguous"], p["unit_size"]))
            print("     A(x=%d y=%d w=%d) %r"
                  % (p["a"]["x"], p["a"]["y"], p["a"]["w"], p["a"]["text"]))
            print("     B(x=%d y=%d w=%d) %r"
                  % (p["b"]["x"], p["b"]["y"], p["b"]["w"], p["b"]["text"]))

    print("\n== 列单元规模（割注并入后的列有多长）==")
    sizes = sorted(d["unit_size"] for d in detail)
    if sizes:
        print("  min=%d p25=%d 中位=%d p75=%d max=%d"
              % (sizes[0], sizes[len(sizes) // 4], sizes[len(sizes) // 2],
                 sizes[3 * len(sizes) // 4], sizes[-1]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"tot_pairs": tot_pairs, "same_col": q1_same_col,
                   "right_first": q2_right_first,
                   "contiguous": q3_contiguous,
                   "has_above": q4_has_above, "has_below": q4_has_below,
                   "n_problems": len(problems),
                   "problems": problems, "detail": detail},
                  f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_warichu_order.json")


if __name__ == "__main__":
    main()
