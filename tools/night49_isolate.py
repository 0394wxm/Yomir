# -*- coding: utf-8 -*-
"""night49_isolate.py — 只隔离 reorder_warichu_slots 这一个变量。

前两版测量各有一个方法论问题：
  * night49_final：改前/改后都走「离线版面过滤 + 重聚类」，自洽，
    但改前不等于归档（复刻 43/47 恒等，p021 差 2 个框）。
  * night49_exact_delta：「改前」用归档下标（filter_off 全集），
    「改后」用过滤后的框集 → 两套框集混比，12 页单元边界对不上，作废。

本脚本用**同一个框集**（归档 line_boxes 全集，不做版面过滤）跑两遍排序：
  改前 = sorted(y) + reorder_main_slots          （= Night48 生产行为）
  改后 = sorted(y) + reorder_warichu_slots + reorder_main_slots

并先校验「改前」是否逐页等于归档顺序——恒等则说明复刻无损，
两组数字之差就是 reorder_warichu_slots 的净效果。

用法: python -X utf8 tools/night49_isolate.py
产出: eval/night49_isolate.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.argv = [sys.argv[0]]
import importlib.util  # noqa: E402

from backend.ocr_layout import (  # noqa: E402
    main_column_keys, reorder_main_slots, reorder_warichu_slots,
)

spec = importlib.util.spec_from_file_location(
    "sim", os.path.join(ROOT, "tools", "night49_simulate.py"))
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)

OFF = os.path.join(ROOT, "eval", "night44_full", "filter_off")
OUT = os.path.join(ROOT, "eval", "night49_isolate.json")


def ov(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


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
            pairs.append((r, l))
            break
    return pairs


def order_pair(boxes):
    """同一个框集 → (旧顺序, 新顺序)。"""
    units = sim.cluster_units([dict(b) for b in boxes])
    mk = main_column_keys([dict(b) for b in boxes])
    old_units = []
    new_units = []
    for u in units:
        if u["kind"] == "col":
            its = sorted(u["items"], key=lambda t: t["y"])
            old_units.append(reorder_main_slots(its, mk))
            new_units.append(reorder_main_slots(
                reorder_warichu_slots(its), mk))
        else:
            its = sorted(u["items"], key=lambda t: -(t["x"]))
            old_units.append(its)
            new_units.append(its)
    # 单元先后顺序两版相同（只改单元内部），这里用生产口径排一次
    order_u = sorted(range(len(units)),
                     key=lambda k: -(units[k]["box"]["x"]
                                     + units[k]["box"]["w"] / 2.0))
    old = [it["index"] for k in order_u for it in old_units[k]]
    new = [it["index"] for k in order_u for it in new_units[k]]
    return old, new


def main():
    per = []
    tot = okb = oka = 0
    exc = []
    nonident = []
    moved = 0
    for fn in sorted(os.listdir(OFF)):
        if not fn.endswith(".json"):
            continue
        q = json.load(open(os.path.join(OFF, fn), encoding="utf-8"))
        bx = [dict(b) for b in q["line_boxes"]]
        if len(bx) < 4:
            continue
        for i, b in enumerate(bx):
            b["index"] = i
        old, new = order_pair(bx)
        if old != list(range(len(bx))):
            nonident.append({"page": q["page"],
                             "n": len(bx),
                             "n_diff": sum(1 for a, b in zip(old,
                                                             range(len(bx)))
                                           if a != b)})
        # 割注对（沿用 Night48 几何判据；wmed 取主栏中位宽）
        from backend.ocr_layout import _main_group, _median
        _m, mn = _main_group([dict(b) for b in bx])
        if not mn:
            continue
        wmed = _median([b["w"] for b in mn])
        if wmed <= 0:
            continue
        thin = [b for b in bx if b["w"] / float(wmed) < 0.6
                and b["h"] >= b["w"]]
        prs = find_pairs(thin, wmed)
        if not prs:
            continue
        pb = {i: p for p, i in enumerate(old)}
        pa = {i: p for p, i in enumerate(new)}
        n = nb = na = 0
        for r, l in prs:
            n += 1
            if pb[r["index"]] < pb[l["index"]]:
                nb += 1
            if pa[r["index"]] < pa[l["index"]]:
                na += 1
            else:
                exc.append({"page": q["page"],
                            "r": {"x": r["x"], "y": r["y"],
                                  "text": q["lines"][r["index"]][:26]},
                            "l": {"x": l["x"], "y": l["y"],
                                  "text": q["lines"][l["index"]][:26]}})
        tot += n
        okb += nb
        oka += na
        nm = sum(1 for a, b in zip(old, new) if a != b)
        moved += nm
        per.append({"page": q["page"], "n": n, "before": nb, "after": na,
                    "moved": nm})

    print("== 只隔离 reorder_warichu_slots（同一框集，无版面过滤）==")
    print("  复刻自检：改前 ≠ 归档顺序的页 %d %s"
          % (len(nonident),
             [(r["page"], r["n_diff"]) for r in nonident]))
    print("\n%-6s %5s %9s %9s %7s" % ("page", "对数", "改前", "改后", "位移"))
    for p in per:
        flag = "  <改前有例外" if p["before"] < p["n"] else ""
        print("%-6s %5d %7d/%d %7d/%d %7d%s"
              % (p["page"], p["n"], p["before"], p["n"], p["after"], p["n"],
                 p["moved"], flag))
    print("\n== 汇总 ==")
    print("  分母 %d 对" % tot)
    print("  改前右先 %d (%.2f%%)，有例外的页 %d"
          % (okb, 100.0 * okb / max(1, tot),
             sum(1 for p in per if p["before"] < p["n"])))
    print("  改后右先 %d (%.2f%%)，有例外的页 %d"
          % (oka, 100.0 * oka / max(1, tot),
             sum(1 for p in per if p["after"] < p["n"])))
    print("  退化（改后 < 改前）的页: %d" % sum(1 for p in per
                                              if p["after"] < p["before"]))
    print("  位置变化的行: %d" % moved)
    print("\n== 改后仍颠倒（应全是伪配对：dy_top 大 / 不等高）==")
    for e in exc:
        print("  %s R(x=%d y=%d) %r | L(x=%d y=%d) %r"
              % (e["page"], e["r"]["x"], e["r"]["y"], e["r"]["text"],
                 e["l"]["x"], e["l"]["y"], e["l"]["text"]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"per_page": per, "total": tot, "before": okb,
                   "after": oka, "exceptions_after": exc,
                   "nonidentical_before": nonident, "moved_lines": moved},
                  f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_isolate.json")


if __name__ == "__main__":
    main()
