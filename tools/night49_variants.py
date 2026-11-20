# -*- coding: utf-8 -*-
"""night49_variants.py — y 槽右→左重排的护栏阈值选型。

对每个「x 重叠上限」OV_MAX 和容差 TOL，测：
  - A_strict 层右先率（越高越好）
  - 退化页数（必须 0）
  - 「垂直堆叠对」相对顺序被改变的个数（必须 0）
    垂直堆叠对 = 同单元内 x 重叠 > 0.5 且 |Δy| > TOL 的框对
  - 位置变化的框数

用法: python -X utf8 tools/night49_variants.py
产出: eval/night49_variants.json
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

OUT = os.path.join(ROOT, "eval", "night49_variants.json")


def ovr(a, b):
    inter = max(0.0, min(a["x"] + a["w"], b["x"] + b["w"])
                - max(a["x"], b["x"]))
    return inter / max(1, min(a["w"], b["w"]))


def sort_col_items2(items, tol, ov_max):
    items = sorted(items, key=lambda t: t["y"])
    out = []
    i, n = 0, len(items)
    while i < n:
        j = i + 1
        anchor = items[i]["y"]
        while j < n and abs(items[j]["y"] - anchor) <= tol:
            j += 1
        run = items[i:j]
        if len(run) > 1:
            mx = max(ovr(run[a], run[b]) for a in range(len(run))
                     for b in range(a + 1, len(run)))
            if mx <= ov_max:
                run = sorted(run, key=lambda t: -(t["x"] + t["w"]))
        out.extend(run)
        i = j
    return out


def order_for2(kept, use_new, tol, ov_max):
    units = sim.cluster_units([dict(b) for b in kept])
    from backend.ocr_layout import main_column_keys, reorder_main_slots
    mk = main_column_keys([dict(b) for b in kept])
    for u in units:
        if u["kind"] == "col":
            if use_new:
                u["items"] = sort_col_items2(u["items"], tol, ov_max)
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


def main():
    pq = json.load(open(os.path.join(ROOT, "eval", "night49_pair_quality.json"),
                        encoding="utf-8"))
    strict = {}
    for x in pq["A_strict"]["rows"]:
        strict.setdefault(x["page"], []).append(
            ((x["r"]["x"], x["r"]["y"]), (x["l"]["x"], x["l"]["y"])))

    pages = []
    for fn in sorted(os.listdir(sim.OFF)):
        if fn.endswith(".json"):
            q = json.load(open(os.path.join(sim.OFF, fn), encoding="utf-8"))
            r = sim.page_kept(q)
            if r:
                pages.append((r[0], q["page"]))

    print("%-6s %-6s %9s %6s %8s %9s %8s"
          % ("OV_MAX", "TOL", "右先率", "退化", "堆叠变序", "位置变", "变页"))
    rows = []
    for ov_max in (0.0, 0.1, 0.3, 0.5, 0.7, 1.0):
        for tol in (4, 8, 12):
            tot = ok = 0
            regress = 0
            stacked_changed = 0
            perm = 0
            changed = 0
            for kept, page in pages:
                before = order_for2(kept, False, tol, ov_max)
                after = order_for2(kept, True, tol, ov_max)
                if sorted(before) != sorted(after):
                    raise SystemExit("invariant broken %s" % page)
                nch = sum(1 for a, b in zip(before, after) if a != b)
                if nch:
                    changed += 1
                    perm += nch
                pb = {i: p for p, i in enumerate(before)}
                pa = {i: p for p, i in enumerate(after)}
                # 垂直堆叠对：同单元 + x 重叠 > 0.5 + |Δy| > tol
                byidx = {it["index"]: it for it in kept}
                for u in sim.cluster_units([dict(b) for b in kept]):
                    its = u["items"]
                    for a in range(len(its)):
                        for b in range(a + 1, len(its)):
                            A, B = its[a], its[b]
                            if ovr(A, B) > 0.5 and \
                                    abs(A["y"] - B["y"]) > tol:
                                if (pb[A["index"]] < pb[B["index"]]) != \
                                        (pa[A["index"]] < pa[B["index"]]):
                                    stacked_changed += 1
                keys = strict.get(page, [])
                if keys:
                    byxy = {(it["x"], it["y"]): it for it in kept}
                    pairs = [(byxy[a], byxy[b]) for a, b in keys
                             if a in byxy and b in byxy]
                    if pairs:
                        b_ok = sim.measure_right_first(before, kept, pairs)
                        a_ok = sim.measure_right_first(after, kept, pairs)
                        tot += len(pairs)
                        ok += a_ok
                        if a_ok < b_ok:
                            regress += 1
            rate = 100.0 * ok / max(1, tot)
            print("%-6.1f %-6d %8.1f%% %6d %8d %9d %8d"
                  % (ov_max, tol, rate, regress, stacked_changed, perm,
                     changed))
            rows.append({"ov_max": ov_max, "tol": tol, "pairs": tot,
                         "right_first": ok, "rate": rate,
                         "regress": regress,
                         "stacked_changed": stacked_changed,
                         "perm": perm, "changed_pages": changed})
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_variants.json")


if __name__ == "__main__":
    main()
