# -*- coding: utf-8 -*-
"""night49_diagnose.py — 割注对顺序颠倒的机制诊断（不修代码）。

night49_order_final 实测：488 对里 432 右先（88.5%），56 对颠倒。
本脚本回答三个问题：

  D1 这些「对」是真的割注吗？——看 gap/wmed 分布。
     Night48 的成对判据允许 gap <= 1.2*wmed（很松）。真割注两半紧挨着，
     gap 应该接近 0。若颠倒对的 gap 明显偏大，它们可能是**伪配对**，
     不是顺序缺陷。

  D2 颠倒对的机制：两半在不在同一个列单元？
     - 同单元 → 单元内按 y 排序，左半 y 更小就排前面
     - 不同单元 → 单元按 bbox 质心 x 排序，bbox 被别的框撑宽就会错位

  D3 用生产 `_cluster_order` 复刻取单元结构；对每对报告
     单元 id、单元 bbox、两半的 y 差、gap。

产出: eval/night49_diagnose.json
用法: python -X utf8 tools/night49_diagnose.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import (  # noqa: E402
    _main_group, _median, judge_headnote_strip, judge_layout,
    main_column_keys, reorder_main_slots,
)

OFF = os.path.join(ROOT, "eval", "night44_full", "filter_off")
OUT = os.path.join(ROOT, "eval", "night49_diagnose.json")


def ov(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def overlap_x(a, b):
    inter = ov(a["x"], a["x"] + a["w"], b["x"], b["x"] + b["w"])
    return inter / max(1, min(a["w"], b["w"]))


def cluster_units(boxes):
    """复刻 _cluster_order 的单元构造（縦書き列聚类），返回 units。"""
    vert = [b for b in boxes if b["h"] >= b["w"]]
    horz = [b for b in boxes if b["h"] < b["w"]]
    units = []
    for b in sorted(vert, key=lambda t: -(t["x"] + t["w"])):
        placed = False
        for u in units:
            if u["kind"] == "col" and overlap_x(u["box"], b) >= 0.4:
                u["items"].append(b)
                u["box"] = {
                    "x": min(u["box"]["x"], b["x"]),
                    "y": min(u["box"]["y"], b["y"]),
                    "w": max(u["box"]["x"] + u["box"]["w"], b["x"] + b["w"])
                    - min(u["box"]["x"], b["x"]),
                    "h": max(u["box"]["y"] + u["box"]["h"], b["y"] + b["h"])
                    - min(u["box"]["y"], b["y"]),
                }
                placed = True
                break
        if not placed:
            units.append({"kind": "col", "box": dict(b), "items": [b]})
    for b in sorted(horz, key=lambda t: t["y"]):
        placed = False
        for u in units:
            if u["kind"] == "row" and overlap_x(u["box"], b) >= 0.4:
                u["items"].append(b)
                placed = True
                break
        if not placed:
            units.append({"kind": "row", "box": dict(b), "items": [b]})
    return units


def find_pairs(thin, wmed):
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
            r, l = (a, b) if a["x"] > b["x"] else (b, a)
            used.add(id(r))
            used.add(id(l))
            pairs.append((r, l, gap))
            break
    return pairs


def main():
    rows = []
    for fn in sorted(os.listdir(OFF)):
        if not fn.endswith(".json"):
            continue
        q = json.load(open(os.path.join(OFF, fn), encoding="utf-8"))
        bx = [dict(b) for b in q["line_boxes"]]
        if len(bx) < 4:
            continue
        _mi, jd = judge_layout(bx)
        ki = [i for i, (_b, r) in enumerate(jd) if r is None]
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
        kept = []
        for i in ki:
            b = bx[i]
            if (b["x"], b["y"], b["w"], b["h"]) in skk:
                continue
            kept.append(dict(b, index=i))
        thin = [b for b in kept if b["w"] / float(wmed) < 0.6
                and b["h"] >= b["w"]]
        pairs = find_pairs(thin, wmed)
        if not pairs:
            continue

        units = cluster_units([dict(b) for b in kept])
        uof = {}
        for ui, u in enumerate(units):
            for it in u["items"]:
                uof[it["index"]] = ui

        for r, l, gap in pairs:
            ur, ul = uof.get(r["index"]), uof.get(l["index"])
            same = (ur == ul)
            # 最终顺序位置 = 归档下标
            pr, pl = r["index"], l["index"]
            right_first = pr < pl
            # 同单元时，生产按 y 排序；检查 y 关系
            ub = units[ur]["box"] if same else None
            rows.append({
                "page": q["page"],
                "gap_rel": round(gap / wmed, 3),
                "dy_left_minus_right": l["y"] - r["y"],
                "dh": abs(l["h"] - r["h"]),
                "wmed": wmed,
                "w_rel_r": round(r["w"] / wmed, 3),
                "w_rel_l": round(l["w"] / wmed, 3),
                "same_unit": same,
                "unit_size": len(units[ur]["items"]) if same else None,
                "unit_w_rel": round(ub["w"] / wmed, 2) if same else None,
                "unit_has_main": None,
                "right_first": right_first,
                "dist": pl - pr,
                "r": {"x": r["x"], "y": r["y"], "w": r["w"], "h": r["h"],
                      "text": q["lines"][pr][:30]},
                "l": {"x": l["x"], "y": l["y"], "w": l["w"], "h": l["h"],
                      "text": q["lines"][pl][:30]},
            })

    n = len(rows)
    bad = [x for x in rows if not x["right_first"]]
    print("== 割注对 %d，颠倒 %d (%.1f%%) ==" % (n, len(bad),
                                                 100.0 * len(bad) / max(1, n)))

    print("\n== D1 gap 分布（gap / 主栏宽）==")
    for label, sub in (("全部", rows), ("右先", [x for x in rows
                                                 if x["right_first"]]),
                       ("颠倒", bad)):
        gs = sorted(x["gap_rel"] for x in sub)
        if not gs:
            continue
        print("  %-4s n=%3d min=%.2f 中位=%.2f p90=%.2f max=%.2f  紧贴(<0.15)=%d"
              % (label, len(gs), gs[0], gs[len(gs) // 2],
                 gs[int(0.9 * (len(gs) - 1))], gs[-1],
                 sum(1 for g in gs if g < 0.15)))

    print("\n== D2 颠倒对的机制 ==")
    same = [x for x in bad if x["same_unit"]]
    diff = [x for x in bad if not x["same_unit"]]
    print("  颠倒 %d：同单元 %d，跨单元 %d" % (len(bad), len(same), len(diff)))
    print("\n  同单元颠倒的 y 关系（左半 y < 右半 y 就会排前面）：")
    for x in same[:20]:
        print("   %s dy(L-R)=%+4d gap=%.2f unitsize=%d unit_w_rel=%.2f"
              % (x["page"], x["dy_left_minus_right"], x["gap_rel"],
                 x["unit_size"], x["unit_w_rel"]))
        print("      R(y=%d h=%d w=%d) %r"
              % (x["r"]["y"], x["r"]["h"], x["r"]["w"], x["r"]["text"]))
        print("      L(y=%d h=%d w=%d) %r"
              % (x["l"]["y"], x["l"]["h"], x["l"]["w"], x["l"]["text"]))
    if diff:
        print("\n  跨单元颠倒：")
        for x in diff[:20]:
            print("   %s dist=%d R(x=%d) L(x=%d) %r | %r"
                  % (x["page"], x["dist"], x["r"]["x"], x["l"]["x"],
                     x["r"]["text"], x["l"]["text"]))

    print("\n== D3 右先对的 gap 对照（判断伪配对）==")
    good = [x for x in rows if x["right_first"]]
    for label, sub in (("右先", good), ("颠倒", bad)):
        tight = [x for x in sub if x["gap_rel"] < 0.15]
        loose = [x for x in sub if x["gap_rel"] >= 0.30]
        print("  %-4s n=%3d  紧贴<0.15: %3d  松>=0.30: %3d"
              % (label, len(sub), len(tight), len(loose)))

    print("\n== 按 gap 分层的右先率 ==")
    bands = [(0.0, 0.10), (0.10, 0.20), (0.20, 0.35), (0.35, 0.60),
             (0.60, 1.25)]
    for lo, hi in bands:
        sub = [x for x in rows if lo <= x["gap_rel"] < hi]
        if not sub:
            continue
        ok = sum(1 for x in sub if x["right_first"])
        print("  gap %.2f-%.2f: n=%3d 右先 %3d (%.0f%%)"
              % (lo, hi, len(sub), ok, 100.0 * ok / len(sub)))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n": n, "n_bad": len(bad),
                   "n_same_unit_bad": len(same),
                   "n_diff_unit_bad": len(diff), "rows": rows},
                  f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_diagnose.json")


if __name__ == "__main__":
    main()
