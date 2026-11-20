# -*- coding: utf-8 -*-
"""night49_tol_probe.py — 选 y 容差的安全边界 + 看两个跨单元颠倒。

问题：修法要在列单元内把「y 相近且 x 不相交」的框按右→左排。
容差 TOL 取多大才不会把「真正上下相接的框」误判为同一槽？

测量：全本 47 页、所有列单元内，**x 不相交的相邻框对**的 |Δy| 分布。
若分布有明显空档，TOL 取空档内的值最安全。

同时打印 p033/p041 两个跨单元颠倒的单元结构。

用法: python -X utf8 tools/night49_tol_probe.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import (  # noqa: E402
    _main_group, _median, judge_headnote_strip, judge_layout,
)

OFF = os.path.join(ROOT, "eval", "night44_full", "filter_off")


def ov(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def overlap_x(a, b):
    inter = ov(a["x"], a["x"] + a["w"], b["x"], b["x"] + b["w"])
    return inter / max(1, min(a["w"], b["w"]))


def disjoint(a, b):
    return a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"]


def cluster_units(boxes):
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


def page_units(q):
    bx = [dict(b) for b in q["line_boxes"]]
    _mi, jd = judge_layout(bx)
    ki = [i for i, (_b, r) in enumerate(jd) if r is None]
    kp = [bx[i] for i in ki]
    vt = [b for b in kp if b["h"] >= b["w"]]
    if not vt:
        return None
    hm = max(b["h"] for b in vt)
    _m3, mn = _main_group([dict(b) for b in kp])
    if not mn:
        return None
    bt = _median([b["y"] for b in mn])
    st = judge_headnote_strip(kp, body_top=bt, h_max=hm)
    skk = {(b["x"], b["y"], b["w"], b["h"]) for b in st}
    kept = []
    for i in ki:
        b = bx[i]
        if (b["x"], b["y"], b["w"], b["h"]) in skk:
            continue
        kept.append(dict(b, index=i))
    return cluster_units([dict(b) for b in kept]), kept, q


def main():
    d = json.load(open(os.path.join(ROOT, "eval", "night49_diagnose.json"),
                       encoding="utf-8"))
    bad_pairs = {(x["page"], x["r"]["x"], x["r"]["y"], x["l"]["x"], x["l"]["y"])
                 for x in d["rows"] if not x["right_first"]}

    gaps = []
    print("== 单元内 x 不相交的相邻框对 |Δy| ==")
    for fn in sorted(os.listdir(OFF)):
        if not fn.endswith(".json"):
            continue
        q = json.load(open(os.path.join(OFF, fn), encoding="utf-8"))
        r = page_units(q)
        if not r:
            continue
        units, kept, q = r
        for u in units:
            its = sorted(u["items"], key=lambda t: t["y"])
            for i in range(len(its) - 1):
                a, b = its[i], its[i + 1]
                if disjoint(a, b):
                    gaps.append((abs(b["y"] - a["y"]), q["page"],
                                 a["x"], b["x"]))
    vs = sorted(g[0] for g in gaps)
    import collections
    hist = collections.Counter()
    for v in vs:
        if v <= 12:
            hist[v] += 1
        elif v <= 20:
            hist[13] += 1
        elif v <= 40:
            hist[14] += 1
        elif v <= 100:
            hist[15] += 1
        else:
            hist[16] += 1
    labels = {13: "13-20", 14: "21-40", 15: "41-100", 16: ">100"}
    print("  n=%d  min=%d 中位=%d p90=%d max=%d"
          % (len(vs), vs[0], vs[len(vs) // 2], vs[int(0.9 * (len(vs) - 1))],
             vs[-1]))
    for k in sorted(hist):
        print("    %-8s %5d %s" % (labels.get(k, str(k)), hist[k],
                                   "#" * min(60, hist[k] // 4)))

    print("\n== 跨单元颠倒的两个案例 ==")
    for page, rx, ry, lx, ly in sorted(bad_pairs):
        if page not in ("p033", "p041"):
            continue
        q = json.load(open(os.path.join(OFF, page + ".json"),
                           encoding="utf-8"))
        units, kept, q = page_units(q)
        # 找含这两个 x 的单元
        hit = [ui for ui, u in enumerate(units)
               if any(it["x"] in (rx, lx) for it in u["items"])]
        print("\n  --- %s  target R(x=%d) L(x=%d)  单元 %s" % (page, rx, lx, hit))
        for ui in hit:
            u = units[ui]
            print("   单元 #%d bbox(x=%d y=%d w=%d h=%d) n=%d 质心x=%.1f"
                  % (ui, u["box"]["x"], u["box"]["y"], u["box"]["w"],
                     u["box"]["h"], len(u["items"]),
                     u["box"]["x"] + u["box"]["w"] / 2.0))
            for it in sorted(u["items"], key=lambda t: t["y"]):
                print("      y=%4d x=%4d w=%3d h=%3d %r"
                      % (it["y"], it["x"], it["w"], it["h"],
                         q["lines"][it["index"]][:40]))


if __name__ == "__main__":
    main()
