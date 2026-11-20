# -*- coding: utf-8 -*-
"""night49_residual.py — 修法后仍颠倒的残余对是什么（TOL=8）。

用法: python -X utf8 tools/night49_residual.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.argv = [sys.argv[0]]
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "sim", os.path.join(ROOT, "tools", "night49_simulate.py"))
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)

TOL = 8


def main():
    pq = json.load(open(os.path.join(ROOT, "eval", "night49_pair_quality.json"),
                        encoding="utf-8"))
    strict = {}
    for x in pq["A_strict"]["rows"]:
        strict.setdefault(x["page"], []).append(x)

    print("== TOL=%d 后仍颠倒的 A 层对 ==" % TOL)
    n_bad = 0
    for fn in sorted(os.listdir(sim.OFF)):
        if not fn.endswith(".json"):
            continue
        q = json.load(open(os.path.join(sim.OFF, fn), encoding="utf-8"))
        r = sim.page_kept(q)
        if not r:
            continue
        kept, bx, q = r
        rows = strict.get(q["page"], [])
        if not rows:
            continue
        after = sim.order_for(kept, True, TOL)
        pos = {idx: p for p, idx in enumerate(after)}
        byxy = {(it["x"], it["y"]): it for it in kept}
        for x in rows:
            ri = byxy.get((x["r"]["x"], x["r"]["y"]))
            li = byxy.get((x["l"]["x"], x["l"]["y"]))
            if not ri or not li:
                continue
            pr, pl = pos[ri["index"]], pos[li["index"]]
            if pr > pl:
                n_bad += 1
                print("  %s R(pos=%d x=%d y=%d) %r"
                      % (q["page"], pr, x["r"]["x"], x["r"]["y"],
                         x["r"]["text"]))
                print("     L(pos=%d x=%d y=%d) %r  dist=%d gap=%.2f"
                      % (pl, x["l"]["x"], x["l"]["y"], x["l"]["text"],
                         pl - pr, x["gap_rel"]))
                # 打印两框所在单元
                units = sim.cluster_units([dict(b) for b in kept])
                for ui, u in enumerate(units):
                    ids = {it["index"] for it in u["items"]}
                    if ri["index"] in ids or li["index"] in ids:
                        print("     单元#%d bbox(x=%d y=%d w=%d h=%d) n=%d 质心=%.1f"
                              % (ui, u["box"]["x"], u["box"]["y"],
                                 u["box"]["w"], u["box"]["h"],
                                 len(u["items"]),
                                 u["box"]["x"] + u["box"]["w"] / 2.0))
                        for it in sorted(u["items"], key=lambda t: t["y"]):
                            mark = " <<<" if it["index"] in (ri["index"],
                                                             li["index"]) else ""
                            print("        y=%4d x=%4d w=%3d h=%3d %r%s"
                                  % (it["y"], it["x"], it["w"], it["h"],
                                     q["lines"][it["index"]][:38], mark))
    print("\n  残余颠倒: %d" % n_bad)


if __name__ == "__main__":
    main()
