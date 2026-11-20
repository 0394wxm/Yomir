# -*- coding: utf-8 -*-
"""night49_unit_dump.py — 打印含割注颠倒的列单元完整内容（设计修法用）。

用法: python -X utf8 tools/night49_unit_dump.py
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


def load(page):
    return json.load(open(os.path.join(OFF, page + ".json"), encoding="utf-8"))


def show(page, want_xs):
    q = load(page)
    bx = [dict(b) for b in q["line_boxes"]]
    _mi, jd = judge_layout(bx)
    ki = [i for i, (_b, r) in enumerate(jd) if r is None]
    kp = [bx[i] for i in ki]
    vt = [b for b in kp if b["h"] >= b["w"]]
    hm = max(b["h"] for b in vt)
    _m3, mn = _main_group([dict(b) for b in kp])
    bt = _median([b["y"] for b in mn])
    st = judge_headnote_strip(kp, body_top=bt, h_max=hm)
    skk = {(b["x"], b["y"], b["w"], b["h"]) for b in st}
    wmed = _median([b["w"] for b in mn])
    kept = []
    for i in ki:
        b = bx[i]
        if (b["x"], b["y"], b["w"], b["h"]) in skk:
            continue
        kept.append(dict(b, index=i))
    units = cluster_units([dict(b) for b in kept])
    print("\n### %s  wmed=%.1f  单元数=%d" % (page, wmed, len(units)))
    for ui, u in enumerate(units):
        xs = {it["x"] for it in u["items"]}
        if not (xs & set(want_xs)):
            continue
        print("  单元 #%d kind=%s bbox(x=%d y=%d w=%d h=%d) n=%d"
              % (ui, u["kind"], u["box"]["x"], u["box"]["y"],
                 u["box"]["w"], u["box"]["h"], len(u["items"])))
        for it in sorted(u["items"], key=lambda t: t["y"]):
            print("    y=%4d x=%4d w=%3d h=%3d  %r"
                  % (it["y"], it["x"], it["w"], it["h"],
                     q["lines"][it["index"]][:46]))


if __name__ == "__main__":
    show("p007", [518, 502])
    show("p013", [988, 968, 906, 886])
    show("p009", [356, 326, 344, 306])
    show("p020", [845, 800])
