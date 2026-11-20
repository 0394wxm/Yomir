# -*- coding: utf-8 -*-
"""night49_text_delta.py — 改前/改后**输出文本序列**的差异，人工可读。

按框坐标把两版顺序映射回文本，逐页列出变化区间，
并统计「整页文本拼接」的差异（用 difflib 定位）。

用法: python -X utf8 tools/night49_text_delta.py
产出: eval/night49_text_delta.json
"""
import difflib
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.argv = [sys.argv[0]]
import importlib.util  # noqa: E402

from backend.ocr_layout import main_column_keys, reorder_main_slots, \
    reorder_warichu_slots  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "sim", os.path.join(ROOT, "tools", "night49_simulate.py"))
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)

OUT = os.path.join(ROOT, "eval", "night49_text_delta.json")


def order_of(kept, use_new):
    units = sim.cluster_units([dict(b) for b in kept])
    mk = main_column_keys([dict(b) for b in kept])
    for u in units:
        if u["kind"] == "col":
            u["items"] = sorted(u["items"], key=lambda t: t["y"])
            if use_new:
                u["items"] = reorder_warichu_slots(u["items"])
            u["items"] = reorder_main_slots(u["items"], mk)
        else:
            u["items"] = sorted(u["items"], key=lambda t: -(t["x"]))
    units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
    out = []
    for u in units:
        out.extend(it["index"] for it in u["items"])
    return out


def main():
    rows = []
    n_page_changed = 0
    n_char_moved = 0
    for fn in sorted(os.listdir(sim.OFF)):
        if not fn.endswith(".json"):
            continue
        q = json.load(open(os.path.join(sim.OFF, fn), encoding="utf-8"))
        r = sim.page_kept(q)
        if not r:
            continue
        kept, _bx, q = r
        byidx = {it["index"]: it for it in kept}
        ob = order_of(kept, False)
        oa = order_of(kept, True)
        if ob == oa:
            continue
        n_page_changed += 1
        tb = [q["lines"][i] for i in ob]
        ta = [q["lines"][i] for i in oa]
        n_char_moved += sum(len(t) for t in tb)
        same_multiset = sorted(tb) == sorted(ta)
        # 人工可读：列出发生位移的框及其前后位置
        pb = {i: p for p, i in enumerate(ob)}
        pa = {i: p for p, i in enumerate(oa)}
        moved = [i for i in ob if pb[i] != pa[i]]
        detail = []
        for i in moved:
            detail.append({"text": q["lines"][i][:34],
                           "pos_before": pb[i], "pos_after": pa[i],
                           "x": byidx[i]["x"]})
        rows.append({"page": q["page"], "n_lines": len(ob),
                     "n_moved": len(moved),
                     "multiset_same": same_multiset,
                     "moved": detail})
        print("\n### %s  行 %d 中位移 %d 条  字符集%s"
              % (q["page"], len(ob), len(moved),
                 "相同" if same_multiset else "**不同**"))
        for d in detail:
            print("   pos %3d → %3d  x=%4d  %r"
                  % (d["pos_before"], d["pos_after"], d["x"], d["text"]))

    print("\n== 汇总 ==")
    print("  输出文本序列变化的页: %d / 47" % n_page_changed)
    print("  位移行总数（含字符数）: %d" % n_char_moved)
    print("  所有页的行多重集相同（无增删，只换序）: %s"
          % all(r["multiset_same"] for r in rows))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"pages": rows, "changed_pages": n_page_changed}, f,
                  ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_text_delta.json")


if __name__ == "__main__":
    main()
