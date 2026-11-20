# -*- coding: utf-8 -*-
"""night49_simulate.py — 离线模拟「列单元内 y 槽右→左」修法（不改生产代码）。

修法定义（拟）：
  在 `_cluster_order` 的列单元内，`sorted(key=y)` 之后，
  把**连续、|Δy_top| <= TOL、两两 x 不相交**的一组框视为同一个 y 槽
  （= 割注的并排半行），槽内按 **x 降序（右→左）** 重排。
  槽内若有任何一对 x 相交（正常上下堆叠），整个槽保持 y 序不动。

护栏：
  G1 只有两两 x 不相交才重排（保护主栏与正常堆叠）
  G2 只重排槽内成员的位置，槽的集合与成员不变（置换不变式）
  G3 与 `reorder_main_slots` 串联后仍满足 G2

本脚本对比：改前 vs 改后
  - 割注对右先率（A_strict 层）
  - 全本 47 页的置换差异（多少个框的位置变了）
  - 哪些页有变化、变化量多少

用法: python -X utf8 tools/night49_simulate.py [TOL]
产出: eval/night49_simulate.json
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
OUT = os.path.join(ROOT, "eval", "night49_simulate.json")
TOL = int(sys.argv[1]) if len(sys.argv) > 1 else 8


def ov(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def overlap_x(a, b):
    inter = ov(a["x"], a["x"] + a["w"], b["x"], b["x"] + b["w"])
    return inter / max(1, min(a["w"], b["w"]))


def xdisjoint(a, b):
    return a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"]


def sort_col_items(items, tol):
    """拟入生产的排序：y 升序，然后在 y 槽内 x 降序。"""
    items = sorted(items, key=lambda t: t["y"])
    out = []
    i = 0
    n = len(items)
    while i < n:
        j = i + 1
        anchor_y = items[i]["y"]
        while j < n and abs(items[j]["y"] - anchor_y) <= tol:
            j += 1
        run = items[i:j]
        if len(run) > 1 and all(xdisjoint(run[a], run[b])
                                for a in range(len(run))
                                for b in range(a + 1, len(run))):
            run = sorted(run, key=lambda t: -(t["x"] + t["w"]))
        out.extend(run)
        i = j
    return out


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


def order_for(kept, use_new, tol):
    units = cluster_units([dict(b) for b in kept])
    mk = main_column_keys([dict(b) for b in kept])
    for u in units:
        if u["kind"] == "col":
            if use_new:
                u["items"] = sort_col_items(u["items"], tol)
            else:
                u["items"] = sorted(u["items"], key=lambda t: t["y"])
            u["items"] = reorder_main_slots(u["items"], mk)
        else:
            u["items"] = sorted(u["items"], key=lambda t: -(t["x"]))
    units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
    out = []
    for u in units:
        out.extend(it["index"] for it in u["items"])
    return out


def page_kept(q):
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
    return kept, bx, q


def measure_right_first(order, kept, pairs):
    """order: index 列表（输出顺序）；返回右先计数。"""
    pos = {idx: p for p, idx in enumerate(order)}
    ok = 0
    for r, l in pairs:
        if pos[r["index"]] < pos[l["index"]]:
            ok += 1
    return ok


def main():
    # A_strict 层的对（从 night49_pair_quality.json 取）
    pq = json.load(open(os.path.join(ROOT, "eval", "night49_pair_quality.json"),
                        encoding="utf-8"))
    strict_keys = {}
    for x in pq["A_strict"]["rows"]:
        strict_keys.setdefault(x["page"], []).append(
            ((x["r"]["x"], x["r"]["y"]), (x["l"]["x"], x["l"]["y"])))

    tot_pairs = 0
    ok_before = ok_after = 0
    changed_pages = []
    total_perm_changes = 0
    rows = []

    for fn in sorted(os.listdir(OFF)):
        if not fn.endswith(".json"):
            continue
        q = json.load(open(os.path.join(OFF, fn), encoding="utf-8"))
        r = page_kept(q)
        if not r:
            continue
        kept, bx, q = r
        before = order_for(kept, False, TOL)
        after = order_for(kept, True, TOL)

        # G2 置换不变式
        if sorted(before) != sorted(after):
            raise SystemExit("FATAL 置换不变式被破坏: %s" % q["page"])

        nch = sum(1 for a, b in zip(before, after) if a != b)
        if nch:
            changed_pages.append({"page": q["page"], "changed": nch,
                                  "n": len(before)})
            total_perm_changes += nch

        # 右先率（A_strict 层）
        keys = strict_keys.get(q["page"], [])
        if keys:
            byxy = {(it["x"], it["y"]): it for it in kept}
            pairs = []
            for rk, lk in keys:
                ri, li = byxy.get(rk), byxy.get(lk)
                if ri and li:
                    pairs.append((ri, li))
            if pairs:
                b_ok = measure_right_first(before, kept, pairs)
                a_ok = measure_right_first(after, kept, pairs)
                tot_pairs += len(pairs)
                ok_before += b_ok
                ok_after += a_ok
                if a_ok < b_ok:
                    rows.append({"page": q["page"], "n": len(pairs),
                                 "before": b_ok, "after": a_ok})
        # 记录该页 A 层的改前改后
        if keys:
            pass

    print("== 离线模拟（TOL=%d，A_strict 层）==" % TOL)
    print("  对数 %d" % tot_pairs)
    print("  改前右先 %d (%.1f%%)" % (ok_before, 100.0 * ok_before / max(1, tot_pairs)))
    print("  改后右先 %d (%.1f%%)" % (ok_after, 100.0 * ok_after / max(1, tot_pairs)))
    print("  退化的页: %d" % len(rows))
    for r in rows:
        print("    %s %d/%d → %d/%d" % (r["page"], r["before"], r["n"],
                                        r["after"], r["n"]))

    print("\n== 全本置换差异 ==")
    print("  有变化的页: %d / 47" % len(changed_pages))
    print("  位置变化的框: %d" % total_perm_changes)
    for c in changed_pages:
        print("    %s %d/%d 框位置变" % (c["page"], c["changed"], c["n"]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"tol": TOL, "pairs": tot_pairs,
                   "right_first_before": ok_before,
                   "right_first_after": ok_after,
                   "regressions": rows, "changed_pages": changed_pages,
                   "total_perm_changes": total_perm_changes},
                  f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_simulate.json")


if __name__ == "__main__":
    main()
